-- Inicialización completa de la BD con todas las tablas y relaciones
-- Este script recrea el esquema completo y es útil para Docker volume cleanup

-- Tablas: empresas (independiente)
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    razon_social VARCHAR(150),
    correo VARCHAR(255),
    telefono VARCHAR(30),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tablas: ciudades (catálogo con empresa_id nullable)
CREATE TABLE IF NOT EXISTS ciudades (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    nombre VARCHAR(120) NOT NULL,
    departamento VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_ciudad_empresa_nombre UNIQUE(empresa_id, nombre)
);

-- Tabla: sucursales (FK a empresas y ciudades)
CREATE TABLE IF NOT EXISTS sucursales (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id),
    nombre VARCHAR(120) NOT NULL,
    ciudad_id INTEGER NOT NULL REFERENCES ciudades(id),
    direccion VARCHAR(255) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_sucursal_empresa_id UNIQUE(empresa_id, id)
);

-- Tabla: proveedores (FK a empresas)
CREATE TABLE IF NOT EXISTS proveedores (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id),
    razon_social VARCHAR(150) NOT NULL,
    nombre_contacto VARCHAR(120) NOT NULL,
    correo VARCHAR(255) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_proveedor_empresa_razon_social UNIQUE(empresa_id, razon_social)
);

-- Tabla: usuarios (FK a empresas, sucursales, proveedores)
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    nombre VARCHAR(120) NOT NULL,
    correo VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sucursal_id INTEGER REFERENCES sucursales(id),
    proveedor_id INTEGER UNIQUE REFERENCES proveedores(id),
    telefono VARCHAR(30),
    CONSTRAINT uq_usuario_empresa_correo UNIQUE(empresa_id, correo)
);

-- Tabla: planes (catálogo global, sin empresa_id)
CREATE TABLE IF NOT EXISTS planes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    precio NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    duracion_dias INTEGER NOT NULL DEFAULT 30,
    limite_sucursales INTEGER NOT NULL DEFAULT 1,
    limite_usuarios INTEGER NOT NULL DEFAULT 5,
    permite_prueba_gratuita BOOLEAN NOT NULL DEFAULT FALSE,
    duracion_prueba_dias INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: suscripciones (FK a empresas y planes)
CREATE TABLE IF NOT EXISTS suscripciones (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id),
    plan_id INTEGER NOT NULL REFERENCES planes(id),
    fecha_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_vencimiento TIMESTAMP WITH TIME ZONE NOT NULL,
    en_prueba BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_fin_prueba TIMESTAMP WITH TIME ZONE,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_usuarios_empresa_id ON usuarios(empresa_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_correo ON usuarios(correo);
CREATE INDEX IF NOT EXISTS idx_sucursales_empresa_id ON sucursales(empresa_id);
CREATE INDEX IF NOT EXISTS idx_proveedores_empresa_id ON proveedores(empresa_id);
CREATE INDEX IF NOT EXISTS idx_suscripciones_empresa_id ON suscripciones(empresa_id);

-- Datos de inicialización
INSERT INTO empresas (nombre, slug, razon_social, correo, telefono, is_active)
VALUES ('FashionStore', 'fashionstore', 'FashionStore SAS', 'info@fashionstore.com', '+573001234567', TRUE)
ON CONFLICT (slug) DO NOTHING;

-- NOTA: Generar hash bcrypt con: python3 -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt(12)).decode())"
-- Para password "admin123" (cambiar antes de producción)
INSERT INTO usuarios (empresa_id, nombre, correo, password_hash, rol, is_active, telefono)
VALUES (
    (SELECT id FROM empresas WHERE slug = 'fashionstore'),
    'Administrador',
    'admin@fashionstore.com',
    '$2b$12$xmvT9F/zKHL0DtSzTdGbgOCJAiS9dEBk/wsX6wtIsIUoC/EmeyJSO',
    'ADMINISTRADOR',
    TRUE,
    '+573001234567'
)
ON CONFLICT (correo) DO NOTHING;

-- Plan de prueba (gratuito)
INSERT INTO planes (nombre, slug, descripcion, precio, duracion_dias, limite_sucursales, limite_usuarios, permite_prueba_gratuita, duracion_prueba_dias, is_active)
VALUES ('Plan Gratuito', 'plan-gratuito', 'Plan de prueba con características limitadas', 0.00, 30, 1, 5, TRUE, 30, TRUE)
ON CONFLICT (slug) DO NOTHING;

-- Suscripción de la empresa al plan gratuito (vigencia: hoy + 30 días)
INSERT INTO suscripciones (empresa_id, plan_id, fecha_inicio, fecha_vencimiento, en_prueba, activa)
SELECT
    e.id,
    p.id,
    NOW(),
    NOW() + INTERVAL '30 days',
    TRUE,
    TRUE
FROM empresas e
CROSS JOIN planes p
WHERE e.slug = 'fashionstore' AND p.slug = 'plan-gratuito'
AND NOT EXISTS (
    SELECT 1 FROM suscripciones WHERE empresa_id = e.id AND plan_id = p.id
);
