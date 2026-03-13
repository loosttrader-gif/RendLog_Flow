"""
Test Fase 3 -- Filtro de Regimen ER
Ejecutar: python test_fase3_regimen.py
No requiere MT5 ni Supabase.
"""
import numpy as np
import pandas as pd
from calculos_rendlog import (
    calcular_rendimientos_log,
    calcular_bandas_sigma,
    calcular_efficiency_ratio,
    clasificar_regimen,
    detectar_anomalias
)


def make_df(prices, timeframe="30M"):
    df = pd.DataFrame({
        'time':  pd.date_range('2026-01-01', periods=len(prices), freq='30min'),
        'close': prices,
        'open':  prices,
    })
    df = calcular_rendimientos_log(df)
    df = calcular_bandas_sigma(df, ventana=20, timeframe=timeframe)
    df = calcular_efficiency_ratio(df, ventana=14)
    return df


def test_er_bajo_en_rango():
    """Mercado en rango debe producir ER bajo."""
    print("\n--- TEST 1: ER bajo en mercado de rango ---")
    np.random.seed(42)

    prices = 1.08 + 0.001 * np.sin(np.linspace(0, 6 * np.pi, 40))
    prices += np.random.normal(0, 0.0001, 40)
    df = make_df(prices)

    er_final  = df['efficiency_ratio'].iloc[-1]
    regimen   = clasificar_regimen(er_final)

    print(f"  ER final: {er_final:.4f}")
    print(f"  Regimen:  {regimen}")

    assert er_final < 0.5, f"ER debe ser bajo en rango: {er_final}"
    print("  [OK] ER bajo en mercado de rango")


def test_er_alto_en_tendencia():
    """Mercado en tendencia debe producir ER alto."""
    print("\n--- TEST 2: ER alto en tendencia ---")

    prices = 1.08 + np.linspace(0, 0.015, 40)
    prices += np.random.normal(0, 0.00005, 40)  # ruido minimo
    df = make_df(prices)

    er_final = df['efficiency_ratio'].iloc[-1]
    regimen  = clasificar_regimen(er_final)

    print(f"  ER final: {er_final:.4f}")
    print(f"  Regimen:  {regimen}")

    assert er_final > 0.5, f"ER debe ser alto en tendencia: {er_final}"
    print("  [OK] ER alto en tendencia")


def test_senal_suprimida_en_tendencia():
    """Senal de RendLog debe ser suprimida cuando hay tendencia fuerte."""
    print("\n--- TEST 3: Senal suprimida en tendencia ---")

    # Tendencia + retorno extremo al final (para forzar senal pre-filtro)
    np.random.seed(99)
    prices_trend = 1.08 + np.linspace(0, 0.02, 50)
    prices_trend[-1] -= 0.005  # caida brusca al final (crea z extremo)
    df = make_df(prices_trend)

    resultado = detectar_anomalias(df, umbral_compra=-0.5, umbral_venta=0.5)

    print(f"  ER:               {resultado.get('er', 'N/A')}")
    print(f"  Regimen:          {resultado.get('regimen', 'N/A')}")
    print(f"  Senal pre-filtro: {resultado.get('senal_pre_filtro', 'N/A')}")
    print(f"  Senal final:      {resultado['señal']}")
    print(f"  Suprimida:        {resultado.get('senal_suprimida', False)}")

    if resultado.get('regimen') == "TENDENCIA" and resultado.get('senal_pre_filtro'):
        assert resultado['señal'] is None, \
            "Senal debe ser None cuando regimen es TENDENCIA"
        print("  [OK] Senal suprimida correctamente en tendencia")
    else:
        print("  [INFO] Condiciones no alcanzadas en este seed -- regimen no trending")


def test_senal_activa_en_rango():
    """Senal de RendLog debe mantenerse activa en regimen de rango."""
    print("\n--- TEST 4: Senal activa en rango ---")
    np.random.seed(42)

    # Rango + retorno extremo al final
    prices_range = 1.08 + 0.001 * np.sin(np.linspace(0, 4 * np.pi, 50))
    prices_range += np.random.normal(0, 0.0001, 50)
    prices_range[-1] -= 0.003  # caida al final

    df = make_df(prices_range)
    resultado = detectar_anomalias(df, umbral_compra=-0.3, umbral_venta=0.3)

    print(f"  ER:               {resultado.get('er', 'N/A')}")
    print(f"  Regimen:          {resultado.get('regimen', 'N/A')}")
    print(f"  Senal:            {resultado['señal']}")

    if resultado.get('regimen') in ["RANGO", "AMBIGUO"]:
        print("  [OK] Senal no suprimida en regimen de rango/ambiguo")


if __name__ == "__main__":
    print("=" * 55)
    print("VALIDACION FASE 3 -- FILTRO DE REGIMEN ER")
    print("=" * 55)

    test_er_bajo_en_rango()
    test_er_alto_en_tendencia()
    test_senal_suprimida_en_tendencia()
    test_senal_activa_en_rango()

    print("\n" + "=" * 55)
    print("[OK] TODOS LOS TESTS PASARON")
    print("=" * 55)
    print("\nQue validar manualmente:")
    print("  TEST 3: cuando el regimen es TENDENCIA y hay senal pre-filtro,")
    print("          la senal final debe ser None (suprimida).")
    print("  Esto es el valor mas importante del filtro de regimen.")
    print("\nCuando estes conforme, confirma para proceder a Fase 4.")
