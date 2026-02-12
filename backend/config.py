# config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================
# SUPABASE (Servidor Central)
# ============================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
API_KEY = os.getenv("API_KEY")  # Usuario lo configura después de registrarse

# ============================================================
# MT5 (Broker Local)
# ============================================================
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0") or "0")
MT5_PASSWORD = os.getenv("MT5_PASSWORD") or ""
MT5_SERVER = os.getenv("MT5_SERVER", "Tickmill-Demo")
SYMBOL = "EURUSD"

# ============================================================
# CONFIGURACIÓN POR DEFECTO
# ============================================================
# Se sobrescribe con datos de Supabase si el usuario tiene config personalizada
DEFAULT_CONFIG = {
    "timeframe": "1M",
    "timezone": "America/New_York",
    "umbral_sigma_compra": -2.0,
    "umbral_sigma_venta": 2.0,
    "ventana_estadistica": 100,
    "alertas_activas": False
}

# ============================================================
# TIMEFRAMES ACTIVOS (se procesan todos en cada ciclo)
# ============================================================
TIMEFRAMES_ACTIVOS = ["1M", "5M", "15M", "30M", "1H", "4H"]

# ============================================================
# MAPEO DE TIMEFRAMES
# ============================================================
TIMEFRAME_MAP = {
    "1M": 1,    # mt5.TIMEFRAME_M1
    "5M": 5,    # mt5.TIMEFRAME_M5
    "15M": 15,  # mt5.TIMEFRAME_M15
    "30M": 30,  # mt5.TIMEFRAME_M30
    "1H": 60,   # mt5.TIMEFRAME_H1
    "4H": 240   # mt5.TIMEFRAME_H4
}
