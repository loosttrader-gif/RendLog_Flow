# calculos_multipair.py — Álgebra lineal multi-par: Covarianza + PCA
#
# Fórmulas:
#   Matriz de retornos: R [T × 4] — inner join por timestamp entre 4 pares
#   Covarianza:         Σ = R.T @ R / (T-1)   [4×4]
#   PCA (eigh):         Σ = V·Λ·V.T  → eigenvalues λ, eigenvectors V
#   Correlación:        Corr[i,j] = Σ[i,j] / sqrt(Σ[i,i] · Σ[j,j])
#   Z-score vectorizado: Z = (R[-1,:] - μ_vec) / σ_vec   (sin loops)
#
import numpy as np
import pandas as pd
from config import (
    PCA_PC1_VARIANZA_UMBRAL,
    PCA_PC1_LOADING_UMBRAL,
    PCA_CORRELACION_UMBRAL,
    PCA_MIN_FILAS_ALINEADAS,
)


def construir_matriz_retornos(dataframes):
    """
    Alinea DataFrames por timestamp y construye la matriz de retornos R.

    Usa inner join en la columna 'time' para garantizar alineación exacta.
    Descarta filas donde cualquier símbolo tiene NaN en log_return.

    Args:
        dataframes: dict[str, pd.DataFrame] — clave = symbol, valor = df con
                    columnas 'time' y 'log_return'

    Returns:
        tuple(R, symbols, timestamps):
            R:          np.ndarray [n_alineadas × n_symbols]
            symbols:    list[str] en el orden de las columnas de R
            timestamps: pd.Series con los timestamps alineados
        Retorna (None, None, None) si hay datos insuficientes.
    """
    if not dataframes:
        return None, None, None

    symbols = list(dataframes.keys())

    # Construir una sola tabla con retornos por símbolo, alineada por 'time'
    merged = None
    for sym in symbols:
        df = dataframes[sym][['time', 'log_return']].copy()
        df = df.rename(columns={'log_return': sym})
        if merged is None:
            merged = df
        else:
            merged = pd.merge(merged, df, on='time', how='inner')

    if merged is None or len(merged) < PCA_MIN_FILAS_ALINEADAS:
        return None, None, None

    # Eliminar filas con cualquier NaN
    merged = merged.dropna(subset=symbols)

    if len(merged) < PCA_MIN_FILAS_ALINEADAS:
        return None, None, None

    R = merged[symbols].values.astype(np.float64)   # [T × n_symbols]
    timestamps = merged['time']

    return R, symbols, timestamps


def calcular_covarianza(R):
    """
    Calcula la matriz de covarianza muestral.

    Σ = R.T @ R / (T - 1)   [equivalente a pd.DataFrame(R).cov()]

    Args:
        R: np.ndarray [T × n_symbols]

    Returns:
        np.ndarray [n_symbols × n_symbols]
    """
    T = R.shape[0]
    R_centrado = R - R.mean(axis=0)   # Centrar por columna
    return R_centrado.T @ R_centrado / (T - 1)


def calcular_pca(cov_matrix, symbols):
    """
    Descomposición espectral de la matriz de covarianza.

    Usa np.linalg.eigh (simétrica → valores propios reales, más estable que eig).
    Normaliza signo de PC1 para que el loading de EURUSD sea siempre positivo
    (resuelve la ambigüedad de signo entre ciclos).

    Args:
        cov_matrix: np.ndarray [n_symbols × n_symbols]
        symbols:    list[str] en el orden de las columnas de cov_matrix

    Returns:
        dict con:
            pc1_loadings:    dict[symbol -> float] — loadings en PC1
            pc1_varianza:    float — fracción de varianza explicada por PC1
            varianza_total:  np.ndarray — fracción explicada por cada PC
            pca_valido:      bool — True si PC1 explica suficiente varianza
    """
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

    # eigh devuelve en orden ascendente → invertir para descendente
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues  = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Varianza explicada
    total = np.sum(np.maximum(eigenvalues, 0))
    if total == 0:
        return _pca_nulo(symbols)

    varianza_explicada = np.maximum(eigenvalues, 0) / total
    pc1_varianza = float(varianza_explicada[0])

    # PC1 loadings (primera columna de eigenvectors)
    pc1_loadings_arr = eigenvectors[:, 0].copy()

    # Normalización de signo: EURUSD siempre positivo
    if "EURUSD" in symbols:
        eurusd_idx = symbols.index("EURUSD")
        if pc1_loadings_arr[eurusd_idx] < 0:
            pc1_loadings_arr = -pc1_loadings_arr

    pc1_loadings = {sym: float(pc1_loadings_arr[i]) for i, sym in enumerate(symbols)}

    return {
        "pc1_loadings": pc1_loadings,
        "pc1_varianza": pc1_varianza,
        "varianza_total": varianza_explicada.tolist(),
        "pca_valido": True,
    }


def detectar_exposicion_usd(cov_matrix, symbols):
    """
    Calcula la correlación de cada par con EURUSD y detecta alta exposición USD.

    Exposición alta: correlación con EURUSD > PCA_CORRELACION_UMBRAL.

    Args:
        cov_matrix: np.ndarray [n_symbols × n_symbols]
        symbols:    list[str]

    Returns:
        dict[symbol -> bool] — True si el par tiene alta correlación con EURUSD
    """
    diag = np.sqrt(np.diag(cov_matrix))
    # Evitar división por cero
    diag_safe = np.where(diag > 0, diag, 1.0)
    corr_matrix = cov_matrix / np.outer(diag_safe, diag_safe)
    np.fill_diagonal(corr_matrix, 1.0)

    exposicion = {}
    if "EURUSD" not in symbols:
        return {sym: False for sym in symbols}

    eurusd_idx = symbols.index("EURUSD")
    for i, sym in enumerate(symbols):
        if sym == "EURUSD":
            exposicion[sym] = False
        else:
            corr_con_eurusd = float(corr_matrix[i, eurusd_idx])
            exposicion[sym] = abs(corr_con_eurusd) > PCA_CORRELACION_UMBRAL

    return exposicion


def calcular_correlacion_con_eurusd(cov_matrix, symbols):
    """
    Retorna la correlación escalar de cada símbolo con EURUSD.

    Args:
        cov_matrix: np.ndarray [n_symbols × n_symbols]
        symbols:    list[str]

    Returns:
        dict[symbol -> float | None]
    """
    diag = np.sqrt(np.diag(cov_matrix))
    diag_safe = np.where(diag > 0, diag, 1.0)
    corr_matrix = cov_matrix / np.outer(diag_safe, diag_safe)
    np.fill_diagonal(corr_matrix, 1.0)

    if "EURUSD" not in symbols:
        return {sym: None for sym in symbols}

    eurusd_idx = symbols.index("EURUSD")
    return {
        sym: (None if sym == "EURUSD" else round(float(corr_matrix[i, eurusd_idx]), 4))
        for i, sym in enumerate(symbols)
    }


def calcular_zscores_vectorizados(R, mu_vec, sigma_vec):
    """
    Computa z-scores para todos los símbolos en la última vela — sin loops.

    Z = (R[-1,:] - mu_vec) / sigma_vec

    Args:
        R:         np.ndarray [T × n_symbols]
        mu_vec:    np.ndarray [n_symbols] — media móvil por símbolo
        sigma_vec: np.ndarray [n_symbols] — sigma EWMA por símbolo

    Returns:
        np.ndarray [n_symbols] — z-score de la última vela para cada par
    """
    sigma_safe = np.where(sigma_vec > 0, sigma_vec, 1.0)
    return (R[-1, :] - mu_vec) / sigma_safe


def es_movimiento_sistemico(pca_result, symbol):
    """
    Determina si la anomalía de un símbolo es sistémica (driver USD).

    Condición:
        PC1 explica > PCA_PC1_VARIANZA_UMBRAL (60%) de la varianza
        AND loading del símbolo en PC1 > PCA_PC1_LOADING_UMBRAL (0.70)

    Args:
        pca_result: dict devuelto por calcular_pca() — puede ser None
        symbol:     str — símbolo a evaluar

    Returns:
        bool — True si el movimiento es sistémico
    """
    if pca_result is None or not pca_result.get("pca_valido", False):
        return False

    pc1_varianza = pca_result.get("pc1_varianza", 0.0)
    loading = abs(pca_result.get("pc1_loadings", {}).get(symbol, 0.0))

    return pc1_varianza > PCA_PC1_VARIANZA_UMBRAL and loading > PCA_PC1_LOADING_UMBRAL


def _pca_nulo(symbols):
    """Estructura PCA vacía cuando el cálculo no es posible."""
    return {
        "pc1_loadings": {sym: None for sym in symbols},
        "pc1_varianza": None,
        "varianza_total": None,
        "pca_valido": False,
    }
