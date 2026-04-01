# calculos_gbm.py — Movimiento Browniano Geométrico (Monte Carlo)
#
# Implementa simulación de caminos de precio bajo GBM discreto.
# Se activa únicamente en velas con anomalía (|z_score| > umbral).
#
# Fórmula GBM discreto (dt = 1 vela, mu y sigma ya en unidades por vela):
#   r_k = (mu - sigma²/2) + sigma · Z_k     Z_k ~ N(0,1)
#   S_k = S_0 · exp(Σ r_i,  i=1..k)
#
# Reversión: un camino "revierte" si en alguna vela del horizonte
#   |r_k - mu| ≤ sigma  (el retorno vuelve a estar dentro de 1σ de la media)
#
import numpy as np
from config import GBM_N_PATHS, GBM_HORIZONTE_VELAS, GBM_Z_UMBRAL_ACTIVACION


def simular_gbm(precio_actual, mu, sigma_ewma, n_paths=GBM_N_PATHS, n_horizonte=10):
    """
    Ejecuta simulación Monte Carlo vectorizada bajo GBM discreto.

    Args:
        precio_actual: float — precio de cierre de la vela con anomalía (S_0)
        mu:            float — drift (rolling mean de log returns)
        sigma_ewma:    float — volatilidad EWMA condicional
        n_paths:       int   — número de caminos simulados
        n_horizonte:   int   — velas hacia adelante

    Returns:
        dict con:
            gbm_prob_reversion: float [0,1] — fracción de caminos que revierten
            gbm_percentil_5:    float — percentil 5 de S al final del horizonte
            gbm_percentil_50:   float — mediana de S al final del horizonte
            gbm_percentil_95:   float — percentil 95 de S al final del horizonte
    """
    if sigma_ewma <= 0 or np.isnan(sigma_ewma) or np.isnan(mu):
        return _campos_nulos()

    # Matriz de ruido: shape (n_paths, n_horizonte)
    Z = np.random.standard_normal((n_paths, n_horizonte))

    # Retornos simulados con corrección de Ito: (mu - sigma²/2) + sigma·Z
    drift_corregido = mu - 0.5 * sigma_ewma ** 2
    log_returns_sim = drift_corregido + sigma_ewma * Z   # (n_paths, n_horizonte)

    # Condición de reversión: ∃ vela k donde |r_k - mu| ≤ sigma
    reversion_por_vela = np.abs(log_returns_sim - mu) <= sigma_ewma  # (n_paths, n_horizonte)
    revierte = np.any(reversion_por_vela, axis=1)                    # (n_paths,)
    prob_reversion = float(np.mean(revierte))

    # Caminos de precio acumulados: S_k = S_0 · exp(suma acumulada de retornos)
    precios_sim = precio_actual * np.exp(np.cumsum(log_returns_sim, axis=1))
    precios_finales = precios_sim[:, -1]   # precio al final del horizonte

    return {
        "gbm_prob_reversion": round(prob_reversion, 4),
        "gbm_percentil_5":    round(float(np.percentile(precios_finales, 5)), 6),
        "gbm_percentil_50":   round(float(np.percentile(precios_finales, 50)), 6),
        "gbm_percentil_95":   round(float(np.percentile(precios_finales, 95)), 6),
    }


def calcular_gbm_anomalia(z_score, mu, sigma_ewma, precio_close, timeframe=None):
    """
    Punto de entrada desde main.py/build_rows().
    Ejecuta GBM solo si |z_score| supera el umbral de activación.

    Args:
        z_score:      float — z-score EWMA de la vela actual
        mu:           float — media móvil del retorno logarítmico
        sigma_ewma:   float — sigma EWMA de la vela actual
        precio_close: float — precio de cierre de la vela (S_0 para simulación)
        timeframe:    str   — nombre del timeframe (ej: "30M") para seleccionar horizonte

    Returns:
        dict con campos GBM. Si no hay anomalía, todos los valores son None.
    """
    if abs(z_score) <= GBM_Z_UMBRAL_ACTIVACION:
        return _campos_nulos()

    n_horizonte = GBM_HORIZONTE_VELAS.get(timeframe, 10) if timeframe else 10

    resultado = simular_gbm(
        precio_actual=precio_close,
        mu=mu,
        sigma_ewma=sigma_ewma,
        n_paths=GBM_N_PATHS,
        n_horizonte=n_horizonte,
    )
    resultado["gbm_horizonte_velas"] = n_horizonte
    return resultado


def _campos_nulos():
    """Devuelve dict con todos los campos GBM en None (vela sin anomalía)."""
    return {
        "gbm_prob_reversion":  None,
        "gbm_horizonte_velas": None,
        "gbm_percentil_5":     None,
        "gbm_percentil_50":    None,
        "gbm_percentil_95":    None,
    }
