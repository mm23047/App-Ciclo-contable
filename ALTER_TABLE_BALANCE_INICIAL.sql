-- Script SQL para agregar campos de modificación a la tabla balance_inicial
-- Ejecutar en pgAdmin Query Tool
-- Base de datos: zapateria

-- Agregar columnas fecha_modificacion y usuario_modificacion
ALTER TABLE balance_inicial 
ADD COLUMN IF NOT EXISTS fecha_modificacion DATE,
ADD COLUMN IF NOT EXISTS usuario_modificacion VARCHAR(50);

-- Comentarios para documentación
COMMENT ON COLUMN balance_inicial.fecha_modificacion IS 'Fecha de última modificación del registro';
COMMENT ON COLUMN balance_inicial.usuario_modificacion IS 'Usuario que realizó la última modificación';

-- Verificar la estructura actualizada
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'balance_inicial'
ORDER BY ordinal_position;
