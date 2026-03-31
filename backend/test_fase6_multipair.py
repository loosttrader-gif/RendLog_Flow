# test_fase6_multipair.py — Tests unitarios del módulo multi-par y PCA
import pytest
import numpy as np
import pandas as pd
from calculos_multipair import (
    construir_matriz_retornos,
    calcular_covarianza,
    calcular_pca,
    detectar_exposicion_usd,
    calcular_correlacion_con_eurusd,
    calcular_zscores_vectorizados,
    es_movimiento_sistemico,
)


# ============================================================
# Fixtures reutilizables
# ============================================================

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
N_ROWS = 50


def _make_df(symbol, n=N_ROWS, seed=None):
    """DataFrame sintético de retornos para pruebas."""
    rng = np.random.default_rng(seed or hash(symbol) % 2**31)
    times = pd.date_range("2026-01-01", periods=n, freq="30min")
    returns = rng.normal(0, 0.0005, n)
    return pd.DataFrame({"time": times, "log_return": returns})


def _make_dfs(n=N_ROWS):
    return {sym: _make_df(sym, n) for sym in SYMBOLS}


# ============================================================
# construir_matriz_retornos()
# ============================================================

def test_matriz_forma_correcta():
    """R debe tener forma [n_alineadas × 4]."""
    dfs = _make_dfs()
    R, syms, ts = construir_matriz_retornos(dfs)
    assert R is not None
    assert R.shape[1] == len(SYMBOLS)
    assert R.shape[0] > 0


def test_matriz_sin_nan():
    """La matriz resultante no debe tener NaN."""
    dfs = _make_dfs()
    R, syms, ts = construir_matriz_retornos(dfs)
    assert not np.isnan(R).any(), "La matriz contiene NaN"


def test_insuficientes_datos_retorna_nulo():
    """Con menos de PCA_MIN_FILAS_ALINEADAS filas, retorna (None, None, None)."""
    dfs = {sym: _make_df(sym, n=10) for sym in SYMBOLS}
    R, syms, ts = construir_matriz_retornos(dfs)
    assert R is None


def test_dict_vacio_retorna_nulo():
    R, syms, ts = construir_matriz_retornos({})
    assert R is None


def test_orden_columnas_respeta_symbols():
    """El orden de columnas en R debe coincidir con el orden de SYMBOLS."""
    dfs = _make_dfs()
    R, syms, ts = construir_matriz_retornos(dfs)
    assert syms == SYMBOLS


# ============================================================
# calcular_covarianza()
# ============================================================

def test_covarianza_simetrica():
    """Σ debe ser una matriz simétrica."""
    dfs = _make_dfs()
    R, _, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    np.testing.assert_allclose(cov, cov.T, atol=1e-12)


def test_covarianza_diagonal_positiva():
    """La diagonal de Σ (varianzas) debe ser positiva."""
    dfs = _make_dfs()
    R, _, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    assert np.all(np.diag(cov) > 0), "Hay varianzas no positivas"


def test_covarianza_forma_cuadrada():
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    assert cov.shape == (len(syms), len(syms))


# ============================================================
# calcular_pca()
# ============================================================

def test_varianza_explicada_suma_uno():
    """La suma de varianzas explicadas debe ser ≈ 1."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    pca = calcular_pca(cov, syms)
    total = sum(pca["varianza_total"])
    assert abs(total - 1.0) < 1e-6, f"Suma de varianzas explicadas: {total}"


def test_pc1_varianza_el_mayor():
    """PC1 debe explicar la mayor fracción de varianza."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    pca = calcular_pca(cov, syms)
    pc1 = pca["varianza_total"][0]
    for v in pca["varianza_total"][1:]:
        assert pc1 >= v, "PC1 no es el componente dominante"


def test_eurusd_loading_positivo():
    """El loading de EURUSD en PC1 debe ser positivo (convención de signo)."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    pca = calcular_pca(cov, syms)
    assert pca["pc1_loadings"]["EURUSD"] > 0


def test_pca_contiene_todos_los_simbolos():
    """pc1_loadings debe tener una entrada por cada símbolo."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    pca = calcular_pca(cov, syms)
    assert set(pca["pc1_loadings"].keys()) == set(SYMBOLS)


# ============================================================
# detectar_exposicion_usd()
# ============================================================

def test_eurusd_no_tiene_exposicion_propia():
    """EURUSD nunca debe marcarse como 'alta exposición a sí mismo'."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    exp = detectar_exposicion_usd(cov, syms)
    assert exp["EURUSD"] is False


def test_exposicion_retorna_todos_los_simbolos():
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    exp = detectar_exposicion_usd(cov, syms)
    assert set(exp.keys()) == set(SYMBOLS)


# ============================================================
# calcular_correlacion_con_eurusd()
# ============================================================

def test_correlacion_diagonal_es_none():
    """La correlación de EURUSD con sí mismo debe ser None."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    corr = calcular_correlacion_con_eurusd(cov, syms)
    assert corr["EURUSD"] is None


def test_correlacion_en_rango():
    """Las correlaciones deben estar en [-1, 1]."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    corr = calcular_correlacion_con_eurusd(cov, syms)
    for sym, v in corr.items():
        if v is not None:
            assert -1.0 <= v <= 1.0, f"Correlación fuera de rango para {sym}: {v}"


def test_pares_identicos_tienen_correlacion_uno():
    """Si dos pares tienen retornos idénticos, la correlación debe ser ≈ 1."""
    times = pd.date_range("2026-01-01", periods=N_ROWS, freq="30min")
    retornos = np.random.default_rng(0).normal(0, 0.0005, N_ROWS)
    dfs = {sym: pd.DataFrame({"time": times, "log_return": retornos}) for sym in SYMBOLS}
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    corr = calcular_correlacion_con_eurusd(cov, syms)
    for sym, v in corr.items():
        if v is not None:
            assert abs(v - 1.0) < 1e-6, f"Correlación esperada 1.0 para {sym}, obtenida {v}"


# ============================================================
# calcular_zscores_vectorizados()
# ============================================================

def test_zscores_vectorizados_forma():
    """Z debe tener shape [n_symbols]."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    mu_vec = R.mean(axis=0)
    sigma_vec = R.std(axis=0)
    Z = calcular_zscores_vectorizados(R, mu_vec, sigma_vec)
    assert Z.shape == (len(syms),)


def test_zscores_no_nan():
    """Z no debe contener NaN."""
    dfs = _make_dfs()
    R, syms, _ = construir_matriz_retornos(dfs)
    mu_vec = R.mean(axis=0)
    sigma_vec = R.std(axis=0)
    Z = calcular_zscores_vectorizados(R, mu_vec, sigma_vec)
    assert not np.isnan(Z).any()


# ============================================================
# es_movimiento_sistemico()
# ============================================================

def test_sistemico_con_pc1_dominante():
    """
    Con correlación perfecta entre todos los pares, PC1 explica ~100%
    y el movimiento debe clasificarse como sistémico.
    """
    times = pd.date_range("2026-01-01", periods=N_ROWS, freq="30min")
    retornos = np.random.default_rng(7).normal(0, 0.0005, N_ROWS)
    dfs = {sym: pd.DataFrame({"time": times, "log_return": retornos}) for sym in SYMBOLS}
    R, syms, _ = construir_matriz_retornos(dfs)
    cov = calcular_covarianza(R)
    pca = calcular_pca(cov, syms)
    # Con retornos idénticos PC1 explica 100%
    assert es_movimiento_sistemico(pca, "EURUSD")


def test_no_sistemico_cuando_pca_none():
    """Sin resultado PCA disponible, es_movimiento_sistemico debe retornar False."""
    assert es_movimiento_sistemico(None, "EURUSD") is False


def test_no_sistemico_cuando_pca_invalido():
    pca_invalido = {"pca_valido": False, "pc1_varianza": 0.8, "pc1_loadings": {"EURUSD": 0.9}}
    assert es_movimiento_sistemico(pca_invalido, "EURUSD") is False
