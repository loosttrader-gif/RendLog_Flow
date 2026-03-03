-- ============================================================
-- FUNCIONES RPC PARA VENTANA MOVIL DE 60 VELAS
-- Ejecutar en Supabase SQL Editor
-- ============================================================

-- 1. Borrar TODA la data del usuario (se llama al iniciar main.py)
CREATE OR REPLACE FUNCTION delete_user_data(api_key_param TEXT)
RETURNS BOOLEAN AS $$
DECLARE
  found_user_id UUID;
BEGIN
  SELECT id INTO found_user_id
  FROM user_profiles
  WHERE api_key = api_key_param;

  IF found_user_id IS NULL THEN
    RETURN FALSE;
  END IF;

  DELETE FROM user_data WHERE user_id = found_user_id;

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Eliminar la vela mas antigua de un timeframe especifico
CREATE OR REPLACE FUNCTION delete_oldest_candle(api_key_param TEXT, timeframe_param TEXT)
RETURNS BOOLEAN AS $$
DECLARE
  found_user_id UUID;
BEGIN
  SELECT id INTO found_user_id
  FROM user_profiles
  WHERE api_key = api_key_param;

  IF found_user_id IS NULL THEN
    RETURN FALSE;
  END IF;

  DELETE FROM user_data
  WHERE user_id = found_user_id
    AND timeframe = timeframe_param
    AND data_timestamp = (
      SELECT MIN(data_timestamp)
      FROM user_data
      WHERE user_id = found_user_id
        AND timeframe = timeframe_param
    );

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
