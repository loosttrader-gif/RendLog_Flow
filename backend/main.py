# main.py - V3.0 (Multi-timeframe: procesa todos los TFs en cada ciclo)
import MetaTrader5 as mt5
import time
import pandas as pd
from datetime import datetime
from conexion_mt5 import conectar_mt5, obtener_datos_historicos
from calculos_rendlog import calcular_rendimientos_log, calcular_bandas_sigma, detectar_anomalias
from calculos_orderflow import calcular_delta_volumen, calcular_volumen_relativo, detectar_anomalia_volumen
from api_client import SupabaseClient
from config import DEFAULT_CONFIG, TIMEFRAME_MAP, TIMEFRAMES_ACTIVOS
from utils import log_mensaje


def build_rows(df_slice, config, timeframe_name):
    """Construye lista de dicts para enviar a Supabase."""
    rows = []
    for _, row in df_slice.iterrows():
        z_score = 0.0
        if not pd.isna(row.get('std', None)) and row['std'] > 0:
            z_score = float((row['log_return'] - row['media']) / row['std'])

        senal = None
        if z_score < config.get('umbral_sigma_compra', -2.0):
            senal = "COMPRA"
        elif z_score > config.get('umbral_sigma_venta', 2.0):
            senal = "VENTA"

        rows.append({
            "timeframe": timeframe_name,
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
                "delta": int(row['delta']) if not pd.isna(row.get('delta', None)) else 0,
                "vol_relativo": float(row['volumen_relativo']) if not pd.isna(row.get('volumen_relativo', None)) else 1.0,
                "anomalia_vol": bool(row['anomalia_volumen']) if not pd.isna(row.get('anomalia_volumen', None)) else False,
                "z_score_vol": float(row['z_score_volumen']) if not pd.isna(row.get('z_score_volumen', None)) else 0,
                "tick_volume": int(row['tick_volume']) if not pd.isna(row.get('tick_volume', None)) else 0
            }
        })
    return rows


def main():
    print("="*70)
    print(" "*15 + "RENDLOG PLATFORM V3.0 - Multi-Timeframe")
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
        log_mensaje("API_KEY no configurada o invalida en archivo .env", "ERROR")
        log_mensaje("", "INFO")
        log_mensaje("INSTRUCCIONES:", "INFO")
        log_mensaje("1. Registrate en el frontend web para obtener tu API_KEY", "INFO")
        log_mensaje("2. Copia el API_KEY en el archivo .env", "INFO")
        log_mensaje("3. Reinicia este backend", "INFO")
        log_mensaje("", "INFO")
        mt5.shutdown()
        return

    log_mensaje(f"Usuario autenticado: {user_id}", "SUCCESS")
    log_mensaje(f"Timeframes activos: {', '.join(TIMEFRAMES_ACTIVOS)}", "INFO")
    log_mensaje("", "INFO")
    log_mensaje("Iniciando loop de actualizacion (cada 30s)...", "INFO")
    log_mensaje("   Presiona Ctrl+C para detener", "INFO")
    print("="*70)

    ciclo = 0
    is_first_cycle = True
    # Timestamp de la última vela enviada por timeframe
    last_sent_time = {}

    try:
        while True:
            ciclo += 1
            print(f"\n{'─'*70}")
            print(f"[Ciclo #{ciclo}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'─'*70}")

            # 1. Obtener configuración actualizada desde Supabase
            config = supabase.obtener_configuracion()
            if not config:
                log_mensaje("Usando configuracion por defecto", "WARNING")
                config = DEFAULT_CONFIG
            else:
                log_mensaje(f"Config: Umbral={config['umbral_sigma_compra']}s / {config['umbral_sigma_venta']}s", "INFO")

            # 2. Procesar cada timeframe
            all_rows = []
            for tf_name in TIMEFRAMES_ACTIVOS:
                timeframe_minutes = TIMEFRAME_MAP.get(tf_name, 1)

                # Obtener datos históricos
                velas_a_pedir = config['ventana_estadistica'] * 2
                log_mensaje(f"[{tf_name}] Obteniendo {velas_a_pedir} velas...", "INFO")
                df = obtener_datos_historicos("EURUSD", timeframe_minutes, velas_a_pedir)

                if df is None or df.empty:
                    log_mensaje(f"[{tf_name}] No se pudieron obtener datos, saltando...", "WARNING")
                    continue

                # Calcular métricas RendLog
                df = calcular_rendimientos_log(df)
                df = calcular_bandas_sigma(df, ventana=config['ventana_estadistica'])
                señal_rendlog = detectar_anomalias(
                    df,
                    config['umbral_sigma_compra'],
                    config['umbral_sigma_venta']
                )

                # Calcular métricas Order Flow
                df = calcular_delta_volumen(df)
                df = calcular_volumen_relativo(df)
                df = detectar_anomalia_volumen(df)

                # Preparar filas
                datos_con_stats = df.dropna(subset=['log_return']).tail(100)

                if is_first_cycle or tf_name not in last_sent_time:
                    nuevas = datos_con_stats
                else:
                    nuevas = datos_con_stats[datos_con_stats['time'] > last_sent_time[tf_name]]

                if nuevas.empty:
                    log_mensaje(f"[{tf_name}] Sin velas nuevas", "INFO")
                    continue

                rows = build_rows(nuevas, config, tf_name)
                all_rows.extend(rows)

                # Actualizar last_sent_time para este TF
                last_sent_time[tf_name] = datos_con_stats['time'].iloc[-1]

                log_mensaje(f"[{tf_name}] {len(rows)} filas preparadas", "SUCCESS")

                # Mostrar señal si existe
                if señal_rendlog.get('señal'):
                    print(f"\n{'='*70}")
                    print(f"  [{tf_name}] SENAL DETECTADA: {señal_rendlog['señal']}")
                    print(f"{'='*70}")
                    print(f"   Z-score: {señal_rendlog['z_score']:.3f}s")
                    print(f"   Mensaje: {señal_rendlog['mensaje']}")
                    print(f"   Timestamp: {señal_rendlog['timestamp']}")
                    print(f"{'='*70}\n")

            # 3. Enviar batch completo a Supabase
            if all_rows:
                modo = f"UPSERT {len(all_rows)} filas ({len(TIMEFRAMES_ACTIVOS)} TFs)"
                if is_first_cycle:
                    modo = f"UPSERT inicial {len(all_rows)} filas ({len(TIMEFRAMES_ACTIVOS)} TFs)"
                log_mensaje(f"Enviando [{modo}]...", "INFO")

                if supabase.enviar_datos(all_rows):
                    log_mensaje("Datos sincronizados correctamente", "SUCCESS")
                    is_first_cycle = False
                else:
                    log_mensaje("Error sincronizando datos", "ERROR")
            else:
                log_mensaje("Sin datos nuevos en ningun timeframe", "INFO")

            # 4. Esperar 30s
            log_mensaje("Esperando 30s para proximo ciclo...\n", "INFO")
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        log_mensaje("Deteniendo backend por peticion del usuario...", "WARNING")
        mt5.shutdown()
        log_mensaje("Desconectado de MT5", "SUCCESS")
        print("="*70)

if __name__ == "__main__":
    main()
