"""
Test Fase 1 — EWMA Sigma Dinámico
Ejecutar: python test_fase1_ewma.py
No requiere MT5 ni Supabase.
"""
import numpy as np
import pandas as pd
from calculos_rendlog import calcular_rendimientos_log, calcular_bandas_sigma, detectar_anomalias


def make_df(prices, timeframe="30M"):
    """Helper: crea DataFrame de prueba con precios y timestamps."""
    df = pd.DataFrame({
        'time':  pd.date_range('2026-01-01', periods=len(prices), freq='30min'),
        'close': prices,
        'open':  prices,
    })
    df = calcular_rendimientos_log(df)
    df = calcular_bandas_sigma(df, ventana=20, timeframe=timeframe)
    return df


def test_ewma_reacciona_a_shock():
    """EWMA debe elevar sigma tras un shock y mantenerlo elevado."""
    print("\n--- TEST 1: Reacción de EWMA ante shock ---")
    np.random.seed(42)

    prices_calmo   = 1.08 + np.cumsum(np.random.normal(0, 0.0004, 40))
    prices_shock   = prices_calmo[-1] + np.cumsum(np.random.normal(0, 0.003, 5))
    prices_post    = prices_shock[-1] + np.cumsum(np.random.normal(0, 0.0004, 20))
    all_prices     = np.concatenate([prices_calmo, prices_shock, prices_post])

    df = make_df(all_prices)

    sigma_antes  = df['std'].iloc[35:40].mean()
    sigma_shock  = df['std'].iloc[40:45].mean()
    sigma_post   = df['std'].iloc[55:60].mean()

    print(f"  Sigma antes del shock:   {sigma_antes:.6f}")
    print(f"  Sigma durante el shock:  {sigma_shock:.6f}")
    print(f"  Sigma después del shock: {sigma_post:.6f}")

    assert sigma_shock > sigma_antes * 1.3, \
        f"EWMA debe elevar sigma durante shock. Ratio: {sigma_shock/sigma_antes:.2f}"
    assert sigma_post > sigma_antes, \
        "EWMA debe mantener sigma elevado después del shock (persistencia)"

    print("  ✅ EWMA reacciona correctamente al shock")


def test_ewma_menor_que_static_en_regimen_volatil():
    """En régimen volátil, z_ewma debe ser MENOR que z_static."""
    print("\n--- TEST 2: z_ewma < z_static en régimen volátil ---")
    np.random.seed(10)

    prices_calmo = 1.08 + np.cumsum(np.random.normal(0, 0.0004, 50))
    prices_volatil = prices_calmo[-1] + np.cumsum(np.random.normal(0, 0.002, 15))
    all_prices = np.concatenate([prices_calmo, prices_volatil])

    df = make_df(all_prices)

    resultado = detectar_anomalias(df)

    print(f"  z_score (EWMA, activo):  {resultado['z_score']:.4f}")
    print(f"  z_score (estático, ref): {resultado['z_score_static']:.4f}")
    print(f"  vol_ratio:               {resultado['vol_ratio']:.4f}")
    print(f"  Régimen volátil:         {resultado['regimen_volatil']}")

    if resultado['regimen_volatil']:
        assert abs(resultado['z_score']) < abs(resultado['z_score_static']), \
            "En régimen volátil, |z_ewma| debe ser menor que |z_static|"
        print("  ✅ z_ewma < z_static en régimen volátil — menos falsas señales")
    else:
        print("  ℹ️  Régimen no volátil en este test, diferencia esperada pequeña")


def test_lambda_diferente_por_timeframe():
    """Diferentes timeframes deben producir sigma diferente."""
    print("\n--- TEST 3: Lambda diferente por timeframe ---")
    np.random.seed(7)

    prices = 1.08 + np.cumsum(np.random.normal(0, 0.0008, 65))

    df_1m  = make_df(prices, timeframe="1M")
    df_4h  = make_df(prices, timeframe="4H")

    sigma_1m = df_1m['std'].iloc[-1]
    sigma_4h = df_4h['std'].iloc[-1]

    print(f"  Sigma final (1M, λ=0.94): {sigma_1m:.6f}")
    print(f"  Sigma final (4H, λ=0.98): {sigma_4h:.6f}")
    print(f"  Son diferentes: {abs(sigma_1m - sigma_4h) > 1e-8}")

    assert abs(sigma_1m - sigma_4h) > 1e-8, \
        "Diferentes λ deben producir sigma diferente"
    print("  ✅ Lambda por timeframe funciona correctamente")


def test_columna_std_static_presente():
    """std_static debe estar en el DataFrame para comparación."""
    print("\n--- TEST 4: Columna std_static presente ---")
    np.random.seed(42)
    prices = 1.08 + np.cumsum(np.random.normal(0, 0.0005, 65))
    df = make_df(prices)

    assert 'std_static' in df.columns, "Columna std_static debe existir"
    assert 'vol_ratio'   in df.columns, "Columna vol_ratio debe existir"
    assert 'std'          in df.columns, "Columna std (EWMA) debe existir"
    print(f"  Columnas presentes: std ✅  std_static ✅  vol_ratio ✅")
    print("  ✅ Todas las columnas de diagnóstico presentes")


if __name__ == "__main__":
    print("=" * 55)
    print("VALIDACIÓN FASE 1 — EWMA SIGMA DINÁMICO")
    print("=" * 55)

    test_ewma_reacciona_a_shock()
    test_ewma_menor_que_static_en_regimen_volatil()
    test_lambda_diferente_por_timeframe()
    test_columna_std_static_presente()

    print("\n" + "=" * 55)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 55)
    print("\nQué validar manualmente:")
    print("  TEST 2: vol_ratio > 1.3 = régimen volátil detectado")
    print("          En ese caso, z_ewma debe ser menor que z_static")
    print("          Esto significa: MENOS falsas señales en post-noticias")
    print("\nCuando estés conforme, confirma para proceder a Fase 2.")
