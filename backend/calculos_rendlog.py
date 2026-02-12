# calculos_rendlog.py
import numpy as np
import pandas as pd

def calcular_rendimientos_log(df):
    """
    Calcula rendimientos logarítmicos

    Formula: log(Close_t / Close_t-1)
    """
    df = df.copy()
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    return df

def calcular_bandas_sigma(df, ventana=100):
    """
    Calcula media móvil y bandas sigma

    Args:
        df: DataFrame con columna 'log_return'
        ventana: int número de velas para cálculo

    Returns:
        DataFrame con columnas de bandas agregadas
    """
    df = df.copy()

    # Media móvil
    df['media'] = df['log_return'].rolling(window=ventana).mean()

    # Desviación estándar móvil
    df['std'] = df['log_return'].rolling(window=ventana).std()

    # Bandas ±2σ
    df['banda_2sigma_superior'] = df['media'] + 2 * df['std']
    df['banda_2sigma_inferior'] = df['media'] - 2 * df['std']

    # Bandas ±3σ
    df['banda_3sigma_superior'] = df['media'] + 3 * df['std']
    df['banda_3sigma_inferior'] = df['media'] - 3 * df['std']

    return df

def detectar_anomalias(df, umbral_compra=-2.0, umbral_venta=2.0):
    """
    Detecta anomalías basadas en Z-score

    Args:
        df: DataFrame con rendimientos y bandas
        umbral_compra: float (ej: -2.0 para -2σ)
        umbral_venta: float (ej: 2.0 para +2σ)

    Returns:
        dict con información de la señal
    """
    # Última vela
    ultimo_rendimiento = df['log_return'].iloc[-1]
    ultimo_sigma = df['std'].iloc[-1]
    ultima_media = df['media'].iloc[-1]

    # Calcular Z-score
    if ultimo_sigma > 0:
        z_score = (ultimo_rendimiento - ultima_media) / ultimo_sigma
    else:
        z_score = 0

    # Detectar señal
    señal = None
    color = None
    mensaje = "Sin anomalías detectadas"

    if z_score < umbral_compra:
        señal = "COMPRA"
        color = "green"
        mensaje = f"Rendimiento por debajo de {umbral_compra}σ. Buscar posible corrección alcista"
    elif z_score > umbral_venta:
        señal = "VENTA"
        color = "red"
        mensaje = f"Rendimiento por encima de {umbral_venta}σ. Buscar posible corrección bajista"

    return {
        'señal': señal,
        'z_score': float(z_score),
        'color': color,
        'mensaje': mensaje,
        'timestamp': df['time'].iloc[-1],
        'rendimiento': float(ultimo_rendimiento)
    }
