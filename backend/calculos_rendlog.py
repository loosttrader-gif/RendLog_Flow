# calculos_rendlog.py — v3.0 Fase 1: EWMA Sigma Dinámico
import numpy as np
import pandas as pd
from config import (
    RENDLOG_LAMBDA_EWMA,
    RENDLOG_LAMBDA_DEFAULT,
    RENDLOG_LAMBDA_EWMA_SYMBOL,
    RENDLOG_ER_UMBRAL_RANGO,
    RENDLOG_ER_UMBRAL_TENDENCIA,
    RENDLOG_ER_VENTANA,
    RENDLOG_NU_MIN_DATOS
)

# Los parámetros estadísticos viven en config.py — no redefinas aquí


def calcular_rendimientos_log(df):
    """
    Calcula rendimientos logarítmicos.
    Formula: log(Close_t / Close_t-1)
    Sin cambios respecto a v2.0.
    """
    df = df.copy()
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    return df


def _calcular_ewma_std(returns_series: pd.Series, lambda_decay: float) -> pd.Series:
    """
    Calcula serie de sigma condicional EWMA para cada punto.

    La varianza EWMA en t depende de la varianza en t-1 y del
    retorno al cuadrado en t-1 (no el actual — causal).

    Args:
        returns_series: Serie de retornos logarítmicos
        lambda_decay:   Factor de decaimiento λ

    Returns:
        Serie de sigma condicional (misma longitud)
    """
    n = len(returns_series)
    returns = returns_series.values
    variance = np.zeros(n)

    # Inicialización: varianza de los primeros 5 retornos válidos
    valid_mask = ~np.isnan(returns)
    if valid_mask.sum() < 2:
        return pd.Series(np.zeros(n), index=returns_series.index)

    first_valid_idx = np.argmax(valid_mask)
    init_window = returns[first_valid_idx:first_valid_idx + 5]
    init_var = np.nanvar(init_window) if len(init_window) > 1 else 1e-10
    variance[first_valid_idx] = init_var if init_var > 0 else 1e-10

    for t in range(first_valid_idx + 1, n):
        r_prev = returns[t - 1]
        if np.isnan(r_prev):
            variance[t] = variance[t - 1]
        else:
            variance[t] = (
                lambda_decay * variance[t - 1] +
                (1 - lambda_decay) * r_prev ** 2
            )

    sigma = np.sqrt(np.maximum(variance, 1e-12))

    # Los primeros puntos sin datos son NaN (igual que el rolling std original)
    sigma_series = pd.Series(sigma, index=returns_series.index)
    sigma_series.iloc[:first_valid_idx] = np.nan

    return sigma_series


def calcular_bandas_sigma(df, ventana=20, timeframe=None, symbol=None):
    """
    Calcula media móvil y bandas sigma usando EWMA para sigma dinámico.

    Cambio respecto a v2.0:
      - 'std' ahora es sigma condicional EWMA, no rolling std estático
      - Las bandas reflejan la volatilidad ACTUAL, no la histórica promedio
      - Se agrega columna 'std_static' para comparación durante validación

    Cambio v4.1 (multi-par):
      - Acepta 'symbol' para seleccionar lambda específico del par.
        Si symbol está en RENDLOG_LAMBDA_EWMA_SYMBOL, usa ese dict;
        sino, fallback a RENDLOG_LAMBDA_EWMA por timeframe.

    Args:
        df:        DataFrame con columna 'log_return'
        ventana:   int — ventana para media móvil (sin cambio)
        timeframe: str — nombre del timeframe (ej: "30M", "1H")
        symbol:    str — nombre del par (ej: "GBPUSD"). None = fallback a EURUSD lambdas.

    Returns:
        DataFrame con columnas de bandas actualizadas
    """
    df = df.copy()

    # Seleccionar lambda: primero por símbolo+timeframe, luego por timeframe solo
    if symbol and symbol in RENDLOG_LAMBDA_EWMA_SYMBOL:
        lambda_decay = RENDLOG_LAMBDA_EWMA_SYMBOL[symbol].get(timeframe, RENDLOG_LAMBDA_DEFAULT)
    else:
        lambda_decay = RENDLOG_LAMBDA_EWMA.get(timeframe, RENDLOG_LAMBDA_DEFAULT)

    # Media móvil — sin cambio respecto a v2.0
    df['media'] = df['log_return'].rolling(window=ventana).mean()

    # Sigma estático original — se conserva para comparación en logs
    df['std_static'] = df['log_return'].rolling(window=ventana).std()

    # Sigma EWMA dinámico — reemplaza 'std' como valor activo
    df['std'] = _calcular_ewma_std(df['log_return'], lambda_decay)

    # Bandas ±2σ (ahora dinámicas)
    df['banda_2sigma_superior'] = df['media'] + 2 * df['std']
    df['banda_2sigma_inferior'] = df['media'] - 2 * df['std']

    # Bandas ±3σ (ahora dinámicas)
    df['banda_3sigma_superior'] = df['media'] + 3 * df['std']
    df['banda_3sigma_inferior'] = df['media'] - 3 * df['std']

    # Ratio de volatilidad: qué tan diferente es EWMA vs estático
    # > 1.3 = EWMA detecta que estamos en régimen volátil
    # < 0.7 = EWMA detecta que estamos en calma inusual
    df['vol_ratio'] = df['std'] / df['std_static'].replace(0, np.nan)
    df['vol_ratio'] = df['vol_ratio'].fillna(1.0)

    return df


def detectar_anomalias(df, umbral_compra=-2.0, umbral_venta=2.0, nu=None, pca_es_sistemico=False):
    """
    Detecta anomalías basadas en Z-score con sigma EWMA.

    Cambio respecto a v2.0:
      - z_score calculado con sigma EWMA (columna 'std')
      - Se agrega z_score_static para comparación en logs
      - Lógica de señal sin cambios
    Cambio Fase 2:
      - Agrega percentil_real y diagnóstico de distribución t

    Args:
        df:             DataFrame con rendimientos y bandas
        umbral_compra:  float (ej: -2.0)
        umbral_venta:   float (ej: +2.0)
        nu:             float — grados de libertad de distribución t (None = normal)

    Returns:
        dict con señal, z_score y diagnóstico adicional
    """
    ultimo_rendimiento = df['log_return'].iloc[-1]
    ultimo_sigma_ewma  = df['std'].iloc[-1]
    ultimo_sigma_static = df['std_static'].iloc[-1]
    ultima_media       = df['media'].iloc[-1]
    ultimo_vol_ratio   = df['vol_ratio'].iloc[-1]

    # Z-score con EWMA (activo)
    if not pd.isna(ultimo_sigma_ewma) and ultimo_sigma_ewma > 0:
        z_score = (ultimo_rendimiento - ultima_media) / ultimo_sigma_ewma
    else:
        z_score = 0

    # Z-score estático (para comparación en logs)
    if not pd.isna(ultimo_sigma_static) and ultimo_sigma_static > 0:
        z_score_static = (ultimo_rendimiento - ultima_media) / ultimo_sigma_static
    else:
        z_score_static = 0

    # Señal — lógica idéntica a v2.0
    señal  = None
    color  = None
    mensaje = "Sin anomalías detectadas"

    if z_score < umbral_compra:
        señal   = "COMPRA"
        color   = "green"
        mensaje = f"Rendimiento por debajo de {umbral_compra}σ. Buscar posible corrección alcista"
    elif z_score > umbral_venta:
        señal   = "VENTA"
        color   = "red"
        mensaje = f"Rendimiento por encima de {umbral_venta}σ. Buscar posible corrección bajista"

    # Fase 2: percentil real bajo distribución t
    percentil_real = calcular_percentil_real(z_score, nu=nu)

    # Fase 3: régimen actual
    er_actual = df['efficiency_ratio'].iloc[-1] if 'efficiency_ratio' in df.columns else np.nan
    regimen   = clasificar_regimen(er_actual)

    # Ajuste de señal según régimen de mercado (Efficiency Ratio)
    senal_original = señal  # guardar señal pre-filtro
    senal_suprimida_er  = False
    senal_suprimida_pca = False

    if señal is not None and regimen == "TENDENCIA":
        señal   = None
        color   = None
        senal_suprimida_er = True
        mensaje = f"Senal suprimida: mercado en tendencia (ER={er_actual:.3f}). RendLog sin edge."

    # Supresión adicional por PCA: movimiento sistémico del USD
    # Si el PCA detecta que PC1 (factor USD) domina, la señal de reversión no aplica
    if señal is not None and pca_es_sistemico:
        señal   = None
        color   = None
        senal_suprimida_pca = True
        mensaje = "Senal suprimida: movimiento sistemico USD detectado por PCA."

    senal_suprimida = senal_suprimida_er or senal_suprimida_pca

    return {
        # Campos originales — sin cambios de nombre (compatibilidad con main.py)
        'señal':       señal,
        'z_score':     float(z_score),
        'color':       color,
        'mensaje':     mensaje,
        'timestamp':   df['time'].iloc[-1],
        'rendimiento': float(ultimo_rendimiento),

        # Fase 1: diagnóstico EWMA
        'z_score_static':  float(z_score_static),
        'sigma_ewma':      float(ultimo_sigma_ewma) if not pd.isna(ultimo_sigma_ewma) else 0,
        'sigma_static':    float(ultimo_sigma_static) if not pd.isna(ultimo_sigma_static) else 0,
        'vol_ratio':       float(ultimo_vol_ratio),
        'regimen_volatil': bool(ultimo_vol_ratio > 1.3),

        # Fase 2: distribución t
        'percentil_real':     round(percentil_real, 2),
        'nu_distribucion':    round(nu, 2) if nu else None,
        'calibracion_activa': nu is not None,

        # Fase 3: régimen
        'er':                  float(er_actual) if not pd.isna(er_actual) else None,
        'regimen':             regimen,
        'senal_pre_filtro':    senal_original,
        'senal_suprimida':     senal_suprimida,
        'senal_suprimida_pca': senal_suprimida_pca,
    }


# ============================================================
# FASE 2 — DISTRIBUCIÓN t DE STUDENT
# ============================================================
from scipy import stats as scipy_stats


def estimar_distribucion_t(df, min_datos=50):
    """
    Estima parámetros de distribución t de Student desde retornos históricos.

    Usa Maximum Likelihood Estimation (MLE) via scipy.stats.t.fit().
    La distribución t captura las colas pesadas de EUR/USD mejor que la normal.

    Args:
        df:        DataFrame con columna 'log_return'
        min_datos: Mínimo de retornos válidos para estimar

    Returns:
        dict con parámetros estimados y diagnóstico,
        o None si hay datos insuficientes
    """
    returns = df['log_return'].dropna().values

    if len(returns) < min_datos:
        return None

    try:
        # MLE: estima (df=nu, loc=mu, scale=sigma)
        nu, mu, sigma = scipy_stats.t.fit(returns)

        # Clampear nu a rango válido para forex (evitar estimaciones degeneradas)
        nu = float(np.clip(nu, 2.1, 30.0))

        # Curtosis empírica vs teórica
        curtosis_empirica = float(scipy_stats.kurtosis(returns, fisher=False))
        curtosis_teorica  = (6 / (nu - 4)) if nu > 4 else float('inf')

        # Asimetría (skewness)
        asimetria = float(scipy_stats.skew(returns))

        return {
            'nu':               round(nu, 3),
            'mu':               round(float(mu), 8),
            'sigma_t':          round(float(sigma), 8),
            'curtosis_empirica': round(curtosis_empirica, 3),
            'curtosis_teorica':  round(curtosis_teorica, 3) if nu > 4 else None,
            'asimetria':        round(asimetria, 4),
            'n_datos':          len(returns),
            'descripcion': (
                "Colas muy pesadas (tipico forex stress)" if nu < 5 else
                "Colas moderadas"                         if nu < 10 else
                "Casi normal"
            )
        }

    except Exception:
        return None


def calcular_percentil_real(z_score, nu=None):
    """
    Calcula el percentil real de un z-score bajo distribución t.

    Si nu es None, usa distribución normal como fallback.

    Args:
        z_score: El z-score calculado (con EWMA de Fase 1)
        nu:      Grados de libertad estimados. None = usar normal.

    Returns:
        float — percentil real (0-100)
    """
    abs_z = abs(float(z_score))

    if nu is None:
        return float(scipy_stats.norm.cdf(abs_z)) * 100
    else:
        return float(scipy_stats.t.cdf(abs_z, df=nu)) * 100


def calcular_umbrales_calibrados(nu):
    """
    Calcula qué z-scores corresponden a los mismos percentiles
    que los umbrales originales asumían bajo distribución normal.

    Args:
        nu: Grados de libertad estimados

    Returns:
        dict con umbrales originales y sus equivalentes bajo distribución t
    """
    umbrales_referencia = {
        "umbral_1.5": (1.5, scipy_stats.norm.cdf(1.5)),
        "umbral_2.0": (2.0, scipy_stats.norm.cdf(2.0)),
        "umbral_2.5": (2.5, scipy_stats.norm.cdf(2.5)),
        "umbral_3.0": (3.0, scipy_stats.norm.cdf(3.0)),
    }

    resultado = {}
    for nombre, (z_normal, percentil_normal) in umbrales_referencia.items():
        z_t         = float(scipy_stats.t.ppf(percentil_normal, df=nu))
        pct_real    = float(scipy_stats.t.cdf(z_normal, df=nu)) * 100
        pct_normal  = percentil_normal * 100

        resultado[nombre] = {
            'z_original':           round(z_normal, 2),
            'percentil_bajo_normal': round(pct_normal, 2),
            'percentil_real_bajo_t': round(pct_real, 2),
            'z_equivalente_t':      round(z_t, 3),
            'sobreestimacion_pct':  round(pct_normal - pct_real, 2),
        }

    return resultado


# ============================================================
# FASE 3 — FILTRO DE RÉGIMEN: EFFICIENCY RATIO
# Los umbrales viven en config.py como RENDLOG_ER_UMBRAL_*
# ============================================================


def calcular_efficiency_ratio(df, ventana=None):
    """
    Calcula Efficiency Ratio para cada punto de la serie.

    ER = desplazamiento_neto / suma_movimientos_individuales

    Args:
        df:      DataFrame con columna 'close'
        ventana: int — número de velas para calcular ER
                       Si None, usa RENDLOG_ER_VENTANA de config.py

    Returns:
        DataFrame con columna 'efficiency_ratio' agregada
    """
    if ventana is None:
        ventana = RENDLOG_ER_VENTANA

    df = df.copy()

    er_values = np.full(len(df), np.nan)

    prices = df['close'].values

    for i in range(ventana, len(prices)):
        window = prices[i - ventana: i + 1]

        net_displacement    = abs(window[-1] - window[0])
        individual_moves    = np.sum(np.abs(np.diff(window)))

        if individual_moves > 0:
            er_values[i] = net_displacement / individual_moves
        else:
            er_values[i] = 0.0

    er_series = np.clip(er_values, 0.0, 1.0)
    df['efficiency_ratio'] = er_series

    return df


def clasificar_regimen(er):
    """
    Clasifica el régimen de mercado dado un valor de ER.

    Args:
        er: float — Efficiency Ratio actual

    Returns:
        str — "RANGO", "TENDENCIA", o "AMBIGUO"
    """
    if pd.isna(er):
        return "DESCONOCIDO"
    elif er < RENDLOG_ER_UMBRAL_RANGO:
        return "RANGO"
    elif er > RENDLOG_ER_UMBRAL_TENDENCIA:
        return "TENDENCIA"
    else:
        return "AMBIGUO"
