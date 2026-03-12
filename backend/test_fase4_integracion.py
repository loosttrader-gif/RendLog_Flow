"""
Test Fase 4 -- Integracion completa del pipeline v3.0
Ejecutar: python test_fase4_integracion.py
No requiere MT5 ni Supabase.
"""
import numpy as np
import pandas as pd
from calculos_rendlog import (
    calcular_rendimientos_log,
    calcular_bandas_sigma,
    detectar_anomalias,
    estimar_distribucion_t,
    calcular_efficiency_ratio,
    clasificar_regimen
)


def make_df_completo(prices, timeframe="30M"):
    df = pd.DataFrame({
        'time':  pd.date_range('2026-01-01', periods=len(prices), freq='30min'),
        'close': prices,
        'open':  prices,
    })
    df = calcular_rendimientos_log(df)
    df = calcular_bandas_sigma(df, ventana=20, timeframe=timeframe)
    df = calcular_efficiency_ratio(df)
    return df


def test_pipeline_completo_todos_los_campos():
    """Verificar que detectar_anomalias retorna todos los campos esperados."""
    print("\n--- TEST 1: Todos los campos presentes en output ---")
    np.random.seed(42)

    prices = 1.08 + np.cumsum(np.random.normal(0, 0.0005, 65))
    df = make_df_completo(prices)

    dist_t  = estimar_distribucion_t(df, min_datos=30)
    nu      = dist_t['nu'] if dist_t else None
    resultado = detectar_anomalias(df, nu=nu)

    campos_requeridos = [
        # Originales v2.0
        'señal', 'z_score', 'color', 'mensaje', 'timestamp', 'rendimiento',
        # Fase 1
        'z_score_static', 'sigma_ewma', 'sigma_static', 'vol_ratio', 'regimen_volatil',
        # Fase 2
        'percentil_real', 'nu_distribucion', 'calibracion_activa',
        # Fase 3
        'er', 'regimen', 'senal_pre_filtro', 'senal_suprimida',
    ]

    faltantes = [c for c in campos_requeridos if c not in resultado]
    assert not faltantes, f"Campos faltantes: {faltantes}"

    for campo in campos_requeridos:
        print(f"  {campo}: {resultado[campo]}")

    print("  [OK] Todos los campos presentes en output")


def test_pipeline_no_rompe_sin_datos_suficientes():
    """Pipeline debe funcionar sin errores con datos minimos."""
    print("\n--- TEST 2: Estabilidad con pocos datos ---")
    np.random.seed(7)

    prices = 1.08 + np.cumsum(np.random.normal(0, 0.0005, 25))
    df = make_df_completo(prices)

    dist_t = estimar_distribucion_t(df, min_datos=50)  # retorna None
    assert dist_t is None, "Debe retornar None con pocos datos"

    resultado = detectar_anomalias(df, nu=None)
    assert 'z_score' in resultado, "detectar_anomalias debe funcionar sin nu"
    print(f"  Resultado con nu=None: z_score={resultado['z_score']:.4f}")
    print("  [OK] Pipeline estable sin distribucion t ajustada")


def test_columnas_en_dataframe():
    """DataFrame debe tener todas las columnas nuevas."""
    print("\n--- TEST 3: Columnas en DataFrame ---")
    np.random.seed(42)

    prices = 1.08 + np.cumsum(np.random.normal(0, 0.0005, 65))
    df = make_df_completo(prices)

    columnas_esperadas = [
        'log_return', 'media',
        'std',           # EWMA (Fase 1)
        'std_static',    # Rolling original (Fase 1)
        'vol_ratio',     # Ratio EWMA/static (Fase 1)
        'banda_2sigma_superior', 'banda_2sigma_inferior',
        'banda_3sigma_superior', 'banda_3sigma_inferior',
        'efficiency_ratio',  # Fase 3
    ]

    faltantes = [c for c in columnas_esperadas if c not in df.columns]
    assert not faltantes, f"Columnas faltantes en DataFrame: {faltantes}"
    print(f"  Columnas presentes: {len(columnas_esperadas)}/{len(columnas_esperadas)}")
    print("  [OK] Todas las columnas del pipeline v3.0 presentes")


if __name__ == "__main__":
    print("=" * 55)
    print("VALIDACION FASE 4 -- INTEGRACION COMPLETA v3.0")
    print("=" * 55)

    test_pipeline_completo_todos_los_campos()
    test_pipeline_no_rompe_sin_datos_suficientes()
    test_columnas_en_dataframe()

    print("\n" + "=" * 55)
    print("[OK] TODOS LOS TESTS PASARON -- RendLog Flow v3.0 listo")
    print("=" * 55)
    print()
    print("Resumen de mejoras implementadas:")
    print("  Fase 1: sigma dinamico EWMA por timeframe")
    print("          -> menos falsas senales post-noticias")
    print("  Fase 2: distribucion t de Student")
    print("          -> percentiles reales, no gaussianos inflados")
    print("  Fase 3: filtro de regimen (Efficiency Ratio)")
    print("          -> senales suprimidas cuando mercado esta en tendencia")
    print()
    print("Archivos modificados:")
    print("  calculos_rendlog.py  -- motor estadistico completo v3.0")
    print("  main.py              -- integracion de timeframe y logging")
    print("  config.py            -- parametros estadisticos v3.0")
    print("  requirements.txt     -- scipy y arch agregados")
    print()
    print("Archivos NO modificados:")
    print("  calculos_orderflow.py")
    print("  api_client.py")
    print("  conexion_mt5.py")
    print("  utils.py")
