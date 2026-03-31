# main.py - V4.1 (Multi-par: 4 símbolos × 6 TFs | GBM Monte Carlo | PCA Sistémico)
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
from calculos_gbm import calcular_gbm_anomalia
from calculos_multipair import (
    construir_matriz_retornos,
    calcular_covarianza,
    calcular_pca,
    detectar_exposicion_usd,
    calcular_correlacion_con_eurusd,
    es_movimiento_sistemico,
)
from api_client import SupabaseClient
from config import (
    DEFAULT_CONFIG, TIMEFRAME_MAP, TIMEFRAMES_ACTIVOS,
    VENTANA_VELAS, SYMBOLS_ACTIVOS, PCA_MIN_FILAS_ALINEADAS
)
from utils import log_mensaje


def _safe_float(value, default=0.0):
    """Convierte a float seguro para JSON. NaN/Inf -> default."""
    if value is None or pd.isna(value) or np.isinf(value):
        return default
    return float(value)


def build_rows(df_slice, config, timeframe_name, symbol, pca_result=None, exposure=None):
    """
    Construye lista de dicts para enviar a Supabase.

    Novedades v4.1:
      - Agrega campo 'symbol' al nivel de fila
      - Agrega campos GBM (gbm_prob_reversion, etc.) en rendlog
      - Agrega campos PCA (pca_pc1_loading, pca_es_sistemico, etc.) en rendlog
    """
    if exposure is None:
        exposure = {}

    pca_es_sistemico = es_movimiento_sistemico(pca_result, symbol)
    pc1_loading = None
    pc1_varianza = None
    if pca_result and pca_result.get("pca_valido"):
        pc1_loading  = pca_result["pc1_loadings"].get(symbol)
        pc1_varianza = pca_result.get("pc1_varianza")

    rows = []
    for _, row in df_slice.iterrows():
        z_score = 0.0
        media_valid     = not pd.isna(row.get('media', None))
        std_valid       = not pd.isna(row.get('std', None)) and row['std'] > 0
        std_static_valid = not pd.isna(row.get('std_static', None)) and row['std_static'] > 0

        if std_valid and media_valid:
            z_score = _safe_float((row['log_return'] - row['media']) / row['std'])

        z_score_static = 0.0
        if std_static_valid and media_valid:
            z_score_static = _safe_float((row['log_return'] - row['media']) / row['std_static'])

        # Señal base (umbral de z-score)
        senal = None
        if z_score < config.get('umbral_sigma_compra', -2.0):
            senal = "COMPRA"
        elif z_score > config.get('umbral_sigma_venta', 2.0):
            senal = "VENTA"

        # Supresión por PCA (movimiento sistémico USD)
        senal_suprimida_pca = False
        if senal is not None and pca_es_sistemico:
            senal = None
            senal_suprimida_pca = True

        # GBM: solo en velas con anomalía
        media_val = _safe_float(row.get('media'))
        std_val   = _safe_float(row.get('std'))
        close_val = _safe_float(row.get('close'))
        gbm_fields = calcular_gbm_anomalia(
            z_score=z_score,
            mu=media_val,
            sigma_ewma=std_val,
            precio_close=close_val,
            timeframe=timeframe_name,
        )

        er_val = row.get('efficiency_ratio', np.nan)

        rows.append({
            "symbol": symbol,
            "timeframe": timeframe_name,
            "data_timestamp": row['time'].isoformat(),
            "rendlog": {
                # Retorno y señal
                "z_score":  z_score,
                "senal":    senal,
                "log_return": _safe_float(row['log_return']),
                "media":    _safe_float(row.get('media')),
                "std":      _safe_float(row.get('std')),
                # Bandas
                "banda_2sigma_superior": _safe_float(row.get('banda_2sigma_superior')),
                "banda_2sigma_inferior": _safe_float(row.get('banda_2sigma_inferior')),
                "banda_3sigma_superior": _safe_float(row.get('banda_3sigma_superior')),
                "banda_3sigma_inferior": _safe_float(row.get('banda_3sigma_inferior')),
                # Diagnóstico EWMA vs estático
                "z_score_static": z_score_static,
                "sigma_ewma":     _safe_float(row.get('std')),
                "sigma_static":   _safe_float(row.get('std_static')),
                "vol_ratio":      _safe_float(row.get('vol_ratio'), default=1.0),
                # Régimen
                "er":      _safe_float(er_val) if not pd.isna(er_val) else None,
                "regimen": clasificar_regimen(er_val),
                # Supresión de señal
                "senal_suprimida":     senal_suprimida_pca or (
                    senal is None and (
                        (z_score < config.get('umbral_sigma_compra', -2.0)) or
                        (z_score > config.get('umbral_sigma_venta', 2.0))
                    )
                ),
                "senal_suprimida_pca": senal_suprimida_pca,
                # GBM Monte Carlo (None en velas sin anomalía)
                **gbm_fields,
                # PCA multi-par
                "pca_pc1_loading":  round(pc1_loading, 4) if pc1_loading is not None else None,
                "pca_pc1_varianza": round(pc1_varianza, 4) if pc1_varianza is not None else None,
                "pca_es_sistemico": pca_es_sistemico,
                "exposure_usd_alto": bool(exposure.get(symbol, False)),
            },
            "orderflow": {
                "delta":       int(row['delta']) if not pd.isna(row.get('delta', None)) else 0,
                "vol_relativo": float(row['volumen_relativo']) if not pd.isna(row.get('volumen_relativo', None)) else 1.0,
                "anomalia_vol": bool(row['anomalia_volumen']) if not pd.isna(row.get('anomalia_volumen', None)) else False,
                "z_score_vol":  float(row['z_score_volumen']) if not pd.isna(row.get('z_score_volumen', None)) else 0,
                "tick_volume":  int(row['tick_volume']) if not pd.isna(row.get('tick_volume', None)) else 0,
            }
        })
    return rows


def calcular_estadisticas(df, config, timeframe=None, symbol=None):
    """Calcula todas las métricas RendLog y OrderFlow sobre el DataFrame."""
    ventana = min(config.get('ventana_estadistica', 20), VENTANA_VELAS // 3)
    df = calcular_rendimientos_log(df)
    df = calcular_bandas_sigma(df, ventana=ventana, timeframe=timeframe, symbol=symbol)
    df = calcular_delta_volumen(df)
    df = calcular_volumen_relativo(df, ventana=min(ventana, 20))
    df = detectar_anomalia_volumen(df, ventana=ventana)
    df = calcular_efficiency_ratio(df)
    return df


def _calcular_pca_para_tf(dfs_por_simbolo):
    """
    Calcula PCA cross-símbolo para un timeframe dado.

    Args:
        dfs_por_simbolo: dict[symbol -> DataFrame con 'time' y 'log_return']

    Returns:
        tuple(pca_result, exposure, correlaciones)
        Todos None si no hay suficientes datos alineados.
    """
    R, syms, _ = construir_matriz_retornos(dfs_por_simbolo)
    if R is None:
        log_mensaje(
            f"PCA: datos insuficientes (<{PCA_MIN_FILAS_ALINEADAS} filas alineadas), "
            "continuando sin análisis sistémico",
            "WARNING"
        )
        return None, {}, {}

    cov        = calcular_covarianza(R)
    pca_result = calcular_pca(cov, syms)
    exposure   = detectar_exposicion_usd(cov, syms)
    corrs      = calcular_correlacion_con_eurusd(cov, syms)

    log_mensaje(
        f"PCA: PC1={pca_result['pc1_varianza']*100:.1f}% varianza | "
        f"Sistémico={'SÍ' if pca_result['pc1_varianza'] > 0.60 else 'NO'} | "
        f"Loadings: {', '.join(f'{s}={v:.2f}' for s,v in pca_result['pc1_loadings'].items())}",
        "INFO"
    )
    return pca_result, exposure, corrs


def main():
    print("=" * 70)
    print(" " * 10 + "RENDLOG PLATFORM V4.1 - Multi-Par + GBM + PCA")
    print("=" * 70)
    print(f"  Símbolos: {', '.join(SYMBOLS_ACTIVOS)}")
    print(f"  Timeframes: {', '.join(TIMEFRAMES_ACTIVOS)}")
    print(f"  Series totales: {len(SYMBOLS_ACTIVOS) * len(TIMEFRAMES_ACTIVOS)}")
    print("=" * 70)

    log_mensaje("Intentando conectar a MT5...", "INFO")
    if not conectar_mt5():
        log_mensaje("No se pudo conectar a MT5. Abortando...", "ERROR")
        return

    log_mensaje("Inicializando cliente Supabase...", "INFO")
    supabase = SupabaseClient()

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

    # ============================================================
    # PASO 1: RESET TOTAL
    # ============================================================
    print(f"\n{'=' * 70}")
    log_mensaje("Limpiando datos anteriores del usuario...", "WARNING")
    if supabase.delete_user_data():
        log_mensaje("Datos anteriores eliminados correctamente", "SUCCESS")
    else:
        log_mensaje("Error limpiando datos (puede ser primera ejecucion)", "WARNING")

    config = supabase.obtener_configuracion()
    if not config:
        log_mensaje("Usando configuracion por defecto", "WARNING")
        config = DEFAULT_CONFIG
    else:
        log_mensaje(
            f"Config: Umbral={config['umbral_sigma_compra']}s / {config['umbral_sigma_venta']}s",
            "INFO"
        )

    # ============================================================
    # PASO 2: CARGA INICIAL — outer=TF, inner=SYMBOL
    # ============================================================
    print(f"\n{'=' * 70}")
    log_mensaje(f"Carga inicial: {VENTANA_VELAS} velas × {len(SYMBOLS_ACTIVOS)} pares × {len(TIMEFRAMES_ACTIVOS)} TFs...", "INFO")

    # last_sent_time[(symbol, tf_name)] = último timestamp enviado
    last_sent_time = {}
    all_initial_rows = []
    nu_estimado = {}   # Fase 2: {(symbol, tf_name): nu}

    for tf_name in TIMEFRAMES_ACTIVOS:
        tf_minutes = TIMEFRAME_MAP.get(tf_name, 1)
        log_mensaje(f"[TF={tf_name}] Cargando {len(SYMBOLS_ACTIVOS)} pares...", "INFO")

        dfs_por_simbolo = {}

        for symbol in SYMBOLS_ACTIVOS:
            df = obtener_datos_historicos(symbol, tf_minutes, VENTANA_VELAS)
            if df is None or df.empty:
                log_mensaje(f"  [{symbol}] No se pudieron obtener datos, saltando", "WARNING")
                continue

            df = calcular_estadisticas(df, config, timeframe=tf_name, symbol=symbol)

            dist_t = estimar_distribucion_t(df, min_datos=30)
            if dist_t:
                nu_estimado[(symbol, tf_name)] = dist_t['nu']
                log_mensaje(
                    f"  [{symbol}/{tf_name}] dist-t: nu={dist_t['nu']}, "
                    f"{dist_t['descripcion']}",
                    "INFO"
                )

            dfs_por_simbolo[symbol] = df

        # PCA cross-símbolo para este timeframe
        pca_result, exposure, _ = _calcular_pca_para_tf(dfs_por_simbolo)

        # Construir filas por símbolo
        for symbol, df in dfs_por_simbolo.items():
            datos = df.dropna(subset=['log_return'])
            rows = build_rows(datos, config, tf_name, symbol, pca_result, exposure)
            all_initial_rows.extend(rows)
            last_sent_time[(symbol, tf_name)] = datos['time'].iloc[-1]
            log_mensaje(f"  [{symbol}/{tf_name}] {len(rows)} filas preparadas", "SUCCESS")

    # Enviar carga inicial
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
    # PASO 3: LOOP PRINCIPAL — ventana móvil multi-par
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

            config = supabase.obtener_configuracion()
            if not config:
                config = DEFAULT_CONFIG

            nuevas_en_ciclo = 0

            for tf_name in TIMEFRAMES_ACTIVOS:
                tf_minutes = TIMEFRAME_MAP.get(tf_name, 1)

                # Verificar qué símbolos tienen vela nueva en este TF
                simbolos_nuevos = []
                for symbol in SYMBOLS_ACTIVOS:
                    df_check = obtener_datos_historicos(symbol, tf_minutes, 1)
                    if df_check is None or df_check.empty:
                        continue
                    latest_time = df_check['time'].iloc[0]
                    clave = (symbol, tf_name)
                    if clave not in last_sent_time or latest_time > last_sent_time[clave]:
                        simbolos_nuevos.append((symbol, latest_time))

                if not simbolos_nuevos:
                    log_mensaje(f"[{tf_name}] Sin velas nuevas", "INFO")
                    continue

                # Hay al menos un símbolo con vela nueva — recalcular todo el TF
                log_mensaje(
                    f"[{tf_name}] Velas nuevas: {', '.join(s for s,_ in simbolos_nuevos)}",
                    "SUCCESS"
                )

                dfs_por_simbolo = {}

                for symbol, latest_time in simbolos_nuevos:
                    # Eliminar vela más antigua de este símbolo+TF
                    if not supabase.delete_oldest_candle(tf_name, symbol):
                        log_mensaje(f"  [{symbol}/{tf_name}] Error eliminando vela antigua", "WARNING")

                    # Obtener ventana completa de 60 velas
                    df = obtener_datos_historicos(symbol, tf_minutes, VENTANA_VELAS)
                    if df is None or df.empty:
                        continue

                    df = calcular_estadisticas(df, config, timeframe=tf_name, symbol=symbol)

                    dist_t = estimar_distribucion_t(df, min_datos=30)
                    if dist_t:
                        nu_estimado[(symbol, tf_name)] = dist_t['nu']

                    dfs_por_simbolo[symbol] = df

                if not dfs_por_simbolo:
                    continue

                # PCA cross-símbolo con los DataFrames del ciclo actual
                # (solo si tenemos los 4 símbolos; si alguno faltó, usamos lo disponible)
                pca_result, exposure, _ = _calcular_pca_para_tf(dfs_por_simbolo)

                # Insertar solo la vela nueva de cada símbolo
                for symbol, latest_time in simbolos_nuevos:
                    if symbol not in dfs_por_simbolo:
                        continue

                    df = dfs_por_simbolo[symbol]
                    datos = df.dropna(subset=['log_return'])
                    new_row = build_rows(datos.tail(1), config, tf_name, symbol, pca_result, exposure)

                    senal_info = detectar_anomalias(
                        df,
                        config['umbral_sigma_compra'],
                        config['umbral_sigma_venta'],
                        nu=nu_estimado.get((symbol, tf_name)),
                        pca_es_sistemico=es_movimiento_sistemico(pca_result, symbol),
                    )

                    if new_row and supabase.enviar_datos(new_row):
                        log_mensaje(
                            f"  [{symbol}/{tf_name}] Insertada | "
                            f"z={senal_info['z_score']:.3f} | "
                            f"señal={senal_info.get('señal') or 'ninguna'} | "
                            f"régimen={senal_info.get('regimen')}",
                            "SUCCESS"
                        )
                        nuevas_en_ciclo += 1
                    else:
                        log_mensaje(f"  [{symbol}/{tf_name}] Error insertando vela", "ERROR")

                    last_sent_time[(symbol, tf_name)] = latest_time

            if nuevas_en_ciclo == 0:
                log_mensaje("Sin velas nuevas en ningun par/timeframe", "INFO")
            else:
                log_mensaje(f"{nuevas_en_ciclo} velas actualizadas en este ciclo", "SUCCESS")

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        log_mensaje("Deteniendo backend por peticion del usuario...", "WARNING")
        mt5.shutdown()
        log_mensaje("Desconectado de MT5", "SUCCESS")
        print("=" * 70)

if __name__ == "__main__":
    main()
