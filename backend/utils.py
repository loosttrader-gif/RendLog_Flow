# utils.py
from datetime import datetime
import pytz

def convertir_timezone(timestamp_utc, timezone_str="America/New_York"):
    """
    Convierte timestamp UTC a timezone específico

    Args:
        timestamp_utc: datetime object en UTC
        timezone_str: string del timezone (ej: "America/New_York")

    Returns:
        datetime object en el timezone especificado
    """
    try:
        tz = pytz.timezone(timezone_str)
        if timestamp_utc.tzinfo is None:
            # Si no tiene timezone, asumimos UTC
            timestamp_utc = pytz.utc.localize(timestamp_utc)
        return timestamp_utc.astimezone(tz)
    except Exception as e:
        print(f"⚠️ Error convirtiendo timezone: {e}")
        return timestamp_utc

def log_mensaje(mensaje, tipo="INFO"):
    """
    Log formateado con timestamp

    Args:
        mensaje: string del mensaje
        tipo: "INFO", "ERROR", "WARNING", "SUCCESS"
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    simbolos = {
        "INFO": "ℹ️",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "SUCCESS": "✅"
    }

    simbolo = simbolos.get(tipo, "•")
    print(f"[{timestamp}] {simbolo} {mensaje}")
