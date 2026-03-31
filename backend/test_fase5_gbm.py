# test_fase5_gbm.py — Tests unitarios del módulo GBM Monte Carlo
import pytest
import numpy as np
from calculos_gbm import simular_gbm, calcular_gbm_anomalia, _campos_nulos


# ============================================================
# simular_gbm()
# ============================================================

def test_prob_reversion_en_rango_valido():
    """La probabilidad de reversión debe estar siempre en [0, 1]."""
    resultado = simular_gbm(precio_actual=1.09, mu=0.0001, sigma_ewma=0.0005)
    p = resultado["gbm_prob_reversion"]
    assert 0.0 <= p <= 1.0, f"Probabilidad fuera de rango: {p}"


def test_percentiles_ordenados():
    """p5 ≤ p50 ≤ p95 siempre (distribución correcta)."""
    resultado = simular_gbm(precio_actual=1.09, mu=0.0001, sigma_ewma=0.0005)
    assert resultado["gbm_percentil_5"] <= resultado["gbm_percentil_50"], "p5 > p50"
    assert resultado["gbm_percentil_50"] <= resultado["gbm_percentil_95"], "p50 > p95"


def test_percentiles_alrededor_del_precio_actual():
    """Con sigma pequeño, los percentiles deben estar cerca del precio inicial."""
    precio = 1.0900
    resultado = simular_gbm(precio_actual=precio, mu=0.0, sigma_ewma=0.0001, n_paths=1000, n_horizonte=5)
    assert abs(resultado["gbm_percentil_50"] - precio) < 0.01, \
        f"Mediana muy lejos del precio: {resultado['gbm_percentil_50']}"


def test_sigma_cero_devuelve_nulos():
    """sigma_ewma = 0 debe retornar campos nulos (evita división por cero)."""
    resultado = simular_gbm(precio_actual=1.09, mu=0.0001, sigma_ewma=0.0)
    assert resultado["gbm_prob_reversion"] is None


def test_sigma_nan_devuelve_nulos():
    """sigma NaN debe retornar campos nulos."""
    resultado = simular_gbm(precio_actual=1.09, mu=0.0, sigma_ewma=float("nan"))
    assert resultado["gbm_prob_reversion"] is None


def test_reproducibilidad_con_semilla():
    """Con misma semilla numpy, el resultado debe ser idéntico."""
    np.random.seed(42)
    r1 = simular_gbm(precio_actual=1.09, mu=0.0001, sigma_ewma=0.0005)
    np.random.seed(42)
    r2 = simular_gbm(precio_actual=1.09, mu=0.0001, sigma_ewma=0.0005)
    assert r1["gbm_prob_reversion"] == r2["gbm_prob_reversion"]


def test_mayor_sigma_mayor_dispersion():
    """Mayor volatilidad → mayor rango entre p5 y p95."""
    np.random.seed(0)
    r_baja = simular_gbm(precio_actual=1.09, mu=0.0, sigma_ewma=0.0002, n_paths=500)
    np.random.seed(0)
    r_alta = simular_gbm(precio_actual=1.09, mu=0.0, sigma_ewma=0.002, n_paths=500)
    rango_baja = r_baja["gbm_percentil_95"] - r_baja["gbm_percentil_5"]
    rango_alta = r_alta["gbm_percentil_95"] - r_alta["gbm_percentil_5"]
    assert rango_alta > rango_baja, "Mayor sigma debería dar mayor dispersión"


# ============================================================
# calcular_gbm_anomalia()
# ============================================================

def test_sin_anomalia_devuelve_nulos():
    """z_score dentro de umbral → todos los campos None."""
    resultado = calcular_gbm_anomalia(
        z_score=1.5, mu=0.0001, sigma_ewma=0.0005,
        precio_close=1.09, timeframe="30M"
    )
    assert resultado["gbm_prob_reversion"] is None
    assert resultado["gbm_horizonte_velas"] is None


def test_anomalia_compra_activa_gbm():
    """z_score < -2 → GBM debe activarse y retornar prob."""
    resultado = calcular_gbm_anomalia(
        z_score=-2.5, mu=0.0001, sigma_ewma=0.0005,
        precio_close=1.09, timeframe="30M"
    )
    assert resultado["gbm_prob_reversion"] is not None
    assert 0.0 <= resultado["gbm_prob_reversion"] <= 1.0


def test_anomalia_venta_activa_gbm():
    """z_score > +2 → GBM debe activarse."""
    resultado = calcular_gbm_anomalia(
        z_score=3.1, mu=0.0001, sigma_ewma=0.0005,
        precio_close=1.09, timeframe="1H"
    )
    assert resultado["gbm_prob_reversion"] is not None


def test_horizonte_correcto_por_timeframe():
    """El horizonte debe coincidir con el dict GBM_HORIZONTE_VELAS."""
    from config import GBM_HORIZONTE_VELAS
    for tf, esperado in GBM_HORIZONTE_VELAS.items():
        resultado = calcular_gbm_anomalia(
            z_score=-3.0, mu=0.0, sigma_ewma=0.0005,
            precio_close=1.09, timeframe=tf
        )
        assert resultado["gbm_horizonte_velas"] == esperado, \
            f"Horizonte incorrecto para {tf}: {resultado['gbm_horizonte_velas']} != {esperado}"


def test_campos_nulos_estructura():
    """_campos_nulos() debe tener exactamente 5 claves."""
    nulos = _campos_nulos()
    claves_esperadas = {
        "gbm_prob_reversion", "gbm_horizonte_velas",
        "gbm_percentil_5", "gbm_percentil_50", "gbm_percentil_95"
    }
    assert set(nulos.keys()) == claves_esperadas
    assert all(v is None for v in nulos.values())
