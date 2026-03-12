"""
Test Fase 2 -- Distribucion t de Student
Ejecutar: python test_fase2_distribucion_t.py
No requiere MT5 ni Supabase.
"""
import numpy as np
import pandas as pd
from scipy import stats
from calculos_rendlog import (
    calcular_rendimientos_log,
    calcular_bandas_sigma,
    estimar_distribucion_t,
    calcular_percentil_real,
    calcular_umbrales_calibrados
)


def make_df_t(nu=4, n=100, scale=0.0008, seed=42):
    """Genera DataFrame con retornos desde distribucion t conocida."""
    np.random.seed(seed)
    returns = stats.t.rvs(df=nu, scale=scale, size=n)
    prices  = 1.08 + np.cumsum(returns)
    df = pd.DataFrame({
        'time':  pd.date_range('2026-01-01', periods=n, freq='30min'),
        'close': prices,
        'open':  prices,
    })
    df = calcular_rendimientos_log(df)
    df = calcular_bandas_sigma(df, ventana=20, timeframe="30M")
    return df


def test_estimacion_nu():
    """nu estimado debe estar cerca del nu verdadero."""
    print("\n--- TEST 1: Estimacion de nu ---")

    nu_verdadero = 4.0
    df = make_df_t(nu=nu_verdadero, n=200)
    resultado = estimar_distribucion_t(df, min_datos=50)

    assert resultado is not None, "Debe retornar resultado con 200 datos"
    print(f"  nu verdadero: {nu_verdadero}")
    print(f"  nu estimado:  {resultado['nu']}")
    print(f"  Curtosis empirica: {resultado['curtosis_empirica']}")
    print(f"  Descripcion: {resultado['descripcion']}")

    assert 2.1 <= resultado['nu'] <= 10.0, \
        f"nu estimado fuera de rango razonable: {resultado['nu']}"
    print("  [OK] Estimacion de nu en rango razonable")


def test_percentil_real_menor_que_normal():
    """Bajo colas pesadas, el percentil real debe ser menor que el gaussiano."""
    print("\n--- TEST 2: Percentil real < percentil gaussiano ---")

    nu = 4.0
    for z in [1.5, 2.0, 2.5, 3.0]:
        pct_normal = stats.norm.cdf(z) * 100
        pct_real   = calcular_percentil_real(z, nu=nu)
        diff       = pct_normal - pct_real
        print(f"  z={z}s: gaussiano={pct_normal:.1f}% | real t(nu={nu})={pct_real:.1f}% | sobreestima {diff:.1f}%")
        assert pct_normal > pct_real, \
            f"Normal debe sobreestimar percentil con colas pesadas en z={z}"

    print("  [OK] Normal sobreestima percentiles bajo colas pesadas")


def test_umbrales_calibrados_son_mayores():
    """Umbrales recalibrados bajo distribucion t deben ser > originales."""
    print("\n--- TEST 3: Umbrales calibrados mas exigentes ---")

    nu = 4.0
    calibracion = calcular_umbrales_calibrados(nu)

    print(f"\n  {'Umbral':<15} {'Original':<10} {'Pct Normal':<13} {'Pct Real':<12} {'Equivalente t'}")
    print(f"  {'-'*65}")

    for nombre, datos in calibracion.items():
        print(f"  {nombre:<15} "
              f"{datos['z_original']:<10} "
              f"{datos['percentil_bajo_normal']:<13} "
              f"{datos['percentil_real_bajo_t']:<12} "
              f"{datos['z_equivalente_t']}")

        assert datos['z_equivalente_t'] > datos['z_original'], \
            f"Umbral calibrado debe ser > original para {nombre}"

    print("\n  [OK] Umbrales calibrados son mas exigentes que bajo normalidad")


def test_datos_insuficientes():
    """Con pocos datos debe retornar None."""
    print("\n--- TEST 4: Manejo de datos insuficientes ---")

    df = make_df_t(n=20)
    resultado = estimar_distribucion_t(df, min_datos=50)

    assert resultado is None, "Debe retornar None con datos insuficientes"
    print("  [OK] Retorna None correctamente con datos insuficientes")


if __name__ == "__main__":
    print("=" * 55)
    print("VALIDACION FASE 2 -- DISTRIBUCION t DE STUDENT")
    print("=" * 55)

    test_estimacion_nu()
    test_percentil_real_menor_que_normal()
    test_umbrales_calibrados_son_mayores()
    test_datos_insuficientes()

    print("\n" + "=" * 55)
    print("[OK] TODOS LOS TESTS PASARON")
    print("=" * 55)
    print("\nQue validar manualmente:")
    print("  TEST 3: revisa la columna 'Pct Real' vs 'Pct Normal'.")
    print("  La diferencia cuantifica cuanto estaba sobreestimando el sistema.")
    print("  Si la sobreestimacion > 1% en cada umbral, las correcciones valen.")
    print("\nCuando estes conforme, confirma para proceder a Fase 3.")
