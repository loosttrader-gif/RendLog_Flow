-- ============================================================
-- RENDLOG FLOW v4.1 — MIGRACIONES SUPABASE
-- Ejecutar en Supabase SQL Editor con el backend DETENIDO
-- ============================================================

-- ============================================================
-- SECCIÓN 1: TABLA user_data — agregar columna symbol
-- ============================================================

-- 1a. Agregar columna symbol con default EURUSD (non-destructivo)
ALTER TABLE user_data
  ADD COLUMN IF NOT EXISTS symbol TEXT NOT NULL DEFAULT 'EURUSD';

-- 1b. Reemplazar el unique constraint para incluir symbol
-- (ejecutar solo si existe el constraint original; el nombre puede variar)
DO $$
BEGIN
  -- Intentar eliminar constraint antiguo (sin symbol)
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'user_data_user_id_timeframe_data_timestamp_key'
  ) THEN
    ALTER TABLE user_data
      DROP CONSTRAINT user_data_user_id_timeframe_data_timestamp_key;
  END IF;
END $$;

-- 1c. Agregar nuevo unique constraint con symbol
ALTER TABLE user_data
  ADD CONSTRAINT IF NOT EXISTS user_data_user_id_symbol_timeframe_timestamp_key
  UNIQUE (user_id, symbol, timeframe, data_timestamp);

-- 1d. Índice para queries rápidas por símbolo
CREATE INDEX IF NOT EXISTS idx_user_data_symbol
  ON user_data(user_id, symbol, timeframe, data_timestamp DESC);


-- ============================================================
-- SECCIÓN 2: delete_user_data (sin cambios, re-publicado)
-- ============================================================

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


-- ============================================================
-- SECCIÓN 3: delete_oldest_candle — ahora filtra por symbol
-- symbol_param DEFAULT 'EURUSD' preserva backward compatibility
-- ============================================================

CREATE OR REPLACE FUNCTION delete_oldest_candle(
  api_key_param  TEXT,
  timeframe_param TEXT,
  symbol_param   TEXT DEFAULT 'EURUSD'
)
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
  WHERE user_id   = found_user_id
    AND timeframe = timeframe_param
    AND symbol    = symbol_param
    AND data_timestamp = (
      SELECT MIN(data_timestamp)
      FROM user_data
      WHERE user_id   = found_user_id
        AND timeframe = timeframe_param
        AND symbol    = symbol_param
    );

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ============================================================
-- SECCIÓN 4: sync_user_data — upsert actualizado con symbol
-- ============================================================
-- Reemplaza el RPC existente para usar el nuevo unique constraint
-- (user_id, symbol, timeframe, data_timestamp)
--
-- NOTA: Si el RPC sync_user_data existente usa ON CONFLICT con
--       el constraint anterior, debe actualizarse a:
--         ON CONFLICT (user_id, symbol, timeframe, data_timestamp)
--
-- Ejemplo de estructura (ajustar al RPC real del proyecto):
--
-- CREATE OR REPLACE FUNCTION sync_user_data(
--   api_key_param TEXT,
--   rows_param    JSONB
-- )
-- RETURNS BOOLEAN AS $$
-- DECLARE
--   found_user_id UUID;
--   row_data      JSONB;
-- BEGIN
--   SELECT id INTO found_user_id
--   FROM user_profiles
--   WHERE api_key = api_key_param;
--
--   IF found_user_id IS NULL THEN
--     RETURN FALSE;
--   END IF;
--
--   FOR row_data IN SELECT * FROM jsonb_array_elements(rows_param)
--   LOOP
--     INSERT INTO user_data (
--       user_id, symbol, timeframe, data_timestamp, rendlog, orderflow
--     ) VALUES (
--       found_user_id,
--       COALESCE(row_data->>'symbol', 'EURUSD'),
--       row_data->>'timeframe',
--       (row_data->>'data_timestamp')::TIMESTAMPTZ,
--       row_data->'rendlog',
--       row_data->'orderflow'
--     )
--     ON CONFLICT (user_id, symbol, timeframe, data_timestamp)
--     DO UPDATE SET
--       rendlog   = EXCLUDED.rendlog,
--       orderflow = EXCLUDED.orderflow;
--   END LOOP;
--
--   RETURN TRUE;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;
