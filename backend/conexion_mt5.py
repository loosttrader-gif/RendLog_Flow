# conexion_mt5.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from config import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, SYMBOL, BROKER_UTC_OFFSET_HOURS
from utils import log_mensaje

def conectar_mt5():
    """
    Establece conexión con MetaTrader 5

    Returns:
        bool: True si conexión exitosa, False si falla
    """
    try:
        # Inicializar MT5
        if not mt5.initialize():
            log_mensaje(f"Error inicializando MT5: {mt5.last_error()}", "ERROR")
            return False

        # Login
        if MT5_LOGIN and MT5_PASSWORD:
            authorized = mt5.login(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER)
            if not authorized:
                log_mensaje(f"Error en login MT5: {mt5.last_error()}", "ERROR")
                mt5.shutdown()
                return False
            log_mensaje(f"Conectado a MT5 - {MT5_SERVER}", "SUCCESS")
        else:
            log_mensaje("Usando cuenta MT5 activa", "INFO")

        # Verificar símbolo
        symbol_info = mt5.symbol_info(SYMBOL)
        if symbol_info is None:
            log_mensaje(f"Símbolo {SYMBOL} no encontrado", "ERROR")
            mt5.shutdown()
            return False

        # Activar símbolo si no está visible
        if not symbol_info.visible:
            if not mt5.symbol_select(SYMBOL, True):
                log_mensaje(f"Error seleccionando símbolo {SYMBOL}", "ERROR")
                mt5.shutdown()
                return False

        return True

    except Exception as e:
        log_mensaje(f"Excepción en conexión MT5: {e}", "ERROR")
        return False

def obtener_datos_historicos(symbol, timeframe_minutes, num_bars):
    """
    Obtiene datos históricos de MT5

    Args:
        symbol: string del par (ej: "EURUSD")
        timeframe_minutes: int de minutos del timeframe
        num_bars: int número de velas a obtener

    Returns:
        DataFrame con columnas: time, open, high, low, close, tick_volume
    """
    try:
        # Mapear timeframe a constante MT5
        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30,
            60: mt5.TIMEFRAME_H1,
            240: mt5.TIMEFRAME_H4,
            1440: mt5.TIMEFRAME_D1
        }

        mt5_timeframe = timeframe_map.get(timeframe_minutes, mt5.TIMEFRAME_M30)

        # Obtener datos
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, num_bars)

        if rates is None or len(rates) == 0:
            log_mensaje(f"No se pudieron obtener datos de {symbol}", "ERROR")
            return None

        # Convertir a DataFrame
        df = pd.DataFrame(rates)
        # MT5 devuelve timestamps en hora del broker; restar offset para obtener UTC real
        df['time'] = pd.to_datetime(df['time'], unit='s') - pd.Timedelta(hours=BROKER_UTC_OFFSET_HOURS)

        return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]

    except Exception as e:
        log_mensaje(f"Error obteniendo datos históricos: {e}", "ERROR")
        return None
