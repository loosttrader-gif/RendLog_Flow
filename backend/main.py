# main.py - V4.0 (Ventana movil de 60 velas con reset al iniciar)
import MetaTrader5 as mt5
import time
import pandas as pd
from datetime import datetime
from conexion_mt5 import conectar_mt5, obtener_datos_historicos
from calculos_rendlog import (
    calcular_rendimientos_log,
    calcular_bandas_sigma,
    detectar_anomalias,
    estimar_distribucion_t,
    calcular_efficiency_ratio,
    clasificar_regimen
)
import numpy as np
from calculos_orderflow import calcular_delta_volumen, calcular_volumen_relativo, detectar_anomalia_volumen
from api_client import SupabaseClient
from config import DEFAULT_CONFIG, TIMEFRAME_MAP, TIMEFRAMES_ACTIVOS, VENTANA_VELAS, SYMBOL
from utils import log_mensaje


def _safe_float(value, default=0.0):
    """Convierte a float seguro para JSON. NaN/Inf -> default."""
    if value is None or pd.isna(value) or np.isinf(value):
        return default
    return float(value)


def build_rows(df_slice, config, timeframe_name):
    """Construye lista de dicts para enviar a Supabase."""
    rows = []
    for _, row in df_slice.iterrows():
        z_score = 0.0
        media_valid = not pd.isna(row.get('media', None))
        std_valid = not pd.isna(row.get('std', None)) and row['std'] > 0
        std_static_valid = not pd.isna(row.get('std_static', None)) and row['std_static'] > 0

        if std_valid and media_valid:
            z_score = _safe_float((row['log_return'] - row['media']) / row['std'])

        # Z-score estático para comparación v2.0 vs v3.0
        z_score_static = 0.0
        if std_static_valid and media_valid:
            z_score_static = _safe_float((row['log_return'] - row['media']) / row['std_static'])

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
                "log_return": _safe_float(row['log_return']),
                "media": _safe_float(row.get('media')),
                "std": _safe_float(row.get('std')),
                "banda_2sigma_superior": _safe_float(row.get('banda_2sigma_superior')),
                "banda_2sigma_inferior": _safe_float(row.get('banda_2sigma_inferior')),
                "banda_3sigma_superior": _safe_float(row.get('banda_3sigma_superior')),
                "banda_3sigma_inferior": _safe_float(row.get('banda_3sigma_inferior')),
                "z_score_static": z_score_static,
                "sigma_ewma": _safe_float(row.get('std')),
                "sigma_static": _safe_float(row.get('std_static')),
                "vol_ratio": _safe_float(row.get('vol_ratio'), default=1.0),
                "er": _safe_float(row.get('efficiency_ratio')) if not pd.isna(row.get('efficiency_ratio', np.nan)) else None,
                "regimen": clasificar_regimen(row.get('efficiency_ratio', np.nan))
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


def calcular_estadisticas(df, config, timeframe=None):
    """Calcula todas las metricas RendLog y OrderFlow sobre el DataFrame."""
    ventana = min(config.get('ventana_estadistica', 20), VENTANA_VELAS // 3)
    df = calcular_rendimientos_log(df)
    df = calcular_bandas_sigma(df, ventana=ventana, timeframe=timeframe)
    df = calcular_delta_volumen(df)
    df = calcular_volumen_relativo(df, ventana=min(ventana, 20))
    df = detectar_anomalia_volumen(df, ventana=ventana)
    df = calcular_efficiency_ratio(df)    # Fase 3
    return df


def main():
    print("=" * 70)
    print(" " * 10 + "RENDLOG PLATFORM V4.0 - Ventana Movil 60 Velas")
    print("=" * 70)

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

    # ============================================================
    # PASO 1: LIMPIAR DATOS ANTERIORES (RESET TOTAL)
    # ============================================================
    print(f"\n{'=' * 70}")
    log_mensaje("Limpiando datos anteriores del usuario...", "WARNING")
    if supabase.delete_user_data():
        log_mensaje("Datos anteriores eliminados correctamente", "SUCCESS")
    else:
        log_mensaje("Error limpiando datos (puede ser primera ejecucion)", "WARNING")

    # Obtener configuracion
    config = supabase.obtener_configuracion()
    if not config:
        log_mensaje("Usando configuracion por defecto", "WARNING")
        config = DEFAULT_CONFIG
    else:
        log_mensaje(f"Config: Umbral={config['umbral_sigma_compra']}s / {config['umbral_sigma_venta']}s", "INFO")

    # ============================================================
    # PASO 2: CARGA INICIAL - 60 VELAS POR TIMEFRAME
    # ============================================================
    print(f"\n{'=' * 70}")
    log_mensaje(f"Carga inicial: {VENTANA_VELAS} velas por timeframe...", "INFO")

    last_sent_time = {}
    all_initial_rows = []
    nu_estimado = {}  # Fase 2: grados de libertad t por timeframe

    for tf_name in TIMEFRAMES_ACTIVOS:
        tf_minutes = TIMEFRAME_MAP.get(tf_name, 1)
        log_mensaje(f"[{tf_name}] Obteniendo {VENTANA_VELAS} velas...", "INFO")

        df = obtener_datos_historicos(SYMBOL, tf_minutes, VENTANA_VELAS)
        if df is None or df.empty:
            log_mensaje(f"[{tf_name}] No se pudieron obtener datos, saltando...", "WARNING")
            continue

        # Calcular estadisticas sobre las 60 velas
        df = calcular_estadisticas(df, config, timeframe=tf_name)

        # Fase 2: estimar distribución t
        dist_t = estimar_distribucion_t(df, min_datos=30)
        if dist_t:
            nu_estimado[tf_name] = dist_t['nu']
            log_mensaje(
                f"[{tf_name}] Distribucion t: nu={dist_t['nu']}, "
                f"curtosis={dist_t['curtosis_empirica']} ({dist_t['descripcion']})",
                "INFO"
            )

        # Detectar senal en ultima vela
        senal = detectar_anomalias(
            df,
            config['umbral_sigma_compra'],
            config['umbral_sigma_venta'],
            nu=nu_estimado.get(tf_name, None)
        )

        # Construir filas (todas las que tienen log_return valido)
        datos = df.dropna(subset=['log_return'])
        rows = build_rows(datos, config, tf_name)
        all_initial_rows.extend(rows)

        # Guardar timestamp de ultima vela
        last_sent_time[tf_name] = datos['time'].iloc[-1]
        log_mensaje(f"[{tf_name}] {len(rows)} filas preparadas", "SUCCESS")

        # Log comparativo v2.0 vs v3.0
        if senal.get('senal_suprimida'):
            log_mensaje(
                f"[{tf_name}] SENAL SUPRIMIDA (regimen {senal.get('regimen')}, "
                f"ER={senal.get('er', 0):.3f}) | "
                f"Senal pre-filtro: {senal.get('senal_pre_filtro')} | "
                f"z_ewma={senal['z_score']:.3f} vs z_static={senal.get('z_score_static', 0):.3f}",
                "WARNING"
            )
        elif senal.get('senal'):
            log_mensaje(
                f"[{tf_name}] SENAL: {senal['señal']} | "
                f"z_ewma={senal['z_score']:.3f} | z_static={senal.get('z_score_static', 0):.3f} | "
                f"pct_real={senal.get('percentil_real', 0):.1f}% | "
                f"regimen={senal.get('regimen', 'N/A')} ER={senal.get('er', 0):.3f} | "
                f"nu={senal.get('nu_distribucion', 'N/A')}",
                "SUCCESS"
            )

    # Enviar carga inicial completa
    if all_initial_rows:
        log_mensaje(f"Enviando {len(all_initial_rows)} filas iniciales a Supabase...", "INFO")
        if supabase.enviar_datos(all_initial_rows):
            log_mensaje(f"Carga inicial completada: {len(all_initial_rows)} filas", "SUCCESS")
        else:
            log_mensaje("Error en carga inicial", "ERROR")
    else:
        log_mensaje("No se obtuvieron datos iniciales de ningun timeframe", "ERROR")
        mt5.shutdown()
        return

    # ============================================================
    # PASO 3: LOOP PRINCIPAL - VENTANA MOVIL
    # ============================================================
    print(f"\n{'=' * 70}")
    log_mensaje("Iniciando loop de ventana movil (cada 30s)...", "INFO")
    log_mensaje("   Presiona Ctrl+C para detener", "INFO")
    print("=" * 70)

    ciclo = 0

    try:
        while True:
            time.sleep(30)
            ciclo += 1
            print(f"\n{'─' * 70}")
            print(f"[Ciclo #{ciclo}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'─' * 70}")

            # Actualizar config cada ciclo
            config = supabase.obtener_configuracion()
            if not config:
                config = DEFAULT_CONFIG

            nuevas_en_ciclo = 0

            for tf_name in TIMEFRAMES_ACTIVOS:
                tf_minutes = TIMEFRAME_MAP.get(tf_name, 1)

                # Obtener solo la ultima vela para verificar si hay nueva
                df_check = obtener_datos_historicos(SYMBOL, tf_minutes, 1)
                if df_check is None or df_check.empty:
                    continue

                latest_time = df_check['time'].iloc[0]

                # Verificar si hay vela nueva
                if tf_name in last_sent_time and latest_time <= last_sent_time[tf_name]:
                    log_mensaje(f"[{tf_name}] Sin vela nueva", "INFO")
                    continue

                # ---- HAY VELA NUEVA ----
                log_mensaje(f"[{tf_name}] Nueva vela detectada: {latest_time}", "SUCCESS")

                # 1. Eliminar vela mas antigua de este timeframe en Supabase
                if supabase.delete_oldest_candle(tf_name):
                    log_mensaje(f"[{tf_name}] Vela mas antigua eliminada", "INFO")
                else:
                    log_mensaje(f"[{tf_name}] Error eliminando vela antigua", "WARNING")

                # 2. Obtener 60 velas para recalcular estadisticas completas
                df = obtener_datos_historicos(SYMBOL, tf_minutes, VENTANA_VELAS)
                if df is None or df.empty:
                    continue

                # 3. Calcular estadisticas con las 60 velas
                df = calcular_estadisticas(df, config, timeframe=tf_name)

                # Fase 2: re-estimar nu con datos frescos
                dist_t = estimar_distribucion_t(df, min_datos=30)
                if dist_t:
                    nu_estimado[tf_name] = dist_t['nu']

                senal = detectar_anomalias(
                    df,
                    config['umbral_sigma_compra'],
                    config['umbral_sigma_venta'],
                    nu=nu_estimado.get(tf_name, None)
                )

                # 4. Construir SOLO la fila nueva (ultima vela)
                datos = df.dropna(subset=['log_return'])
                new_row = build_rows(datos.tail(1), config, tf_name)

                # 5. Insertar vela nueva en Supabase
                if new_row and supabase.enviar_datos(new_row):
                    log_mensaje(f"[{tf_name}] Vela nueva insertada (ventana = {VENTANA_VELAS})", "SUCCESS")
                    nuevas_en_ciclo += 1
                else:
                    log_mensaje(f"[{tf_name}] Error insertando vela nueva", "ERROR")

                # Actualizar timestamp
                last_sent_time[tf_name] = latest_time

                # Log comparativo v2.0 vs v3.0
                if senal.get('senal_suprimida'):
                    log_mensaje(
                        f"[{tf_name}] SENAL SUPRIMIDA (regimen {senal.get('regimen')}, "
                        f"ER={senal.get('er', 0):.3f}) | "
                        f"Senal pre-filtro: {senal.get('senal_pre_filtro')} | "
                        f"z_ewma={senal['z_score']:.3f} vs z_static={senal.get('z_score_static', 0):.3f}",
                        "WARNING"
                    )
                elif senal.get('senal'):
                    log_mensaje(
                        f"[{tf_name}] SENAL: {senal['señal']} | "
                        f"z_ewma={senal['z_score']:.3f} | z_static={senal.get('z_score_static', 0):.3f} | "
                        f"pct_real={senal.get('percentil_real', 0):.1f}% | "
                        f"regimen={senal.get('regimen', 'N/A')} ER={senal.get('er', 0):.3f} | "
                        f"nu={senal.get('nu_distribucion', 'N/A')}",
                        "SUCCESS"
                    )

            if nuevas_en_ciclo == 0:
                log_mensaje("Sin velas nuevas en ningun timeframe", "INFO")
            else:
                log_mensaje(f"{nuevas_en_ciclo} timeframe(s) actualizados", "SUCCESS")

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        log_mensaje("Deteniendo backend por peticion del usuario...", "WARNING")
        mt5.shutdown()
        log_mensaje("Desconectado de MT5", "SUCCESS")
        print("=" * 70)

if __name__ == "__main__":
    main()
