# main.py - V2.0 (Integración con Supabase)
import MetaTrader5 as mt5
import time
import pandas as pd
from datetime import datetime
from conexion_mt5 import conectar_mt5, obtener_datos_historicos
from calculos_rendlog import calcular_rendimientos_log, calcular_bandas_sigma, detectar_anomalias
from calculos_orderflow import calcular_delta_volumen, calcular_volumen_relativo, detectar_anomalia_volumen
from api_client import SupabaseClient
from config import DEFAULT_CONFIG, TIMEFRAME_MAP
from utils import log_mensaje

def main():
    print("="*70)
    print(" "*15 + "RENDLOG PLATFORM V2.0 - Backend Local")
    print("="*70)

    # Conectar MT5
    log_mensaje("Intentando conectar a MT5...", "INFO")
    if not conectar_mt5():
        log_mensaje("No se pudo conectar a MT5. Abortando...", "ERROR")
        return

    # Inicializar cliente Supabase
    log_mensaje("Inicializando cliente Supabase...", "INFO")
    supabase = SupabaseClient()

    # Verificar credenciales
    user_id = supabase.obtener_user_id()
    if not user_id:
        log_mensaje("", "ERROR")
        log_mensaje("API_KEY no configurada o inválida en archivo .env", "ERROR")
        log_mensaje("", "INFO")
        log_mensaje("INSTRUCCIONES:", "INFO")
        log_mensaje("1. Regístrate en el frontend web para obtener tu API_KEY", "INFO")
        log_mensaje("2. Copia el API_KEY en el archivo .env", "INFO")
        log_mensaje("3. Reinicia este backend", "INFO")
        log_mensaje("", "INFO")
        mt5.shutdown()
        return

    log_mensaje(f"Usuario autenticado: {user_id}", "SUCCESS")
    log_mensaje("", "INFO")
    log_mensaje("🔄 Iniciando loop de actualización (cada 30s)...", "INFO")
    log_mensaje("   Presiona Ctrl+C para detener", "INFO")
    print("="*70)

    ciclo = 0

    try:
        while True:
            ciclo += 1
            print(f"\n{'─'*70}")
            print(f"[Ciclo #{ciclo}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'─'*70}")

            # 1. Obtener configuración actualizada desde Supabase
            config = supabase.obtener_configuracion()
            if not config:
                log_mensaje("Usando configuración por defecto", "WARNING")
                config = DEFAULT_CONFIG
            else:
                log_mensaje(f"Config: TF={config['timeframe']}, Umbral={config['umbral_sigma_compra']}σ / {config['umbral_sigma_venta']}σ", "INFO")

            # 2. Determinar timeframe en minutos
            timeframe_minutes = TIMEFRAME_MAP.get(config['timeframe'], 30)

            # 3. Obtener datos históricos
            log_mensaje(f"Obteniendo {config['ventana_estadistica']} velas de {config['timeframe']}...", "INFO")
            df = obtener_datos_historicos("EURUSD", timeframe_minutes, config['ventana_estadistica'])

            if df is None or df.empty:
                log_mensaje("No se pudieron obtener datos. Reintentando en 30s...", "WARNING")
                time.sleep(30)
                continue

            log_mensaje(f"Datos obtenidos: {len(df)} velas", "SUCCESS")

            # 4. Calcular métricas RendLog
            log_mensaje("Calculando RendLog...", "INFO")
            df = calcular_rendimientos_log(df)
            df = calcular_bandas_sigma(df, ventana=config['ventana_estadistica'])
            señal_rendlog = detectar_anomalias(
                df,
                config['umbral_sigma_compra'],
                config['umbral_sigma_venta']
            )

            # 5. Calcular métricas Order Flow
            log_mensaje("Calculando Order Flow...", "INFO")
            df = calcular_delta_volumen(df)
            df = calcular_volumen_relativo(df)
            df = detectar_anomalia_volumen(df)

            # 6. Preparar las 100 filas para enviar
            datos_ultimas = df.dropna(subset=['log_return']).tail(100)
            rows = []

            for _, row in datos_ultimas.iterrows():
                # Z-score individual por fila
                z_score = 0.0
                if not pd.isna(row.get('std', None)) and row['std'] > 0:
                    z_score = float((row['log_return'] - row['media']) / row['std'])

                # Señal individual
                senal = None
                if z_score < config.get('umbral_sigma_compra', -2.0):
                    senal = "COMPRA"
                elif z_score > config.get('umbral_sigma_venta', 2.0):
                    senal = "VENTA"

                rows.append({
                    "data_timestamp": row['time'].isoformat(),
                    "rendlog": {
                        "z_score": z_score,
                        "senal": senal,
                        "log_return": float(row['log_return']) if not pd.isna(row['log_return']) else 0,
                        "media": float(row['media']) if not pd.isna(row['media']) else 0,
                        "std": float(row['std']) if not pd.isna(row['std']) else 0,
                        "banda_2sigma_superior": float(row['banda_2sigma_superior']) if not pd.isna(row['banda_2sigma_superior']) else 0,
                        "banda_2sigma_inferior": float(row['banda_2sigma_inferior']) if not pd.isna(row['banda_2sigma_inferior']) else 0,
                        "banda_3sigma_superior": float(row['banda_3sigma_superior']) if not pd.isna(row['banda_3sigma_superior']) else 0,
                        "banda_3sigma_inferior": float(row['banda_3sigma_inferior']) if not pd.isna(row['banda_3sigma_inferior']) else 0
                    },
                    "orderflow": {
                        "delta": float(row['delta']) if not pd.isna(row.get('delta', None)) else 0,
                        "vol_relativo": float(row['volumen_relativo']) if not pd.isna(row.get('volumen_relativo', None)) else 1.0,
                        "anomalia_vol": bool(row['anomalia_volumen']) if not pd.isna(row.get('anomalia_volumen', None)) else False,
                        "z_score_vol": float(row['z_score_volumen']) if not pd.isna(row.get('z_score_volumen', None)) else 0,
                        "tick_volume": int(row['tick_volume']) if not pd.isna(row.get('tick_volume', None)) else 0
                    }
                })

            # 7. Enviar a Supabase
            log_mensaje(f"Enviando {len(rows)} filas a Supabase...", "INFO")
            if supabase.enviar_datos(rows):
                log_mensaje("Datos sincronizados correctamente", "SUCCESS")
            else:
                log_mensaje("Error sincronizando datos", "ERROR")

            # 8. Mostrar señal si existe
            if señal_rendlog.get('señal'):
                print(f"\n{'='*70}")
                print(f"🚨 SEÑAL DETECTADA: {señal_rendlog['señal']}")
                print(f"{'='*70}")
                print(f"   Z-score: {señal_rendlog['z_score']:.3f}σ")
                print(f"   Mensaje: {señal_rendlog['mensaje']}")
                print(f"   Timestamp: {señal_rendlog['timestamp']}")
                print(f"{'='*70}\n")

            # 9. Esperar 30s
            log_mensaje("Esperando 30s para próximo ciclo...\n", "INFO")
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        log_mensaje("Deteniendo backend por petición del usuario...", "WARNING")
        mt5.shutdown()
        log_mensaje("Desconectado de MT5", "SUCCESS")
        print("="*70)

if __name__ == "__main__":
    main()
