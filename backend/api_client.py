# api_client.py
import requests
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_ANON_KEY, API_KEY
from utils import log_mensaje

class SupabaseClient:
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.anon_key = SUPABASE_ANON_KEY
        self.api_key = API_KEY

        # Headers para todas las llamadas REST (Supabase siempre requiere ANON_KEY)
        self.headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}",
            "Content-Type": "application/json"
        }

    def obtener_user_id(self):
        """
        Obtiene user_id desde API_KEY usando función RPC de Supabase

        Returns:
            str: UUID del usuario o None si falla
        """
        if not self.api_key:
            log_mensaje("API_KEY no configurada en .env", "ERROR")
            return None

        url = f"{self.supabase_url}/rest/v1/rpc/get_user_id_from_api_key"
        payload = {"api_key_param": self.api_key}

        try:
            response = requests.post(url, json=payload, headers=self.headers)

            if response.status_code == 200:
                user_id = response.json()
                if user_id:
                    return user_id
                else:
                    log_mensaje("API_KEY no válida o usuario inactivo", "ERROR")
                    return None
            else:
                log_mensaje(f"Error obteniendo user_id: {response.status_code}", "ERROR")
                return None

        except Exception as e:
            log_mensaje(f"Excepción obteniendo user_id: {e}", "ERROR")
            return None

    def obtener_configuracion(self):
        """
        Consulta configuración personalizada del usuario desde Supabase

        Returns:
            dict: Configuración del usuario o None si falla
        """
        user_id = self.obtener_user_id()
        if not user_id:
            return None

        url = f"{self.supabase_url}/rest/v1/user_config?user_id=eq.{user_id}"

        try:
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    log_mensaje("Configuración cargada desde Supabase", "SUCCESS")
                    return data[0]
                else:
                    log_mensaje("No se encontró configuración del usuario", "WARNING")
                    return None
            else:
                log_mensaje(f"Error obteniendo config: {response.status_code}", "ERROR")
                return None

        except Exception as e:
            log_mensaje(f"Excepción obteniendo config: {e}", "ERROR")
            return None

    def enviar_datos(self, rows):
        """
        Envía datos a Supabase via UPSERT (INSERT + ON CONFLICT UPDATE).
        Nunca borra datos existentes.

        Args:
            rows: list[dict] con cada fila conteniendo data_timestamp, rendlog, orderflow

        Returns:
            bool: True si envío exitoso, False si falla
        """
        url = f"{self.supabase_url}/rest/v1/rpc/sync_user_data"

        payload = {
            "api_key_param": self.api_key,
            "rows_param": rows
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)

            if response.status_code == 200:
                result = response.json()
                if result:
                    return True
                else:
                    log_mensaje("API_KEY no válida al enviar datos", "ERROR")
                    return False
            else:
                log_mensaje(f"Error enviando datos: {response.status_code} - {response.text}", "ERROR")
                return False

        except Exception as e:
            log_mensaje(f"Excepción enviando datos: {e}", "ERROR")
            return False
