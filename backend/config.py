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

# Offset UTC del servidor del broker (Tickmill = UTC+2, en verano UTC+3)
# MT5 devuelve timestamps en hora del broker; se resta este offset para convertir a UTC real
BROKER_UTC_OFFSET_HOURS = int(os.getenv("BROKER_UTC_OFFSET", "2"))

# ============================================================
# VENTANA MOVIL DE VELAS
# ============================================================
# Numero exacto de velas que se mantienen en Supabase por timeframe
VENTANA_VELAS = 60

# ============================================================
# CONFIGURACIÓN POR DEFECTO
# ============================================================
# Se sobrescribe con datos de Supabase si el usuario tiene config personalizada
DEFAULT_CONFIG = {
    "timeframe": "1M",
    "timezone": "America/New_York",
    "umbral_sigma_compra": -2.0,
    "umbral_sigma_venta": 2.0,
    "ventana_estadistica": 20,
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

# ============================================================
# RENDLOG v3.0 — PARÁMETROS ESTADÍSTICOS
# ============================================================

# EWMA: factor de decaimiento por timeframe
# Mayor λ = más persistencia (más lento para olvidar shocks recientes)
# Menor λ = más reactivo (olvida shocks rápido)
RENDLOG_LAMBDA_EWMA = {
    "1M":  0.94,   # Alta frecuencia: shocks se disipan rápido
    "5M":  0.95,
    "15M": 0.96,
    "30M": 0.97,
    "1H":  0.97,
    "4H":  0.98    # Baja frecuencia: shocks duran más
}
RENDLOG_LAMBDA_DEFAULT = 0.96  # Fallback si timeframe no está en el dict

# Efficiency Ratio: umbrales de régimen de mercado
# ER < RANGO     → mercado en rango    → RendLog tiene edge
# ER > TENDENCIA → mercado en tendencia → RendLog sin edge, señal suprimida
RENDLOG_ER_UMBRAL_RANGO     = 0.30
RENDLOG_ER_UMBRAL_TENDENCIA = 0.60
RENDLOG_ER_VENTANA          = 14   # Ventana de velas para calcular ER

# Distribución t: mínimo de retornos válidos para estimar ν
RENDLOG_NU_MIN_DATOS = 50
