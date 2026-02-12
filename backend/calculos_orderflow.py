# calculos_orderflow.py
import pandas as pd
import numpy as np

def calcular_delta_volumen(df):
    """
    Calcula delta de volumen (presión compradora vs vendedora)
    """
    df = df.copy()

    # Clasificar velas por dirección
    df['es_alcista'] = df['close'] > df['open']

    # Volumen alcista y bajista
    df['volumen_alcista'] = df['tick_volume'].where(df['es_alcista'], 0)
    df['volumen_bajista'] = df['tick_volume'].where(~df['es_alcista'], 0)

    # Delta = volumen alcista - volumen bajista
    # Cast a int64 para evitar overflow con uint64 de MT5
    df['delta'] = df['volumen_alcista'].astype(np.int64) - df['volumen_bajista'].astype(np.int64)

    return df

def calcular_volumen_relativo(df, ventana=20):
    """
    Calcula volumen relativo (actual vs promedio)

    Args:
        df: DataFrame con columna 'tick_volume'
        ventana: int número de velas para promedio
    """
    df = df.copy()

    # Promedio móvil de volumen
    df['promedio_volumen'] = df['tick_volume'].rolling(window=ventana).mean()

    # Ratio actual vs promedio
    df['volumen_relativo'] = df['tick_volume'] / df['promedio_volumen']

    # Rellenar NaN con 1.0
    df['volumen_relativo'] = df['volumen_relativo'].fillna(1.0)

    return df

def detectar_anomalia_volumen(df, ventana=100):
    """
    Detecta anomalías en volumen usando Z-score

    Args:
        df: DataFrame con columna 'tick_volume'
        ventana: int número de velas para cálculo
    """
    df = df.copy()

    # Media y desviación estándar del volumen
    vol_mean = df['tick_volume'].rolling(window=ventana).mean()
    vol_std = df['tick_volume'].rolling(window=ventana).std()

    # Z-score volumen
    df['z_score_volumen'] = (df['tick_volume'] - vol_mean) / vol_std

    # Anomalía si |z_score| > 2
    df['anomalia_volumen'] = df['z_score_volumen'].abs() > 2

    # Rellenar NaN
    df['z_score_volumen'] = df['z_score_volumen'].fillna(0)
    df['anomalia_volumen'] = df['anomalia_volumen'].fillna(False)

    return df
