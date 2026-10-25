--
-- PostgreSQL database dump
--

\restrict PduCDWNkezDysSeCsWkpfjW882vzKsY7Ruc8uj3f58MUTzbVzRSgt8gzZh5khAR

-- Dumped from database version 18.6 (fd34222)
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: neon_auth; Type: SCHEMA; Schema: -; Owner: neon_auth
--

CREATE SCHEMA neon_auth;


ALTER SCHEMA neon_auth OWNER TO neon_auth;

--
-- Name: estado_pago; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.estado_pago AS ENUM (
    'PENDIENTE',
    'PAGADO',
    'CANCELADO',
    'FALLIDO'
);


ALTER TYPE public.estado_pago OWNER TO neondb_owner;

--
-- Name: estado_producto_proveedor; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.estado_producto_proveedor AS ENUM (
    'PENDIENTE',
    'APROBADO',
    'RECHAZADO'
);


ALTER TYPE public.estado_producto_proveedor OWNER TO neondb_owner;

--
-- Name: estado_reembolso; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.estado_reembolso AS ENUM (
    'REGISTRADO',
    'COMPLETADO'
);


ALTER TYPE public.estado_reembolso OWNER TO neondb_owner;

--
-- Name: estado_reserva; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.estado_reserva AS ENUM (
    'PENDIENTE',
    'CANCELADA',
    'ATENDIDA',
    'PREPARADA',
    'EN_ATENCION',
    'LISTA_PARA_CAJA',
    'VENCIDA'
);


ALTER TYPE public.estado_reserva OWNER TO neondb_owner;

--
-- Name: estado_venta; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.estado_venta AS ENUM (
    'PENDIENTE_PAGO',
    'PAGADA'
);


ALTER TYPE public.estado_venta OWNER TO neondb_owner;

--
-- Name: motivo_devolucion; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.motivo_devolucion AS ENUM (
    'TALLA',
    'DEFECTO',
    'PRODUCTO_INCORRECTO',
    'OTRO'
);


ALTER TYPE public.motivo_devolucion OWNER TO neondb_owner;

--
-- Name: origen_venta; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.origen_venta AS ENUM (
    'DIRECTA',
    'RESERVA'
);


ALTER TYPE public.origen_venta OWNER TO neondb_owner;

--
-- Name: proveedor_pago; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.proveedor_pago AS ENUM (
    'STRIPE',
    'EFECTIVO',
    'TARJETA',
    'QR'
);


ALTER TYPE public.proveedor_pago OWNER TO neondb_owner;

--
-- Name: rol_usuario; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.rol_usuario AS ENUM (
    'SUPERADMIN',
    'ADMINISTRADOR',
    'ENCARGADO_SUCURSAL',
    'CAJERO',
    'CLIENTE',
    'PROVEEDOR'
);


ALTER TYPE public.rol_usuario OWNER TO neondb_owner;

--
-- Name: tipo_movimiento_inventario; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.tipo_movimiento_inventario AS ENUM (
    'AJUSTE_POSITIVO',
    'AJUSTE_NEGATIVO'
);


ALTER TYPE public.tipo_movimiento_inventario OWNER TO neondb_owner;

--
-- Name: tipo_operacion_devolucion; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.tipo_operacion_devolucion AS ENUM (
    'DEVOLUCION',
    'CAMBIO'
);


ALTER TYPE public.tipo_operacion_devolucion OWNER TO neondb_owner;

--
-- Name: tipo_tarjeta; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.tipo_tarjeta AS ENUM (
    'DEBITO',
    'CREDITO'
);


ALTER TYPE public.tipo_tarjeta OWNER TO neondb_owner;

--
-- Name: tipo_venta; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.tipo_venta AS ENUM (
    'DIGITAL',
    'PRESENCIAL'
);


ALTER TYPE public.tipo_venta OWNER TO neondb_owner;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.account (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "accountId" text NOT NULL,
    "providerId" text NOT NULL,
    "userId" uuid NOT NULL,
    "accessToken" text,
    "refreshToken" text,
    "idToken" text,
    "accessTokenExpiresAt" timestamp with time zone,
    "refreshTokenExpiresAt" timestamp with time zone,
    scope text,
    password text,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone NOT NULL
);


ALTER TABLE neon_auth.account OWNER TO neon_auth;

--
-- Name: invitation; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.invitation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "organizationId" uuid NOT NULL,
    email text NOT NULL,
    role text,
    status text NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "inviterId" uuid NOT NULL
);


ALTER TABLE neon_auth.invitation OWNER TO neon_auth;

--
-- Name: jwks; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.jwks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "publicKey" text NOT NULL,
    "privateKey" text NOT NULL,
    "createdAt" timestamp with time zone NOT NULL,
    "expiresAt" timestamp with time zone
);


ALTER TABLE neon_auth.jwks OWNER TO neon_auth;

--
-- Name: member; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.member (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "organizationId" uuid NOT NULL,
    "userId" uuid NOT NULL,
    role text NOT NULL,
    "createdAt" timestamp with time zone NOT NULL
);


ALTER TABLE neon_auth.member OWNER TO neon_auth;

--
-- Name: organization; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.organization (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    logo text,
    "createdAt" timestamp with time zone NOT NULL,
    metadata text
);


ALTER TABLE neon_auth.organization OWNER TO neon_auth;

--
-- Name: project_config; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.project_config (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    endpoint_id text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    trusted_origins jsonb NOT NULL,
    social_providers jsonb NOT NULL,
    email_provider jsonb,
    email_and_password jsonb,
    allow_localhost boolean NOT NULL,
    plugin_configs jsonb,
    webhook_config jsonb
);


ALTER TABLE neon_auth.project_config OWNER TO neon_auth;

--
-- Name: session; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.session (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    token text NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone NOT NULL,
    "ipAddress" text,
    "userAgent" text,
    "userId" uuid NOT NULL,
    "impersonatedBy" text,
    "activeOrganizationId" text
);


ALTER TABLE neon_auth.session OWNER TO neon_auth;

--
-- Name: user; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth."user" (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    email text NOT NULL,
    "emailVerified" boolean NOT NULL,
    image text,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    role text,
    banned boolean,
    "banReason" text,
    "banExpires" timestamp with time zone
);


ALTER TABLE neon_auth."user" OWNER TO neon_auth;

--
-- Name: verification; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.verification (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    identifier text NOT NULL,
    value text NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE neon_auth.verification OWNER TO neon_auth;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO neondb_owner;

--
-- Name: carrito_items; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.carrito_items (
    id integer NOT NULL,
    carrito_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    fecha_agregado timestamp with time zone DEFAULT now() NOT NULL,
    seleccionado boolean DEFAULT true NOT NULL
);


ALTER TABLE public.carrito_items OWNER TO neondb_owner;

--
-- Name: carrito_items_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.carrito_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.carrito_items_id_seq OWNER TO neondb_owner;

--
-- Name: carrito_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.carrito_items_id_seq OWNED BY public.carrito_items.id;


--
-- Name: carritos; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.carritos (
    id integer NOT NULL,
    cliente_id integer NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    fecha_actualizacion timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.carritos OWNER TO neondb_owner;

--
-- Name: carritos_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.carritos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.carritos_id_seq OWNER TO neondb_owner;

--
-- Name: carritos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.carritos_id_seq OWNED BY public.carritos.id;


--
-- Name: categorias; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.categorias (
    id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    is_active boolean NOT NULL,
    imagen_url character varying(500),
    empresa_id integer
);


ALTER TABLE public.categorias OWNER TO neondb_owner;

--
-- Name: categorias_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorias_id_seq OWNER TO neondb_owner;

--
-- Name: categorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;


--
-- Name: ciudades; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.ciudades (
    id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    is_active boolean NOT NULL,
    departamento character varying(120) NOT NULL,
    empresa_id integer
);


ALTER TABLE public.ciudades OWNER TO neondb_owner;

--
-- Name: ciudades_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.ciudades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ciudades_id_seq OWNER TO neondb_owner;

--
-- Name: ciudades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.ciudades_id_seq OWNED BY public.ciudades.id;


--
-- Name: colecciones; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.colecciones (
    id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    temporada_id integer NOT NULL,
    descripcion character varying(255),
    is_active boolean NOT NULL,
    es_destacada_inicio boolean DEFAULT false NOT NULL,
    imagen_destacada_url character varying(500),
    empresa_id integer
);


ALTER TABLE public.colecciones OWNER TO neondb_owner;

--
-- Name: colecciones_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.colecciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.colecciones_id_seq OWNER TO neondb_owner;

--
-- Name: colecciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.colecciones_id_seq OWNED BY public.colecciones.id;


--
-- Name: colores; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.colores (
    id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    is_active boolean NOT NULL,
    empresa_id integer
);


ALTER TABLE public.colores OWNER TO neondb_owner;

--
-- Name: colores_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.colores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.colores_id_seq OWNER TO neondb_owner;

--
-- Name: colores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.colores_id_seq OWNED BY public.colores.id;


--
-- Name: detalles_recepcion_mercaderia; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.detalles_recepcion_mercaderia (
    id integer NOT NULL,
    recepcion_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    cantidad_recibida integer NOT NULL,
    CONSTRAINT ck_detalle_recepcion_cantidad_positiva CHECK ((cantidad_recibida > 0))
);


ALTER TABLE public.detalles_recepcion_mercaderia OWNER TO neondb_owner;

--
-- Name: detalles_recepcion_mercaderia_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.detalles_recepcion_mercaderia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detalles_recepcion_mercaderia_id_seq OWNER TO neondb_owner;

--
-- Name: detalles_recepcion_mercaderia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.detalles_recepcion_mercaderia_id_seq OWNED BY public.detalles_recepcion_mercaderia.id;


--
-- Name: devoluciones_cambios; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.devoluciones_cambios (
    id integer NOT NULL,
    venta_id integer NOT NULL,
    venta_detalle_id integer NOT NULL,
    tipo public.tipo_operacion_devolucion NOT NULL,
    cantidad integer NOT NULL,
    variante_original_id integer NOT NULL,
    variante_nueva_id integer,
    motivo public.motivo_devolucion,
    observacion character varying(300),
    monto_reembolso numeric(10,2),
    metodo_reembolso public.proveedor_pago,
    estado_reembolso public.estado_reembolso,
    stripe_refund_id character varying(255),
    cajero_id integer NOT NULL,
    sucursal_id integer NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_devolucion_cambio_cantidad_positiva CHECK ((cantidad > 0))
);


ALTER TABLE public.devoluciones_cambios OWNER TO neondb_owner;

--
-- Name: devoluciones_cambios_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.devoluciones_cambios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.devoluciones_cambios_id_seq OWNER TO neondb_owner;

--
-- Name: devoluciones_cambios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.devoluciones_cambios_id_seq OWNED BY public.devoluciones_cambios.id;


--
-- Name: empresas; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.empresas (
    id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    slug character varying(100) NOT NULL,
    razon_social character varying(200) NOT NULL,
    correo character varying(255) NOT NULL,
    telefono character varying(30) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.empresas OWNER TO neondb_owner;

--
-- Name: empresas_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.empresas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.empresas_id_seq OWNER TO neondb_owner;

--
-- Name: empresas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.empresas_id_seq OWNED BY public.empresas.id;


--
-- Name: movimientos_inventario; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.movimientos_inventario (
    id integer NOT NULL,
    sucursal_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo public.tipo_movimiento_inventario NOT NULL,
    cantidad integer NOT NULL,
    motivo character varying(300) NOT NULL,
    stock_anterior integer NOT NULL,
    stock_resultante integer NOT NULL,
    fecha_hora timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_movimiento_inventario_cantidad_positiva CHECK ((cantidad > 0)),
    CONSTRAINT ck_movimiento_inventario_stock_no_negativo CHECK (((stock_anterior >= 0) AND (stock_resultante >= 0)))
);


ALTER TABLE public.movimientos_inventario OWNER TO neondb_owner;

--
-- Name: movimientos_inventario_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.movimientos_inventario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimientos_inventario_id_seq OWNER TO neondb_owner;

--
-- Name: movimientos_inventario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.movimientos_inventario_id_seq OWNED BY public.movimientos_inventario.id;


--
-- Name: pagos; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pagos (
    id integer NOT NULL,
    venta_id integer NOT NULL,
    proveedor public.proveedor_pago NOT NULL,
    stripe_checkout_session_id character varying(255),
    stripe_payment_intent_id character varying(255),
    monto numeric(10,2) NOT NULL,
    estado public.estado_pago NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    fecha_confirmacion timestamp with time zone,
    cajero_id integer,
    monto_recibido numeric(10,2),
    cambio numeric(10,2),
    tipo_tarjeta public.tipo_tarjeta,
    referencia character varying(120)
);


ALTER TABLE public.pagos OWNER TO neondb_owner;

--
-- Name: pagos_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pagos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pagos_id_seq OWNER TO neondb_owner;

--
-- Name: pagos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pagos_id_seq OWNED BY public.pagos.id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.password_reset_tokens (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    token_hash character varying(64) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.password_reset_tokens OWNER TO neondb_owner;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.password_reset_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.password_reset_tokens_id_seq OWNER TO neondb_owner;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;


--
-- Name: producto_colores; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.producto_colores (
    producto_id integer NOT NULL,
    color_id integer NOT NULL
);


ALTER TABLE public.producto_colores OWNER TO neondb_owner;

--
-- Name: producto_imagenes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.producto_imagenes (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    url character varying(500) NOT NULL,
    orden integer NOT NULL
);


ALTER TABLE public.producto_imagenes OWNER TO neondb_owner;

--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.producto_imagenes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.producto_imagenes_id_seq OWNER TO neondb_owner;

--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.producto_imagenes_id_seq OWNED BY public.producto_imagenes.id;


--
-- Name: producto_tallas; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.producto_tallas (
    producto_id integer NOT NULL,
    talla_id integer NOT NULL
);


ALTER TABLE public.producto_tallas OWNER TO neondb_owner;

--
-- Name: producto_variantes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.producto_variantes (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    talla_id integer NOT NULL,
    color_id integer NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.producto_variantes OWNER TO neondb_owner;

--
-- Name: producto_variantes_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.producto_variantes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.producto_variantes_id_seq OWNER TO neondb_owner;

--
-- Name: producto_variantes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.producto_variantes_id_seq OWNED BY public.producto_variantes.id;


--
-- Name: productos; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.productos (
    id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    descripcion character varying(500),
    proveedor_id integer CONSTRAINT productos_proveedor_id_not_null1 NOT NULL,
    producto_proveedor_id integer,
    categoria_id integer NOT NULL,
    temporada_id integer NOT NULL,
    coleccion_id integer NOT NULL,
    precio_venta numeric(10,2) NOT NULL,
    is_active boolean NOT NULL,
    imagen_principal_url character varying(500),
    empresa_id integer
);


ALTER TABLE public.productos OWNER TO neondb_owner;

--
-- Name: productos_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.productos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.productos_id_seq OWNER TO neondb_owner;

--
-- Name: productos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.productos_id_seq OWNED BY public.productos.id;


--
-- Name: productos_proveedor; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.productos_proveedor (
    id integer NOT NULL,
    proveedor_id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    descripcion character varying(500),
    disponibilidad boolean NOT NULL,
    is_active boolean NOT NULL,
    imagen_url character varying(500),
    estado public.estado_producto_proveedor DEFAULT 'PENDIENTE'::public.estado_producto_proveedor NOT NULL
);


ALTER TABLE public.productos_proveedor OWNER TO neondb_owner;

--
-- Name: productos_proveedor_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.productos_proveedor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.productos_proveedor_id_seq OWNER TO neondb_owner;

--
-- Name: productos_proveedor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.productos_proveedor_id_seq OWNED BY public.productos_proveedor.id;


--
-- Name: promocion_productos; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.promocion_productos (
    promocion_id integer NOT NULL,
    producto_id integer NOT NULL
);


ALTER TABLE public.promocion_productos OWNER TO neondb_owner;

--
-- Name: promociones; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.promociones (
    id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    porcentaje_descuento numeric(5,2) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    activa boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_promocion_fechas_orden CHECK ((fecha_fin >= fecha_inicio)),
    CONSTRAINT ck_promocion_porcentaje_rango CHECK (((porcentaje_descuento > (0)::numeric) AND (porcentaje_descuento < (100)::numeric)))
);


ALTER TABLE public.promociones OWNER TO neondb_owner;

--
-- Name: promociones_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.promociones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.promociones_id_seq OWNER TO neondb_owner;

--
-- Name: promociones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.promociones_id_seq OWNED BY public.promociones.id;


--
-- Name: proveedores; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.proveedores (
    id integer NOT NULL,
    razon_social character varying(150) NOT NULL,
    nombre_contacto character varying(120) NOT NULL,
    correo character varying(255) NOT NULL,
    telefono character varying(30) NOT NULL,
    is_active boolean NOT NULL,
    empresa_id integer
);


ALTER TABLE public.proveedores OWNER TO neondb_owner;

--
-- Name: proveedores_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.proveedores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.proveedores_id_seq OWNER TO neondb_owner;

--
-- Name: proveedores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.proveedores_id_seq OWNED BY public.proveedores.id;


--
-- Name: recepciones_mercaderia; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.recepciones_mercaderia (
    id integer NOT NULL,
    proveedor_id integer NOT NULL,
    sucursal_id integer NOT NULL,
    usuario_id integer NOT NULL,
    fecha_hora timestamp with time zone DEFAULT now() NOT NULL,
    observacion character varying(500)
);


ALTER TABLE public.recepciones_mercaderia OWNER TO neondb_owner;

--
-- Name: recepciones_mercaderia_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.recepciones_mercaderia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.recepciones_mercaderia_id_seq OWNER TO neondb_owner;

--
-- Name: recepciones_mercaderia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.recepciones_mercaderia_id_seq OWNED BY public.recepciones_mercaderia.id;


--
-- Name: reserva_detalles; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.reserva_detalles (
    id integer CONSTRAINT reservas_id_not_null NOT NULL,
    producto_variante_id integer CONSTRAINT reservas_producto_variante_id_not_null NOT NULL,
    cantidad integer CONSTRAINT reservas_cantidad_not_null NOT NULL,
    estado public.estado_reserva CONSTRAINT reservas_estado_not_null NOT NULL,
    reserva_id integer NOT NULL,
    CONSTRAINT ck_reserva_detalle_cantidad_positiva CHECK ((cantidad > 0))
);


ALTER TABLE public.reserva_detalles OWNER TO neondb_owner;

--
-- Name: reserva_detalles_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.reserva_detalles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reserva_detalles_id_seq OWNER TO neondb_owner;

--
-- Name: reserva_detalles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.reserva_detalles_id_seq OWNED BY public.reserva_detalles.id;


--
-- Name: reservas; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.reservas (
    id integer CONSTRAINT reservas_id_not_null1 NOT NULL,
    codigo_reserva character varying(20) NOT NULL,
    cliente_id integer CONSTRAINT reservas_cliente_id_not_null1 NOT NULL,
    sucursal_id integer CONSTRAINT reservas_sucursal_id_not_null1 NOT NULL,
    fecha_reserva date CONSTRAINT reservas_fecha_reserva_not_null1 NOT NULL,
    hora_inicio time without time zone CONSTRAINT reservas_hora_inicio_not_null1 NOT NULL,
    estado_general public.estado_reserva NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() CONSTRAINT reservas_fecha_creacion_not_null1 NOT NULL
);


ALTER TABLE public.reservas OWNER TO neondb_owner;

--
-- Name: reservas_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.reservas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reservas_id_seq OWNER TO neondb_owner;

--
-- Name: reservas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.reservas_id_seq OWNED BY public.reservas.id;


--
-- Name: stock_sucursal; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.stock_sucursal (
    id integer NOT NULL,
    sucursal_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    cantidad integer DEFAULT 0 NOT NULL,
    stock_reservado integer DEFAULT 0 NOT NULL,
    CONSTRAINT ck_stock_sucursal_cantidad_no_negativa CHECK ((cantidad >= 0)),
    CONSTRAINT ck_stock_sucursal_reservado_no_negativo CHECK ((stock_reservado >= 0))
);


ALTER TABLE public.stock_sucursal OWNER TO neondb_owner;

--
-- Name: stock_sucursal_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.stock_sucursal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.stock_sucursal_id_seq OWNER TO neondb_owner;

--
-- Name: stock_sucursal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.stock_sucursal_id_seq OWNED BY public.stock_sucursal.id;


--
-- Name: sucursales; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sucursales (
    id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    ciudad_id integer NOT NULL,
    direccion character varying(255) NOT NULL,
    telefono character varying(30) NOT NULL,
    is_active boolean NOT NULL,
    empresa_id integer
);


ALTER TABLE public.sucursales OWNER TO neondb_owner;

--
-- Name: sucursales_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sucursales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sucursales_id_seq OWNER TO neondb_owner;

--
-- Name: sucursales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sucursales_id_seq OWNED BY public.sucursales.id;


--
-- Name: tallas; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.tallas (
    id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    is_active boolean NOT NULL,
    empresa_id integer
);


ALTER TABLE public.tallas OWNER TO neondb_owner;

--
-- Name: tallas_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.tallas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tallas_id_seq OWNER TO neondb_owner;

--
-- Name: tallas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.tallas_id_seq OWNED BY public.tallas.id;


--
-- Name: temporadas; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.temporadas (
    id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    is_active boolean NOT NULL,
    empresa_id integer
);


ALTER TABLE public.temporadas OWNER TO neondb_owner;

--
-- Name: temporadas_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.temporadas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.temporadas_id_seq OWNER TO neondb_owner;

--
-- Name: temporadas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.temporadas_id_seq OWNED BY public.temporadas.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    correo character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    rol public.rol_usuario NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    sucursal_id integer,
    proveedor_id integer,
    telefono character varying(30),
    empresa_id integer
);


ALTER TABLE public.usuarios OWNER TO neondb_owner;

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO neondb_owner;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: venta_detalles; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.venta_detalles (
    id integer NOT NULL,
    venta_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric(10,2) NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    carrito_item_id integer,
    CONSTRAINT ck_venta_detalle_cantidad_positiva CHECK ((cantidad > 0))
);


ALTER TABLE public.venta_detalles OWNER TO neondb_owner;

--
-- Name: venta_detalles_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.venta_detalles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.venta_detalles_id_seq OWNER TO neondb_owner;

--
-- Name: venta_detalles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.venta_detalles_id_seq OWNED BY public.venta_detalles.id;


--
-- Name: ventas; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.ventas (
    id integer NOT NULL,
    codigo_venta character varying(20) NOT NULL,
    cliente_id integer,
    sucursal_id integer NOT NULL,
    tipo public.tipo_venta NOT NULL,
    estado public.estado_venta NOT NULL,
    total numeric(10,2) NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    cajero_id integer,
    origen public.origen_venta,
    reserva_id integer
);


ALTER TABLE public.ventas OWNER TO neondb_owner;

--
-- Name: ventas_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.ventas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ventas_id_seq OWNER TO neondb_owner;

--
-- Name: ventas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.ventas_id_seq OWNED BY public.ventas.id;


--
-- Name: carrito_items id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.carrito_items ALTER COLUMN id SET DEFAULT nextval('public.carrito_items_id_seq'::regclass);


--
-- Name: carritos id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.carritos ALTER COLUMN id SET DEFAULT nextval('public.carritos_id_seq'::regclass);


--
-- Name: categorias id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);


--
-- Name: ciudades id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ciudades ALTER COLUMN id SET DEFAULT nextval('public.ciudades_id_seq'::regclass);


--
-- Name: colecciones id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.colecciones ALTER COLUMN id SET DEFAULT nextval('public.colecciones_id_seq'::regclass);


--
-- Name: colores id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.colores ALTER COLUMN id SET DEFAULT nextval('public.colores_id_seq'::regclass);


--
-- Name: detalles_recepcion_mercaderia id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.detalles_recepcion_mercaderia ALTER COLUMN id SET DEFAULT nextval('public.detalles_recepcion_mercaderia_id_seq'::regclass);


--
-- Name: devoluciones_cambios id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.devoluciones_cambios ALTER COLUMN id SET DEFAULT nextval('public.devoluciones_cambios_id_seq'::regclass);


--
-- Name: empresas id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.empresas ALTER COLUMN id SET DEFAULT nextval('public.empresas_id_seq'::regclass);


--
-- Name: movimientos_inventario id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.movimientos_inventario ALTER COLUMN id SET DEFAULT nextval('public.movimientos_inventario_id_seq'::regclass);


--
-- Name: pagos id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pagos ALTER COLUMN id SET DEFAULT nextval('public.pagos_id_seq'::regclass);


--
-- Name: password_reset_tokens id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq'::regclass);


--
-- Name: producto_imagenes id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_imagenes ALTER COLUMN id SET DEFAULT nextval('public.producto_imagenes_id_seq'::regclass);


--
-- Name: producto_variantes id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_variantes ALTER COLUMN id SET DEFAULT nextval('public.producto_variantes_id_seq'::regclass);


--
-- Name: productos id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos ALTER COLUMN id SET DEFAULT nextval('public.productos_id_seq'::regclass);


--
-- Name: productos_proveedor id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos_proveedor ALTER COLUMN id SET DEFAULT nextval('public.productos_proveedor_id_seq'::regclass);


--
-- Name: promociones id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.promociones ALTER COLUMN id SET DEFAULT nextval('public.promociones_id_seq'::regclass);


--
-- Name: proveedores id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.proveedores ALTER COLUMN id SET DEFAULT nextval('public.proveedores_id_seq'::regclass);


--
-- Name: recepciones_mercaderia id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.recepciones_mercaderia ALTER COLUMN id SET DEFAULT nextval('public.recepciones_mercaderia_id_seq'::regclass);


--
-- Name: reserva_detalles id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reserva_detalles ALTER COLUMN id SET DEFAULT nextval('public.reserva_detalles_id_seq'::regclass);


--
-- Name: reservas id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reservas ALTER COLUMN id SET DEFAULT nextval('public.reservas_id_seq'::regclass);


--
-- Name: stock_sucursal id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.stock_sucursal ALTER COLUMN id SET DEFAULT nextval('public.stock_sucursal_id_seq'::regclass);


--
-- Name: sucursales id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sucursales ALTER COLUMN id SET DEFAULT nextval('public.sucursales_id_seq'::regclass);


--
-- Name: tallas id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tallas ALTER COLUMN id SET DEFAULT nextval('public.tallas_id_seq'::regclass);


--
-- Name: temporadas id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.temporadas ALTER COLUMN id SET DEFAULT nextval('public.temporadas_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: venta_detalles id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.venta_detalles ALTER COLUMN id SET DEFAULT nextval('public.venta_detalles_id_seq'::regclass);


--
-- Name: ventas id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ventas ALTER COLUMN id SET DEFAULT nextval('public.ventas_id_seq'::regclass);


--
-- Data for Name: account; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth.account (id, "accountId", "providerId", "userId", "accessToken", "refreshToken", "idToken", "accessTokenExpiresAt", "refreshTokenExpiresAt", scope, password, "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: invitation; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth.invitation (id, "organizationId", email, role, status, "expiresAt", "createdAt", "inviterId") FROM stdin;
\.


--
-- Data for Name: jwks; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth.jwks (id, "publicKey", "privateKey", "createdAt", "expiresAt") FROM stdin;
\.


--
-- Data for Name: member; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth.member (id, "organizationId", "userId", role, "createdAt") FROM stdin;
\.


--
-- Data for Name: organization; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth.organization (id, name, slug, logo, "createdAt", metadata) FROM stdin;
\.


--
-- Data for Name: project_config; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth.project_config (id, name, endpoint_id, created_at, updated_at, trusted_origins, social_providers, email_provider, email_and_password, allow_localhost, plugin_configs, webhook_config) FROM stdin;
c58ed0dc-8cac-4ed3-8312-4a6871ecd922	FashionStore	ep-misty-pine-ay658r76	2026-09-05 05:19:01.338+00	2026-09-05 05:19:01.338+00	[]	[{"id": "google", "isShared": true}]	{"type": "shared"}	{"enabled": true, "disableSignUp": false, "emailVerificationMethod": "otp", "requireEmailVerification": false, "autoSignInAfterVerification": true, "sendVerificationEmailOnSignIn": false, "sendVerificationEmailOnSignUp": false}	t	{"magicLink": {"config": {"expiresIn": 5, "disableSignUp": false}, "enabled": false}, "phoneNumber": {"config": {"otp_expires_in": 300}, "enabled": false}, "organization": {"config": {"creatorRole": "owner", "membershipLimit": 100, "organizationLimit": 10, "sendInvitationEmail": false}, "enabled": true}}	{"enabled": false, "enabledEvents": [], "timeoutSeconds": 5}
\.


--
-- Data for Name: session; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth.session (id, "expiresAt", token, "createdAt", "updatedAt", "ipAddress", "userAgent", "userId", "impersonatedBy", "activeOrganizationId") FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth."user" (id, name, email, "emailVerified", image, "createdAt", "updatedAt", role, banned, "banReason", "banExpires") FROM stdin;
\.


--
-- Data for Name: verification; Type: TABLE DATA; Schema: neon_auth; Owner: neon_auth
--

COPY neon_auth.verification (id, identifier, value, "expiresAt", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.alembic_version (version_num) FROM stdin;
f4d5e6a7b8c9
i9j0k1l2m3n4
\.


--
-- Data for Name: carrito_items; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.carrito_items (id, carrito_id, producto_variante_id, fecha_agregado, seleccionado) FROM stdin;
187	110	5	2026-09-20 21:50:37.933831+00	f
\.


--
-- Data for Name: carritos; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.carritos (id, cliente_id, fecha_creacion, fecha_actualizacion) FROM stdin;
62	4360	2026-09-17 22:21:06.418099+00	2026-09-17 22:21:06.418099+00
111	4608	2026-09-21 00:26:47.202337+00	2026-09-29 11:37:24.391162+00
119	4623	2026-09-22 12:08:33.250713+00	2026-09-29 11:52:28.459322+00
110	4609	2026-09-20 21:24:04.59471+00	2026-09-20 23:37:11.060136+00
\.


--
-- Data for Name: categorias; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.categorias (id, nombre, is_active, imagen_url, empresa_id) FROM stdin;
677	Calzado	t	\N	\N
568	Categoria b7dce728	f	\N	\N
552	Categoria bda000d1	f	\N	\N
1385	Categoria 2cf9cdb7	f	\N	\N
659	Categoria beddd3f6	f	\N	\N
316	Categoria da4775e8	f	\N	\N
545	Categoria 2a5c9552	f	\N	\N
1087	Bolsos	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/6b3226ed92594913b9b912c801d8fdfd.jpg	\N
554	Categoria 85e3b477	f	\N	\N
242	Categoria 257957b7	f	\N	\N
676	Categoria 0bdc0b33	f	\N	\N
1088	Categoria 118b5add	f	\N	\N
1382	Categoria 29e80fbf	f	\N	\N
666	Accesorios	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/40e86b80ea8c4661b6004eeac0be7d59.jpg	\N
1173	Categoria 2b6351c6	f	\N	\N
664	Categoria 43a81482	f	\N	\N
1387	Abrigos	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/dfc870d983304eb382a9be0e3b6bd36b.jpg	\N
679	Categoria 4477a021	f	\N	\N
655	Vestidos	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/8d40778eb1404095947185609eebabca.jpg	\N
1171	Pantalones	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/ab2fe161c32f4bc197d16ebcaa9074a9.jpg	\N
1085	Categoria 382ab4db	f	\N	\N
1	Blusas	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/ed161dc84bec4afcbb7e743925964dd2.jpg	\N
883	DEPORTE	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/3808463539fb45f3a7aefffc14282dd2.jpg	\N
674	Categoria 1c5297d9	f	\N	\N
1120	Categoria ff6a971f	f	\N	\N
1086	Categoria 1c92491f	f	\N	\N
668	Categoria 25437a6f	f	\N	\N
670	Categoria 377ac1c9	f	\N	\N
557	Categoria 3770f276	f	\N	\N
555	Categoria 421c84aa	f	\N	\N
665	Categoria 3346c688	f	\N	\N
680	Categoria 22e75069	f	\N	\N
1084	Categoria 1e624154	f	\N	\N
1172	Categoria 32552d32	f	\N	\N
672	Categoria 49080b4b	f	\N	\N
654	Categoria 70770165	f	\N	\N
667	Categoria adcd7e76	f	\N	\N
661	Categoria 9ff37315	f	\N	\N
671	Categoria 984cc384	f	\N	\N
569	Categoria 4b8b0f60	f	\N	\N
681	Categoria c37276ae	f	\N	\N
1032	Categoria 9d0d301a	f	\N	\N
1174	Categoria 8a6b2a5f	f	\N	\N
1181	Categoria c3c691e4	f	\N	\N
662	Categoria 9fb83135	f	\N	\N
553	Categoria 4bd088be	f	\N	\N
663	Categoria c4be23ec	f	\N	\N
1183	Categoria 5f6a3251	f	\N	\N
669	Categoria 6b1bdab3	f	\N	\N
917	Categoria 6859fcd3	f	\N	\N
660	Categoria 55b81b1d	f	\N	\N
656	Categoria 8bac4271	f	\N	\N
1386	Categoria 4df10f2b	f	\N	\N
683	Categoria ea240691	f	\N	\N
682	Categoria 53aa0a23	f	\N	\N
678	Categoria 61e45d64	f	\N	\N
1176	Categoria 655d0f55	f	\N	\N
675	Categoria afb35648	f	\N	\N
1381	Categoria 8b98d6ec	f	\N	\N
673	Categoria a0a504d8	f	\N	\N
1529	Categoria aa997ffe	f	\N	\N
1175	Categoria f9546c40	f	\N	\N
1388	Categoria a1208af1	f	\N	\N
1384	Categoria a401dd69	f	\N	\N
1083	Categoria ee8178f6	f	\N	\N
810	Categoria f6b48186	f	\N	\N
551	Categoria f15a7b4f	f	\N	\N
652	Categoria f1e3931f	f	\N	\N
544	Categoria e5c8184b	f	\N	\N
1383	Categoria b35cd479	f	\N	\N
657	Categoria b68c1bc2	f	\N	\N
658	CHAQUETAS	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/bfb4fb9b8058434aa95fdf9b86ad25f1.jpg	\N
653	HOODIES	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/categorias/92a45245483e4643b03ae6687a817631.jpg	\N
1712	Categoría 28d1ee	t	\N	\N
1804	Categoria 72c15306	t	\N	\N
1805	Categoria e0a40b13	t	\N	\N
\.


--
-- Data for Name: ciudades; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.ciudades (id, nombre, is_active, departamento, empresa_id) FROM stdin;
1	Santa Cruz	t	Santa Cruz	\N
625	Ciudad 49080b4b	f	Depto	\N
622	Ciudad 6b1bdab3	f	Depto	\N
865	Ciudad 6859fcd3	f	Depto	\N
626	Ciudad a0a504d8	f	Depto	\N
607	Ciudad 70770165	f	Depto	\N
608	Ciudad b82c0b36	f	Depto	\N
1130	Ciudad c161610f	f	Depto	\N
1134	Ciudad f9546c40	f	Depto	\N
619	Ciudad de20e805	f	Depto	\N
1040	Ciudad ee8178f6	f	Depto	\N
605	Ciudad f1e3931f	f	Depto	\N
1493	Ciudad aa997ffe	f	Depto	\N
499	Ciudad e5c8184b	f	Depto	\N
1427	Ciudad e6dea0f6	f	Depto	\N
610	Ciudad b68c1bc2	f	Depto	\N
628	Ciudad afb35648	f	Depto	\N
620	Ciudad adcd7e76	f	Depto	\N
634	Ciudad aaa0396c	f	Depto	\N
1345	Ciudad a401dd69	f	Depto	\N
1351	Ciudad 6d036f37	f	Depto	\N
523	Ciudad b7dce728	f	Depto	\N
506	Ciudad f15a7b4f	f	Depto	\N
637	Ciudad ea240691	f	Depto	\N
1342	Ciudad 8b98d6ec	f	Depto	\N
614	Ciudad 9ff37315	f	Depto	\N
635	Ciudad c37276ae	f	Depto	\N
1349	Ciudad a1208af1	f	Depto	\N
1133	Ciudad 8a6b2a5f	f	Depto	\N
507	Ciudad bda000d1	f	Depto	\N
509	Ciudad 85e3b477	f	Depto	\N
609	Ciudad 8bac4271	f	Depto	\N
612	Ciudad beddd3f6	f	Depto	\N
989	Ciudad 9d0d301a	f	Depto	\N
624	Ciudad 984cc384	f	Depto	\N
615	Ciudad 9fb83135	f	Depto	\N
1140	Ciudad c3c691e4	f	Depto	\N
1348	Ciudad d9badbc1	f	Depto	\N
761	Ciudad f6b48186	f	Depto	\N
1044	Ciudad d38c1f76	f	Depto	\N
616	Ciudad c4be23ec	f	Depto	\N
1079	Ciudad ff6a971f	f	Depto	\N
1648	Sucre	t	Chuquisaca	\N
1649	El alto	t	La paz	\N
831	Ciudad 05c8d4d9	f	Depto	\N
630	Ciudad 07930464	f	Depto	\N
629	Ciudad 0bdc0b33	f	Depto	\N
1650	Cochabamba	t	Cochabamba	\N
1651	Cobija	t	Pando	\N
1045	Ciudad 118b5add	f	Depto	\N
606	Ciudad 12bdaa56	f	Depto	\N
611	Ciudad 1654bcf4	f	Depto	\N
1347	Ciudad 4df10f2b	f	Depto	\N
617	Ciudad 43a81482	f	Depto	\N
508	Ciudad 4bd088be	f	Depto	\N
1142	Ciudad 5f6a3251	f	Depto	\N
510	Ciudad 421c84aa	f	Depto	\N
524	Ciudad 4b8b0f60	f	Depto	\N
631	Ciudad 61e45d64	f	Depto	\N
1042	Ciudad 382ab4db	f	Depto	\N
636	Ciudad 53aa0a23	f	Depto	\N
1132	Ciudad 2b6351c6	f	Depto	\N
1344	Ciudad b35cd479	f	Depto	\N
1135	Ciudad 655d0f55	f	Depto	\N
1340	Ciudad 54860d87	f	Depto	\N
632	Ciudad 4477a021	f	Depto	\N
1131	Ciudad 32552d32	f	Depto	\N
623	Ciudad 377ac1c9	f	Depto	\N
618	Ciudad 3346c688	f	Depto	\N
512	Ciudad 3770f276	f	Depto	\N
500	Ciudad 2a5c9552	f	Depto	\N
633	Ciudad 22e75069	f	Depto	\N
1343	Ciudad 29e80fbf	f	Depto	\N
1346	Ciudad 2cf9cdb7	f	Depto	\N
621	Ciudad 25437a6f	f	Depto	\N
1043	Ciudad 1c92491f	f	Depto	\N
758	Ciudad 19d44985	f	Santa Cruz	\N
627	Ciudad 1c5297d9	f	Depto	\N
1041	Ciudad 1e624154	f	Depto	\N
613	Ciudad 55b81b1d	f	Depto	\N
1664	Ciudad 8b849791	t	Depto	\N
1682	Ciudad 72c15306	t	Depto	\N
1683	Ciudad e0a40b13	t	Depto	\N
\.


--
-- Data for Name: colecciones; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.colecciones (id, nombre, temporada_id, descripcion, is_active, es_destacada_inicio, imagen_destacada_url, empresa_id) FROM stdin;
1012	Coleccion 61e45d64	1361	\N	f	f	\N	\N
1245	Coleccion 6859fcd3	1618	\N	f	f	\N	\N
1504	Coleccion 655d0f55	1877	\N	f	f	\N	\N
1017	Coleccion ea240691	1366	\N	f	f	\N	\N
875	Coleccion e5c8184b	1200	\N	f	f	\N	\N
995	Coleccion 9ff37315	1344	\N	f	f	\N	\N
1000	Coleccion de20e805	1349	\N	f	f	\N	\N
993	Coleccion beddd3f6	1342	\N	f	f	\N	\N
1712	Coleccion 8b98d6ec	2109	\N	f	f	\N	\N
990	Coleccion 8bac4271	1339	\N	f	f	\N	\N
1005	Coleccion 984cc384	1354	\N	f	f	\N	\N
1360	Coleccion 9d0d301a	1733	\N	f	f	\N	\N
996	Coleccion 9fb83135	1345	\N	f	f	\N	\N
1007	Coleccion a0a504d8	1356	\N	f	f	\N	\N
541	Coleccion da4775e8	741	\N	f	f	\N	\N
1415	Coleccion d38c1f76	1788	\N	f	f	\N	\N
1719	Coleccion a1208af1	2116	\N	f	f	\N	\N
899	Coleccion b7dce728	1224	\N	f	f	\N	\N
989	Coleccion b82c0b36	1338	\N	f	f	\N	\N
883	Coleccion bda000d1	1208	\N	f	f	\N	\N
1718	Coleccion d9badbc1	2115	\N	f	f	\N	\N
997	Coleccion c4be23ec	1346	\N	f	f	\N	\N
991	Coleccion b68c1bc2	1340	\N	f	f	\N	\N
1509	Coleccion c3c691e4	1882	\N	f	f	\N	\N
1015	Coleccion c37276ae	1364	\N	f	f	\N	\N
1715	Coleccion a401dd69	2112	\N	f	f	\N	\N
1499	Coleccion c161610f	1872	\N	f	f	\N	\N
1011	Coleccion 07930464	1360	\N	f	f	\N	\N
1010	Coleccion 0bdc0b33	1359	\N	f	f	\N	\N
1860	Coleccion aa997ffe	2257	\N	f	f	\N	\N
1714	Coleccion b35cd479	2111	\N	f	f	\N	\N
1001	Coleccion adcd7e76	1350	\N	f	f	\N	\N
1009	Invierno	1358	\N	t	f	\N	\N
87	Urban	1	\N	t	f	\N	\N
1211	PRETY	1	\N	f	f	\N	\N
2015	Europeo	1	\N	t	f	\N	\N
1448	Coleccion ff6a971f	1821	\N	f	f	\N	\N
987	Coleccion 12bdaa56	1336	\N	f	f	\N	\N
2018	Colección 45db69	2416	\N	t	f	\N	\N
1416	Coleccion 118b5add	1789	\N	f	f	\N	\N
992	Coleccion 1654bcf4	1341	\N	f	f	\N	\N
1412	Coleccion 1e624154	1785	\N	f	f	\N	\N
1008	Coleccion 1c5297d9	1357	\N	f	f	\N	\N
1414	Coleccion 1c92491f	1787	\N	f	f	\N	\N
1014	Coleccion 22e75069	1363	\N	f	f	\N	\N
1002	Coleccion 25437a6f	1351	\N	f	f	\N	\N
390	Coleccion 257957b7	538	\N	f	f	\N	\N
876	Coleccion 2a5c9552	1201	\N	f	f	\N	\N
1713	Coleccion 29e80fbf	2110	\N	f	f	\N	\N
1501	Coleccion 2b6351c6	1874	\N	f	f	\N	\N
1716	Coleccion 2cf9cdb7	2113	\N	f	f	\N	\N
888	Coleccion 3770f276	1213	\N	f	f	\N	\N
1500	Coleccion 32552d32	1873	\N	f	f	\N	\N
999	Coleccion 3346c688	1348	\N	f	f	\N	\N
1004	Coleccion 377ac1c9	1353	\N	f	f	\N	\N
1413	Coleccion 382ab4db	1786	\N	f	f	\N	\N
886	Coleccion 421c84aa	1211	\N	f	f	\N	\N
1147	Coleccion f6b48186	1520	\N	f	f	\N	\N
1502	Coleccion 8a6b2a5f	1875	\N	f	f	\N	\N
885	Coleccion 85e3b477	1210	\N	f	f	\N	\N
988	Coleccion 70770165	1337	\N	f	f	\N	\N
998	Coleccion 43a81482	1347	\N	f	f	\N	\N
1503	Coleccion f9546c40	1876	\N	f	f	\N	\N
1003	Coleccion 6b1bdab3	1352	\N	f	f	\N	\N
986	Coleccion f1e3931f	1335	\N	f	f	\N	\N
1013	Coleccion 4477a021	1362	\N	f	f	\N	\N
882	Coleccion f15a7b4f	1207	\N	f	f	\N	\N
1006	Coleccion 49080b4b	1355	\N	f	f	\N	\N
900	Coleccion 4b8b0f60	1225	\N	f	f	\N	\N
884	Coleccion 4bd088be	1209	\N	f	f	\N	\N
1717	Coleccion 4df10f2b	2114	\N	f	f	\N	\N
1016	Coleccion 53aa0a23	1365	\N	f	f	\N	\N
994	Coleccion 55b81b1d	1343	\N	f	f	\N	\N
1411	Coleccion ee8178f6	1784	\N	f	f	\N	\N
1511	Coleccion 5f6a3251	1884	\N	f	f	\N	\N
2140	Coleccion 72c15306	2616	\N	t	f	\N	\N
2141	Coleccion e0a40b13	2617	\N	t	f	\N	\N
1	Asia	1	\N	t	f	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/colecciones/ca404aff987d4a85bf880b4d02267ac2.png	\N
\.


--
-- Data for Name: colores; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.colores (id, nombre, is_active, empresa_id) FROM stdin;
1	Negro	t	\N
2	Blanco	t	\N
796	Amarillo	t	\N
1403	Color-ddc20b66	f	\N
1411	Color-b4092025	f	\N
1189	Negro-05c8d4d9	f	\N
1408	Verde	t	\N
1397	Color-c1c9fb65	f	\N
1396	Color-cd1361e6	f	\N
1518	Color-dfee75e1	f	\N
1496	Naranja	t	\N
1508	Plomo	t	\N
951	Negro-07930464	f	\N
950	Negro-0bdc0b33	f	\N
1404	Negro-1c92491f	f	\N
1398	Negro-1e624154	f	\N
954	Negro-22e75069	f	\N
808	Negro-3770f276	f	\N
1783	Negro-2cf9cdb7	f	\N
953	Negro-4477a021	f	\N
939	Negro-3346c688	f	\N
1782	Negro-a401dd69	f	\N
938	Negro-43a81482	f	\N
1410	Negro-118b5add	f	\N
927	Negro-12bdaa56	f	\N
932	Negro-1654bcf4	f	\N
343	Negro-257957b7	f	\N
1780	Negro-29e80fbf	f	\N
1401	Celeste	t	\N
804	Amarillo pastel	t	\N
948	Fuccia	t	\N
1498	Negro-32552d32	f	\N
1501	Negro-2b6351c6	f	\N
946	Negro-49080b4b	f	\N
820	Negro-4b8b0f60	f	\N
806	Negro-421c84aa	f	\N
1521	Negro-5f6a3251	f	\N
1510	Negro-655d0f55	f	\N
928	Negro-70770165	f	\N
1784	Negro-4df10f2b	f	\N
942	Negro-25437a6f	f	\N
934	Negro-55b81b1d	f	\N
956	Negro-53aa0a23	f	\N
952	Negro-61e45d64	f	\N
944	Negro-377ac1c9	f	\N
1223	Negro-6859fcd3	f	\N
930	Negro-8bac4271	f	\N
805	Negro-85e3b477	f	\N
943	Negro-6b1bdab3	f	\N
1344	Negro-9d0d301a	f	\N
1786	Negro-a1208af1	f	\N
945	Negro-984cc384	f	\N
1504	Negro-8a6b2a5f	f	\N
1779	Negro-8b98d6ec	f	\N
947	Negro-a0a504d8	f	\N
949	Negro-afb35648	f	\N
941	Negro-adcd7e76	f	\N
931	Negro-b68c1bc2	f	\N
819	Negro-b7dce728	f	\N
344	Blanco-257957b7	f	\N
1406	Color-059e07f8	f	\N
1400	Color-06b5a535	f	\N
1409	Color-065dae11	f	\N
1399	Color-149429c4	f	\N
1412	Color-2421d8c0	f	\N
937	Negro-c4be23ec	f	\N
1512	Color-22972cfc	f	\N
1444	Azul	t	\N
1107	Rosa	t	\N
1519	Lila	t	\N
1497	Crema	t	\N
1509	Pistacho	t	\N
1500	Color-3f44e902	f	\N
1506	Color-9fd161f1	f	\N
1499	Color-5293a550	f	\N
1507	Negro-f9546c40	f	\N
1405	Color-8195d28a	f	\N
1511	Color-85cc9de0	f	\N
1505	Color-79a4092b	f	\N
1503	Color-591a5a03	f	\N
936	Negro-9fb83135	f	\N
1402	Color-71a4bf1a	f	\N
1502	Color-6d6bcdd9	f	\N
1785	Rojo	t	\N
935	Negro-9ff37315	f	\N
1495	Negro-c161610f	f	\N
1990	Negro-aa997ffe	f	\N
802	Negro-f15a7b4f	f	\N
926	Negro-f1e3931f	f	\N
1395	Negro-ee8178f6	f	\N
795	Negro-e5c8184b	f	\N
1781	Negro-b35cd479	f	\N
933	Negro-beddd3f6	f	\N
929	Negro-b82c0b36	f	\N
1407	Negro-d38c1f76	f	\N
803	Negro-bda000d1	f	\N
955	Negro-c37276ae	f	\N
1517	Negro-c3c691e4	f	\N
957	Rosa pastel	t	\N
940	Perla	t	\N
451	Mostaza	t	\N
2193	Alfa-099e99	t	\N
2194	Beta-95f2e2	f	\N
2202	Negro-28d1ee	t	\N
2363	Negro-72c15306	t	\N
2364	Negro-e0a40b13	t	\N
\.


--
-- Data for Name: detalles_recepcion_mercaderia; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.detalles_recepcion_mercaderia (id, recepcion_id, producto_variante_id, cantidad_recibida) FROM stdin;
1	1	684	10
2	2	684	5
3	3	684	1
4	4	1	7
5	4	2	3
6	5	55	5
\.


--
-- Data for Name: devoluciones_cambios; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.devoluciones_cambios (id, venta_id, venta_detalle_id, tipo, cantidad, variante_original_id, variante_nueva_id, motivo, observacion, monto_reembolso, metodo_reembolso, estado_reembolso, stripe_refund_id, cajero_id, sucursal_id, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: empresas; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.empresas (id, nombre, slug, razon_social, correo, telefono, is_active, created_at, updated_at) FROM stdin;
1	FashionStore - Empresa Principal	fashionstore-empresa-principal	FashionStore Empresa Principal	admin@fashionstore-principal.com	+591 2 123456789	t	2026-10-24 23:28:14.287495+00	2026-10-24 23:28:14.287495+00
\.


--
-- Data for Name: movimientos_inventario; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.movimientos_inventario (id, sucursal_id, producto_variante_id, usuario_id, tipo, cantidad, motivo, stock_anterior, stock_resultante, fecha_hora) FROM stdin;
1	1	684	2661	AJUSTE_POSITIVO	3	Conteo fisico detecto 3 unidades adicionales	16	19	2026-09-13 20:22:19.773029+00
2	1	684	2661	AJUSTE_NEGATIVO	2	2 prendas danadas	19	17	2026-09-13 20:23:16.801728+00
3	1	684	2661	AJUSTE_POSITIVO	1	intento manipular sucursal	17	18	2026-09-13 20:25:10.151476+00
4	430	883	2669	AJUSTE_POSITIVO	3	Conteo físico detectó unidades adicionales	10	13	2026-09-13 20:35:03.27955+00
5	431	884	2670	AJUSTE_NEGATIVO	2	2 prendas dañadas	10	8	2026-09-13 20:35:18.303878+00
6	437	891	2676	AJUSTE_POSITIVO	5	intento cruzado	0	5	2026-09-13 20:37:11.415689+00
7	439	892	2678	AJUSTE_POSITIVO	5	intento de manipular la sucursal	10	15	2026-09-13 20:37:34.609468+00
8	441	894	2680	AJUSTE_POSITIVO	3	Conteo físico	10	13	2026-09-13 20:37:48.976221+00
9	443	896	2682	AJUSTE_POSITIVO	1	movimiento de la sucursal B	20	21	2026-09-13 20:38:16.685887+00
40	1	2447	4620	AJUSTE_POSITIVO	5	se encontor	0	5	2026-09-22 12:00:55.626761+00
41	1	2596	4620	AJUSTE_POSITIVO	15	AUMENTO DE STOCK	0	15	2026-09-29 11:38:01.417809+00
42	1	58	4620	AJUSTE_POSITIVO	14	MAS STOCK	0	14	2026-09-29 11:38:33.953151+00
43	1	2441	4620	AJUSTE_POSITIVO	2	LLEGARON TALLAS	0	2	2026-09-29 11:38:58.10971+00
44	1	2442	4620	AJUSTE_POSITIVO	7	LLEGARON TALLAS	0	7	2026-09-29 11:39:06.642541+00
45	1	2445	4620	AJUSTE_POSITIVO	14	LLEGARON TALLAS	0	14	2026-09-29 11:39:16.27392+00
46	1	2443	4620	AJUSTE_POSITIVO	10	LLEGARON TALLAS	0	10	2026-09-29 11:39:25.234624+00
47	1	2444	4620	AJUSTE_POSITIVO	7	LLEGARON TALLAS	0	7	2026-09-29 11:39:39.82056+00
48	1	2446	4620	AJUSTE_POSITIVO	7	LLEGARON TALLAS	0	7	2026-09-29 11:39:49.471058+00
\.


--
-- Data for Name: pagos; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pagos (id, venta_id, proveedor, stripe_checkout_session_id, stripe_payment_intent_id, monto, estado, fecha_creacion, fecha_confirmacion, cajero_id, monto_recibido, cambio, tipo_tarjeta, referencia) FROM stdin;
20	49	STRIPE	cs_test_a1M6J8PIkobijEuGmEsqseBlGxl9LJrUoQ1dyoNf1W5mOhty1eR6RTTiLl	\N	100.00	PENDIENTE	2026-09-21 00:01:12.091568+00	\N	\N	\N	\N	\N	\N
21	50	STRIPE	cs_test_a1IcYkEFieVYWRGqByCG5aVpyxFbgdUR2BPRo4vZlmaD69JvANtEfTZGHo	\N	100.00	PENDIENTE	2026-09-21 00:27:40.879516+00	\N	\N	\N	\N	\N	\N
29	58	STRIPE	cs_test_a1dZH46PLaUCVAdA1A0JwfmuWRN9OQ7mccWQ17zIDSQtlZpSP9r2d9pQdV	\N	100.00	PENDIENTE	2026-09-21 00:45:37.710401+00	\N	\N	\N	\N	\N	\N
30	59	STRIPE	cs_test_a1vRTlGVqlZPUDE1wjAzmOUtpmU5X2brSVmFJhmw2JfoqqHvxUbp2fHcfj	\N	100.00	PENDIENTE	2026-09-21 00:59:23.787206+00	\N	\N	\N	\N	\N	\N
31	60	STRIPE	cs_test_a1NzkTunsypTell7N5MZfIRAK9XO6bU0UZRZCho3pTlG93HGASpxjLvEFh	pi_3UHwy8JO82YVluNl0Ru3ymHL	100.00	PAGADO	2026-09-21 02:28:05.279209+00	2026-09-21 02:28:40.680542+00	\N	\N	\N	\N	\N
32	61	STRIPE	cs_test_a15O3wdaTNMqtM8sHrnakbIHSx04dkwK6uAJ0uTRQxcNOHncU1H4Mq9AO7	pi_3UIS9OJO82YVluNl2BR5XBM3	100.00	PAGADO	2026-09-22 11:45:42.341758+00	2026-09-22 11:46:21.542218+00	\N	\N	\N	\N	\N
33	62	STRIPE	cs_test_a1Fh1OdlbvyMqEWLPqDzrQNDR5mlhb1VT39kC4A28JiADFBYswzq8SaHwL	pi_3UISETJO82YVluNl0K3ekwr4	100.00	PAGADO	2026-09-22 11:50:51.560452+00	2026-09-22 11:51:36.786477+00	\N	\N	\N	\N	\N
34	63	STRIPE	cs_test_a1bRmYauqTvyecKKlmyWZ4N5WVBj9bw5btHjM9qpMnPjjlOqtYSFBujhC2	pi_3UISWKJO82YVluNl0f36qI9S	100.00	PAGADO	2026-09-22 12:09:08.411155+00	2026-09-22 12:10:04.924228+00	\N	\N	\N	\N	\N
35	64	STRIPE	cs_test_a1niedQ21dlQohRNTXaowhAvzvSIqTPxdtiKn1xSlQVHdNrq05vGKXTEZu	pi_3UKzWUJO82YVluNl1Btf5jyV	90.00	PAGADO	2026-09-29 11:47:55.143945+00	2026-09-29 11:48:41.619975+00	\N	\N	\N	\N	\N
37	66	STRIPE	cs_test_a1HyLykruI0WYKZtJ2uFSn3C4cBoBJ3SpEAFtrWZI607urzww6WzE6HAgl	\N	90.00	FALLIDO	2026-09-29 11:56:56.352635+00	\N	\N	\N	\N	\N	\N
36	65	STRIPE	cs_test_a1mkF04CCMNBIxANCRvIsdDqupf7BG2QgjFdjsvawnfQS5EQYC1AEKEK7B	pi_3UKzfXJO82YVluNl1Uk0MlkE	90.00	PAGADO	2026-09-29 11:52:59.698546+00	2026-09-29 11:58:04.635883+00	\N	\N	\N	\N	\N
38	67	STRIPE	cs_test_a1TkZQtZrZvVjCkjDV6KfgnRm13S3Adf6oKIGUEy0K5a2yDeORqcdCIpdB	pi_3UKzy9JO82YVluNl0WkPgNQA	100.00	PAGADO	2026-09-29 12:16:46.774644+00	2026-09-29 12:17:17.504357+00	\N	\N	\N	\N	\N
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.password_reset_tokens (id, usuario_id, token_hash, expires_at, used_at, created_at) FROM stdin;
73	4609	55c8a4c9c8c67b593b643cf7e9457c307b7bf9bfc2860d87f88b76c68e5e4485	2026-09-20 19:32:19.227945+00	\N	2026-09-20 19:02:19.203156+00
\.


--
-- Data for Name: producto_colores; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.producto_colores (producto_id, color_id) FROM stdin;
1	1
1	2
298	2
1504	2363
799	1344
1505	2364
684	1223
272	2
938	1495
939	1498
940	1501
941	1504
942	1507
943	1510
14	1
14	2
1279	1990
948	1517
586	1107
445	926
446	927
447	928
448	929
449	930
450	931
451	932
452	933
354	795
355	796
453	934
454	935
455	936
456	937
457	938
324	2
361	802
362	803
363	804
364	805
365	806
458	939
367	808
459	940
460	941
461	942
462	943
463	944
464	945
465	946
466	947
468	949
469	950
379	820
470	951
471	952
472	953
473	954
474	955
475	956
476	957
950	1521
887	1444
1131	1779
1132	1780
1133	1781
650	1189
1134	1782
1135	1783
1136	1784
1137	1785
1138	1786
850	1395
851	1398
852	1401
853	1404
854	1407
855	1410
1434	1
1434	2
1435	1408
1435	1401
1435	1444
1435	957
1435	940
298	1
298	1508
298	1444
650	1
650	2
650	804
650	1444
650	1497
650	957
470	1
470	1508
470	1444
469	1
469	2
469	1444
942	1
942	804
942	1444
942	451
855	1
855	796
855	1444
855	1509
854	1
854	1444
446	1401
446	1444
451	1
451	2
451	1444
451	1785
467	1
467	2
467	1497
467	1509
14	1444
14	1509
\.


--
-- Data for Name: producto_imagenes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.producto_imagenes (id, producto_id, url, orden) FROM stdin;
179	1434	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/08237e14e8ba46338bcd92014e3f1f9a.jpg	0
180	1434	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/a4da1e6f7e0b4958bec9f70ce098d533.jpg	1
181	298	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/a9e1dd64186f43dca24352da29330220.jpg	0
182	298	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/8afba43000264ceb915eea896c694db1.jpg	1
183	470	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/50b4e6179d324f2abab8bb78b061a754.jpg	0
184	469	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/683e4d2c40a240d285554afa7a04fa9e.jpg	0
185	854	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/cbe499a04b4a408aa95c5b030eae93f9.jpg	0
186	854	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/44cb6396ac3f45dbb2410fc034d9a063.jpg	1
187	446	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/11368e722e5b4f0882e03fc56dac0368.jpg	0
188	1	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/89e181ea346d49ab9596ada3466dfc29.jpg	0
189	14	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/aaa92d3d831349528000a5a7b439e60c.jpg	0
\.


--
-- Data for Name: producto_tallas; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.producto_tallas (producto_id, talla_id) FROM stdin;
1	1
1	2
1	3
298	2
799	1347
684	1225
272	2
938	1499
939	1502
940	1505
941	1508
942	1511
943	1514
1504	2470
14	1
14	2
1505	2471
948	1521
586	1108
445	927
446	928
447	929
448	930
449	931
450	932
451	933
452	934
354	796
355	797
453	935
454	936
455	937
456	938
457	939
324	2
361	803
362	804
363	805
364	806
365	807
458	940
367	809
459	941
460	942
461	943
462	944
463	945
464	946
465	947
466	948
467	949
468	950
469	951
379	821
471	953
472	954
473	955
474	956
475	957
476	958
950	1525
887	1448
1131	1784
1132	1786
1133	1788
1134	1790
1135	1792
1136	1794
1137	1796
1138	1798
650	1191
1279	2022
1279	2023
850	1398
851	1401
852	1404
853	1407
854	1410
855	1413
1434	2
1434	2276
1434	2022
1435	1
1435	2
1435	2276
298	1
298	2276
298	1191
298	952
650	2
650	2276
470	2
470	3
470	2276
469	1
469	2
469	952
942	2277
942	2022
942	1191
855	2
855	2276
854	2278
854	1191
446	2
446	1512
446	1191
451	2
14	2276
\.


--
-- Data for Name: producto_variantes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.producto_variantes (id, producto_id, talla_id, color_id, is_active) FROM stdin;
1	1	1	2	t
2	1	2	1	t
3	1	3	1	t
4	1	1	1	t
5	1	2	2	t
6	1	3	2	t
812	324	2	2	t
1879	1131	1784	1779	t
1880	1131	1785	1779	t
1881	1132	1786	1780	t
1882	1132	1787	1780	t
1883	1133	1788	1781	t
1884	1133	1789	1781	t
1885	1134	1790	1782	t
1886	1134	1791	1782	t
1491	850	1398	1395	t
883	354	796	795	t
884	355	797	796	t
1492	850	1399	1396	t
1493	850	1400	1397	t
1494	851	1401	1398	t
1495	851	1402	1399	t
1496	851	1403	1400	t
890	361	803	802	t
891	362	804	803	t
892	363	805	804	t
893	364	806	805	t
894	365	807	806	t
1015	445	927	926	t
896	367	809	808	t
1016	446	928	927	t
1017	447	929	928	t
1018	448	930	929	t
1019	449	931	930	t
1020	450	932	931	t
1021	451	933	932	t
1022	452	934	933	t
1023	453	935	934	t
1024	454	936	935	t
1025	455	937	936	t
1026	456	938	937	t
908	379	821	820	t
1027	457	939	938	t
1028	458	940	939	t
1029	459	941	940	t
1030	460	942	941	t
1031	461	943	942	t
1032	462	944	943	t
684	272	2	2	t
1033	463	945	944	t
1034	464	946	945	t
1035	465	947	946	t
55	14	1	1	t
56	14	1	2	t
57	14	2	1	t
58	14	2	2	t
1036	466	948	947	t
748	298	2	2	t
1038	468	950	949	t
1039	469	951	950	t
1041	471	953	952	t
1042	472	954	953	t
1043	473	955	954	t
1044	474	956	955	t
1045	475	957	956	t
1046	476	958	957	t
1497	852	1404	1401	t
1498	852	1405	1402	t
1499	852	1406	1403	t
1312	684	1225	1223	t
1500	853	1407	1404	t
1501	853	1408	1405	t
1440	799	1347	1344	t
1502	853	1409	1406	t
1503	854	1410	1407	t
1506	855	1413	1410	t
1887	1135	1792	1783	t
1197	586	1108	1107	t
1888	1135	1793	1783	t
1889	1136	1794	1784	t
1890	1136	1795	1784	t
1891	1137	1796	1785	t
1892	1137	1797	1785	t
1893	1138	1798	1786	t
1894	1138	1799	1786	t
2807	1504	2470	2363	t
2808	1505	2471	2364	t
1592	938	1499	1495	t
1593	938	1500	1496	t
1594	938	1501	1497	t
1278	650	1191	1189	t
1595	939	1502	1498	t
1596	939	1503	1499	t
1597	939	1504	1500	t
1598	940	1505	1501	t
1599	940	1506	1502	t
1600	940	1507	1503	t
1601	941	1508	1504	t
1602	941	1509	1505	t
1603	941	1510	1506	t
1604	942	1511	1507	t
1607	943	1514	1510	t
1541	887	1448	1444	t
1608	943	1515	1511	t
1609	943	1516	1512	t
2441	1434	2	1	t
1614	948	1521	1517	t
1615	948	1522	1518	t
1616	948	1523	1519	t
2442	1434	2276	2	t
1618	950	1525	1521	t
2443	1434	2022	2	t
2444	1434	2276	1	t
2445	1434	2	2	t
2446	1434	2022	1	t
2447	1435	1	957	t
2448	1435	2	1444	t
2449	1435	2276	1401	t
2450	1435	2276	957	t
2451	1435	1	940	t
2452	1435	2276	940	t
2453	1435	1	1444	t
2454	1435	2	1408	t
2455	1435	1	1408	t
2456	1435	2	1401	t
2457	1435	2	957	t
2458	1435	2276	1444	t
2459	1435	1	1401	t
2460	1435	2276	1408	t
2461	1435	2	940	t
2462	298	2276	2	t
2463	298	1191	1	t
2464	298	1191	1444	t
2465	298	1191	1508	t
2466	298	2276	1	t
2467	298	2276	1444	t
2468	298	2276	1508	t
2469	298	2	1444	t
2470	298	1	2	t
2471	298	2	1	t
2472	298	2	1508	t
2473	298	952	2	t
2474	298	1	1	t
2475	298	1	1444	t
2476	298	1	1508	t
2477	298	1191	2	t
2172	1279	2022	1990	t
2173	1279	2023	1990	t
2478	298	952	1	t
2479	298	952	1444	t
2480	298	952	1508	t
2481	650	2276	1497	t
2482	650	2276	957	t
2483	650	2276	2	t
2484	650	1191	804	t
2485	650	2	1189	t
2486	650	2	1497	t
2487	650	2	957	t
2488	650	2	2	t
2489	650	2276	804	t
2490	650	1191	1	t
2491	650	1191	1444	t
2492	650	2	804	t
2493	650	2276	1	t
2494	650	2276	1444	t
2495	650	2	1444	t
2496	650	2	1	t
2497	650	1191	1497	t
2498	650	1191	957	t
2499	650	1191	2	t
2500	650	2276	1189	t
2501	470	2	1444	t
2502	470	2276	951	t
2503	470	2	1508	t
2504	470	2	1	t
2505	470	3	1444	t
2506	470	3	1	t
2507	470	3	1508	t
2508	470	2276	1444	t
2509	470	2276	1	t
2510	470	2	951	t
2511	470	3	951	t
2512	470	2276	1508	t
2513	469	2	1444	t
2514	469	1	2	t
2515	469	951	1	t
2516	469	2	1	t
2517	469	951	1444	t
2518	469	1	950	t
2519	469	1	1	t
2520	469	1	1444	t
2521	469	952	2	t
2522	469	952	950	t
2523	469	952	1	t
2524	469	2	2	t
2525	469	952	1444	t
2526	469	2	950	t
2527	469	951	2	t
2528	942	1191	804	t
2529	942	2022	1507	t
2530	942	2277	1507	t
2531	942	1191	1	t
2532	942	2022	451	t
2533	942	1191	1444	t
2534	942	2277	451	t
2535	942	1511	451	t
2536	942	2277	804	t
2537	942	2022	804	t
2538	942	1191	1507	t
2539	942	2022	1444	t
2540	942	1511	804	t
2541	942	2022	1	t
2542	942	1191	451	t
2543	942	2277	1444	t
2544	942	2277	1	t
2545	942	1511	1	t
2546	942	1511	1444	t
2547	855	2	1444	t
2548	855	2	1	t
2549	855	2276	796	t
2550	855	2276	1410	t
2551	855	2276	1509	t
2552	855	1413	796	t
2553	855	2276	1	t
2554	855	1413	1509	t
2555	855	2276	1444	t
2556	855	2	796	t
2557	855	2	1410	t
2558	855	1413	1	t
2559	855	2	1509	t
2560	855	1413	1444	t
2561	854	1191	1444	t
2562	854	1410	1	t
2563	854	2278	1407	t
2564	854	1191	1407	t
2565	854	2278	1444	t
2566	854	2278	1	t
2567	854	1191	1	t
2568	854	1410	1444	t
2569	446	1191	1444	t
2570	446	2	927	t
2571	446	2	1444	t
2572	446	928	1444	t
2573	446	1512	1401	t
2574	446	1191	1401	t
2575	446	928	1401	t
2576	446	2	1401	t
2577	446	1512	927	t
2578	446	1191	927	t
2579	446	1512	1444	t
2580	451	933	1444	t
2581	451	2	1444	t
2582	451	2	1	t
2583	451	2	932	t
2584	451	933	2	t
2585	451	2	2	t
2586	451	933	1	t
2587	451	933	1785	t
2588	451	2	1785	t
2589	467	949	1497	t
2590	467	949	1	t
2591	467	949	2	t
2592	467	949	1509	t
2593	14	2	1444	t
2594	14	2276	2	t
2595	14	1	1509	t
2596	14	2276	1509	t
2597	14	2276	1444	t
2598	14	1	1444	t
2599	14	2276	1	t
2600	14	2	1509	t
\.


--
-- Data for Name: productos; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.productos (id, nombre, descripcion, proveedor_id, producto_proveedor_id, categoria_id, temporada_id, coleccion_id, precio_venta, is_active, imagen_principal_url, empresa_id) FROM stdin;
1434	SHORT DEPORTIVO	SHORT DEPORTIVO ANTRACITA MUJER	1	\N	883	1	2015	150.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/f1a8a54ca7444eb89c5025e222a2bfe2.jpg	\N
324	QA Ciclo Completo Estados	Convertido	1	153	1	1	1	55.00	f	\N	\N
469	Gorras	\N	1	\N	666	1	87	70.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/fa46400d44b54cdcb5a11103e5d78697.jpg	\N
14	SAKURA	\N	1	\N	1	1	1	90.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/7b1666799b9440669c4f34e1f3284c20.jpg	\N
855	Dress After	\N	1	\N	655	1	2015	250.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/da6de28dc04c46b8a14b01a31f350245.jpg	\N
853	Chaqueta Denim 1c92491f	\N	1448	\N	1086	1787	1414	149.90	f	\N	\N
948	Chaqueta Denim c3c691e4	\N	1543	\N	1181	1882	1509	149.90	f	\N	\N
446	Pantalón pretty	Jeans con bordados	1	\N	1171	1	2015	115.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/8048a365b8174046b8f6343635beb821.jpg	\N
1	Morigami	\N	1	\N	1	1	1	100.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/63ffa916e2d74552882a1b6b058e0310.jpg	\N
1279	Chompa Andina aa997ffe	\N	1916	\N	1529	2257	1860	100.00	f	\N	\N
272	Producto QA Auditoria	Convertido desde propuesta de proveedor para auditoria	1	126	1	1	1	99.90	f	\N	\N
473	Chaqueta Denim 22e75069	\N	1028	\N	680	1363	1014	149.90	f	\N	\N
1436	Producto 28d1ee	Prenda de prueba	2075	\N	1712	2416	2018	399.00	t	\N	\N
1132	Chaqueta Denim 29e80fbf	\N	1769	\N	1382	2110	1713	149.90	f	\N	\N
851	Chaqueta Denim 1e624154	\N	1446	\N	1084	1785	1412	149.90	f	\N	\N
461	Chaqueta Denim 25437a6f	\N	1016	\N	668	1351	1002	149.90	f	\N	\N
355	Chaqueta Denim 2a5c9552	\N	868	\N	545	1201	876	149.90	f	\N	\N
940	Chaqueta Denim 2b6351c6	\N	1535	\N	1173	1874	1501	149.90	f	\N	\N
1135	Chaqueta Denim 2cf9cdb7	\N	1772	\N	1385	2113	1716	149.90	f	\N	\N
939	Chaqueta Denim 32552d32	\N	1534	\N	1172	1873	1500	149.90	f	\N	\N
458	Chaqueta Denim 3346c688	\N	1013	\N	665	1348	999	149.90	f	\N	\N
367	Chaqueta Denim 3770f276	\N	880	\N	557	1213	888	149.90	f	\N	\N
463	Chaqueta Denim 377ac1c9	\N	1018	\N	670	1353	1004	149.90	f	\N	\N
852	Chaqueta Denim 382ab4db	\N	1447	\N	1085	1786	1413	149.90	f	\N	\N
365	Chaqueta Denim 421c84aa	\N	878	\N	555	1211	886	149.90	f	\N	\N
457	Chaqueta Denim 43a81482	\N	1012	\N	664	1347	998	149.90	f	\N	\N
472	Chaqueta Denim 4477a021	\N	1027	\N	679	1362	1013	149.90	f	\N	\N
465	Chaqueta Denim 49080b4b	\N	1020	\N	672	1355	1006	149.90	f	\N	\N
379	Chaqueta Denim 4b8b0f60	\N	892	\N	569	1225	900	149.90	f	\N	\N
363	Chaqueta Denim 4bd088be	\N	876	\N	553	1209	884	149.90	f	\N	\N
1136	Chaqueta Denim 4df10f2b	\N	1773	\N	1386	2114	1717	149.90	f	\N	\N
475	Chaqueta Denim 53aa0a23	\N	1030	\N	682	1365	1016	149.90	f	\N	\N
453	Chaqueta Denim 55b81b1d	\N	1008	\N	660	1343	994	149.90	f	\N	\N
950	Chaqueta Denim 5f6a3251	\N	1545	\N	1183	1884	1511	149.90	f	\N	\N
471	Chaqueta Denim 61e45d64	\N	1026	\N	678	1361	1012	149.90	f	\N	\N
943	Chaqueta Denim 655d0f55	\N	1538	\N	1176	1877	1504	149.90	f	\N	\N
684	Chaqueta Denim 6859fcd3	\N	1279	\N	917	1618	1245	149.90	f	\N	\N
462	Chaqueta Denim 6b1bdab3	\N	1017	\N	669	1352	1003	149.90	f	\N	\N
447	Chaqueta Denim 70770165	\N	1002	\N	654	1337	988	149.90	f	\N	\N
364	Chaqueta Denim 85e3b477	\N	877	\N	554	1210	885	149.90	f	\N	\N
941	Chaqueta Denim 8a6b2a5f	\N	1536	\N	1174	1875	1502	149.90	f	\N	\N
1131	Chaqueta Denim 8b98d6ec	\N	1768	\N	1381	2109	1712	149.90	f	\N	\N
449	Chaqueta Denim 8bac4271	\N	1004	\N	656	1339	990	149.90	f	\N	\N
464	Chaqueta Denim 984cc384	\N	1019	\N	671	1354	1005	149.90	f	\N	\N
799	Chaqueta Denim 9d0d301a	\N	1394	\N	1032	1733	1360	149.90	f	\N	\N
455	Chaqueta Denim 9fb83135	\N	1010	\N	662	1345	996	149.90	f	\N	\N
454	Chaqueta Denim 9ff37315	\N	1009	\N	661	1344	995	149.90	f	\N	\N
466	Chaqueta Denim a0a504d8	\N	1021	\N	673	1356	1007	149.90	f	\N	\N
1138	Chaqueta Denim a1208af1	\N	1775	\N	1388	2116	1719	149.90	f	\N	\N
1134	Chaqueta Denim a401dd69	\N	1771	\N	1384	2112	1715	149.90	f	\N	\N
460	Chaqueta Denim adcd7e76	\N	1015	\N	667	1350	1001	149.90	f	\N	\N
448	Chaqueta Denim b82c0b36	\N	1003	\N	655	1338	989	149.90	f	\N	\N
468	Chaqueta Denim afb35648	\N	1023	\N	675	1358	1009	149.90	f	\N	\N
1133	Chaqueta Denim b35cd479	\N	1770	\N	1383	2111	1714	149.90	f	\N	\N
450	Chaqueta Denim b68c1bc2	\N	1005	\N	657	1340	991	149.90	f	\N	\N
362	Chaqueta Denim bda000d1	\N	875	\N	552	1208	883	149.90	f	\N	\N
452	Chaqueta Denim beddd3f6	\N	1007	\N	659	1342	993	149.90	f	\N	\N
938	Chaqueta Denim c161610f	\N	1533	\N	1171	1872	1499	149.90	f	\N	\N
474	Chaqueta Denim c37276ae	\N	1029	\N	681	1364	1015	149.90	f	\N	\N
456	Chaqueta Denim c4be23ec	\N	1011	\N	663	1346	997	149.90	f	\N	\N
1137	Chaqueta Denim d9badbc1	\N	1774	\N	1387	2115	1718	149.90	f	\N	\N
459	Chaqueta Denim de20e805	\N	1014	\N	666	1349	1000	149.90	f	\N	\N
354	Chaqueta Denim e5c8184b	\N	867	\N	544	1200	875	149.90	f	\N	\N
476	Chaqueta Denim ea240691	\N	1031	\N	683	1366	1017	149.90	f	\N	\N
850	Chaqueta Denim ee8178f6	\N	1445	\N	1083	1784	1411	149.90	f	\N	\N
361	Chaqueta Denim f15a7b4f	\N	874	\N	551	1207	882	149.90	f	\N	\N
445	Chaqueta Denim f1e3931f	\N	1000	\N	652	1335	986	149.90	f	\N	\N
586	Chaqueta Denim f6b48186	\N	1181	\N	810	1520	1147	149.90	f	\N	\N
887	Chaqueta Denim ff6a971f	\N	1482	\N	1120	1821	1448	149.90	f	\N	\N
650	Dummer blue	\N	1	\N	655	1	2015	149.90	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/29d4118faf504a24b3e8ca61ff59e124.jpg	\N
298	Polera unisex	Polera de algodón frescura y suavidad	1	139	883	1	87	49.90	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/0466975c701942b5b5a55c01ba065b8e.jpg	\N
1435	Abrigo color	Abrigo confeccionado para estar con estilo	1	\N	1387	1	2015	25.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/27539fc4b43c4bc68e473e2658790e32.jpg	\N
470	Chaqueta Denim	\N	1	\N	658	1	87	149.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/0de2b4840b3c4cf2b7f7c9d352ab77bc.jpg	\N
854	Cangurera	\N	1	\N	1087	1	87	100.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/8bf32d210c1048d7897d62be2c0c7882.jpg	\N
451	Gafas de sol	Estilo y protección para tus ojos	1	\N	666	1	2015	80.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/a9600090b64f4b4eb573e4a469fe5ea3.jpg	\N
942	Pantalón star	Cómodo y con estilo	1	\N	1171	1	87	100.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/b0694376c6de43e9bd036b61affa5b08.jpg	\N
467	Abrigo conf	\N	1	\N	1387	1	2015	250.00	t	https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/359683ac435842e38ed4bbc94b1cbb41.jpg	\N
1504	Chaqueta Denim 72c15306	\N	2167	\N	1804	2616	2140	149.90	t	\N	\N
1505	Chaqueta Denim e0a40b13	\N	2168	\N	1805	2617	2141	149.90	t	\N	\N
\.


--
-- Data for Name: productos_proveedor; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.productos_proveedor (id, proveedor_id, nombre, descripcion, disponibilidad, is_active, imagen_url, estado) FROM stdin;
139	1	QA Nuevo Flujo Sin Temporada	prueba	t	t	/api/v1/media/productos-proveedor/2c2aa7665698434495cbadef832c19ef.jpg	APROBADO
126	1	Producto QA Auditoria	Registro de prueba para auditoria PROVEEDOR	f	t	\N	APROBADO
127	1	Producto regresion CU15	check	t	t	\N	RECHAZADO
153	1	QA Ciclo Completo Estados	prueba aprobar/rechazar	t	t	\N	APROBADO
\.


--
-- Data for Name: promocion_productos; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.promocion_productos (promocion_id, producto_id) FROM stdin;
\.


--
-- Data for Name: promociones; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.promociones (id, nombre, porcentaje_descuento, fecha_inicio, fecha_fin, activa, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: proveedores; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.proveedores (id, razon_social, nombre_contacto, correo, telefono, is_active, empresa_id) FROM stdin;
1	Produccion ASRL	Andres Ibañez	cristelvicente981@gmail.com	75553135	t	\N
2167	Proveedor 72c15306	Ana	ana-72c15306@textiles.com	70011111	t	\N
2168	Proveedor e0a40b13	Ana	ana-e0a40b13@textiles.com	70011111	t	\N
892	Proveedor 4b8b0f60	Ana	ana-4b8b0f60@textiles.com	70011111	t	\N
1027	Proveedor 4477a021	Ana	ana-4477a021@textiles.com	70011111	f	\N
1245	Proveedor 05c8d4d9	Ana	ana-05c8d4d9@textiles.com	70011111	f	\N
1025	Proveedor 07930464	Ana	ana-07930464@textiles.com	70011111	f	\N
1450	Proveedor 118b5add	Ana	ana-118b5add@textiles.com	70011111	f	\N
1024	Proveedor 0bdc0b33	Ana	ana-0bdc0b33@textiles.com	70011111	f	\N
1769	Proveedor 29e80fbf	Ana	ana-29e80fbf@textiles.com	70011111	f	\N
1001	Proveedor 12bdaa56	Ana	ana-12bdaa56@textiles.com	70011111	f	\N
1006	Proveedor 1654bcf4	Ana	ana-1654bcf4@textiles.com	70011111	f	\N
1022	Proveedor 1c5297d9	Ana	ana-1c5297d9@textiles.com	70011111	f	\N
1448	Proveedor 1c92491f	Ana	ana-1c92491f@textiles.com	70011111	f	\N
868	Proveedor 2a5c9552	Ana	ana-2a5c9552@textiles.com	70011111	f	\N
1016	Proveedor 25437a6f	Ana	ana-25437a6f@textiles.com	70011111	f	\N
1013	Proveedor 3346c688	Ana	ana-3346c688@textiles.com	70011111	f	\N
1394	Proveedor 9d0d301a	Ana	ana-9d0d301a@textiles.com	70011111	f	\N
378	Proveedor 257957b7	Juan Pérez	proveedor-257957b7@textiles.com	70012345	f	\N
1482	Proveedor ff6a971f	Ana	ana-ff6a971f@textiles.com	70011111	f	\N
1537	Proveedor f9546c40	Ana	ana-f9546c40@textiles.com	70011111	f	\N
1009	Proveedor 9ff37315	Ana	ana-9ff37315@textiles.com	70011111	f	\N
1535	Proveedor 2b6351c6	Ana	ana-2b6351c6@textiles.com	70011111	f	\N
1534	Proveedor 32552d32	Ana	ana-32552d32@textiles.com	70011111	f	\N
1772	Proveedor 2cf9cdb7	Ana	ana-2cf9cdb7@textiles.com	70011111	f	\N
1028	Proveedor 22e75069	Ana	ana-22e75069@textiles.com	70011111	f	\N
1446	Proveedor 1e624154	Ana	ana-1e624154@textiles.com	70011111	f	\N
1018	Proveedor 377ac1c9	Ana	ana-377ac1c9@textiles.com	70011111	f	\N
1178	Proveedor 5d9b3026	Contacto de prueba	contacto@proveedor.com	70012345	f	\N
876	Proveedor 4bd088be	Ana	ana-4bd088be@textiles.com	70011111	f	\N
878	Proveedor 421c84aa	Ana	ana-421c84aa@textiles.com	70011111	f	\N
1447	Proveedor 382ab4db	Ana	ana-382ab4db@textiles.com	70011111	f	\N
1012	Proveedor 43a81482	Ana	ana-43a81482@textiles.com	70011111	f	\N
1020	Proveedor 49080b4b	Ana	ana-49080b4b@textiles.com	70011111	f	\N
880	Proveedor 3770f276	Ana	ana-3770f276@textiles.com	70011111	f	\N
1030	Proveedor 53aa0a23	Ana	ana-53aa0a23@textiles.com	70011111	f	\N
1773	Proveedor 4df10f2b	Ana	ana-4df10f2b@textiles.com	70011111	f	\N
1008	Proveedor 55b81b1d	Ana	ana-55b81b1d@textiles.com	70011111	f	\N
867	Proveedor e5c8184b	Ana	ana-e5c8184b@textiles.com	70011111	f	\N
1545	Proveedor 5f6a3251	Ana	ana-5f6a3251@textiles.com	70011111	f	\N
1010	Proveedor 9fb83135	Ana	ana-9fb83135@textiles.com	70011111	f	\N
1026	Proveedor 61e45d64	Ana	ana-61e45d64@textiles.com	70011111	f	\N
1538	Proveedor 655d0f55	Ana	ana-655d0f55@textiles.com	70011111	f	\N
1279	Proveedor 6859fcd3	Ana	ana-6859fcd3@textiles.com	70011111	f	\N
1017	Proveedor 6b1bdab3	Ana	ana-6b1bdab3@textiles.com	70011111	f	\N
1002	Proveedor 70770165	Ana	ana-70770165@textiles.com	70011111	f	\N
1536	Proveedor 8a6b2a5f	Ana	ana-8a6b2a5f@textiles.com	70011111	f	\N
1768	Proveedor 8b98d6ec	Ana	ana-8b98d6ec@textiles.com	70011111	f	\N
1004	Proveedor 8bac4271	Ana	ana-8bac4271@textiles.com	70011111	f	\N
877	Proveedor 85e3b477	Ana	ana-85e3b477@textiles.com	70011111	f	\N
874	Proveedor f15a7b4f	Ana	ana-f15a7b4f@textiles.com	70011111	f	\N
1775	Proveedor a1208af1	Ana	ana-a1208af1@textiles.com	70011111	f	\N
1771	Proveedor a401dd69	Ana	ana-a401dd69@textiles.com	70011111	f	\N
1015	Proveedor adcd7e76	Ana	ana-adcd7e76@textiles.com	70011111	f	\N
516	Proveedor da4775e8	Ana	ana-da4775e8@textiles.com	70011111	f	\N
1449	Proveedor d38c1f76	Ana	ana-d38c1f76@textiles.com	70011111	f	\N
1543	Proveedor c3c691e4	Ana	ana-c3c691e4@textiles.com	70011111	f	\N
1916	Proveedor aa997ffe	Ana	ana-aa997ffe@textiles.com	70011111	f	\N
1021	Proveedor a0a504d8	Ana	ana-a0a504d8@textiles.com	70011111	f	\N
1031	Proveedor ea240691	Ana	ana-ea240691@textiles.com	70011111	f	\N
1023	Proveedor afb35648	Ana	ana-afb35648@textiles.com	70011111	f	\N
1770	Proveedor b35cd479	Ana	ana-b35cd479@textiles.com	70011111	f	\N
1005	Proveedor b68c1bc2	Ana	ana-b68c1bc2@textiles.com	70011111	f	\N
891	Proveedor b7dce728	Ana	ana-b7dce728@textiles.com	70011111	f	\N
1019	Proveedor 984cc384	Ana	ana-984cc384@textiles.com	70011111	f	\N
875	Proveedor bda000d1	Ana	ana-bda000d1@textiles.com	70011111	f	\N
1007	Proveedor beddd3f6	Ana	ana-beddd3f6@textiles.com	70011111	f	\N
1533	Proveedor c161610f	Ana	ana-c161610f@textiles.com	70011111	f	\N
1029	Proveedor c37276ae	Ana	ana-c37276ae@textiles.com	70011111	f	\N
1011	Proveedor c4be23ec	Ana	ana-c4be23ec@textiles.com	70011111	f	\N
1014	Proveedor de20e805	Ana	ana-de20e805@textiles.com	70011111	f	\N
1774	Proveedor d9badbc1	Ana	ana-d9badbc1@textiles.com	70011111	f	\N
1445	Proveedor ee8178f6	Ana	ana-ee8178f6@textiles.com	70011111	f	\N
1003	Proveedor b82c0b36	Ana	ana-b82c0b36@textiles.com	70011111	f	\N
1000	Proveedor f1e3931f	Ana	ana-f1e3931f@textiles.com	70011111	f	\N
1181	Proveedor f6b48186	Ana	ana-f6b48186@textiles.com	70011111	f	\N
2075	Proveedor 28d1ee	Juan Pérez	proveedor-28d1ee@textiles.com	70012345	t	\N
\.


--
-- Data for Name: recepciones_mercaderia; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.recepciones_mercaderia (id, proveedor_id, sucursal_id, usuario_id, fecha_hora, observacion) FROM stdin;
1	1	1	2103	2026-09-13 03:43:22.081808+00	Recepcion QA auditoria CU15
2	1	1	2103	2026-09-13 03:43:53.020313+00	\N
3	1	1	2103	2026-09-13 03:46:25.008237+00	\N
4	1	1	2103	2026-09-13 03:57:04.793303+00	\N
5	1	1	2103	2026-09-13 03:58:01.7512+00	\N
\.


--
-- Data for Name: reserva_detalles; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.reserva_detalles (id, producto_variante_id, cantidad, estado, reserva_id) FROM stdin;
145	1440	1	PENDIENTE	34
255	1618	1	PENDIENTE	144
611	5	1	CANCELADA	413
609	5	1	VENCIDA	411
610	5	1	VENCIDA	412
612	1	1	PENDIENTE	414
406	1879	1	PENDIENTE	259
407	1881	1	PENDIENTE	260
408	1883	1	PENDIENTE	261
409	1885	1	PENDIENTE	262
410	1887	1	PREPARADA	263
411	1889	1	CANCELADA	264
412	1891	1	PENDIENTE	265
413	1893	1	PENDIENTE	266
208	1541	1	PENDIENTE	97
632	2807	1	ATENDIDA	431
\.


--
-- Data for Name: reservas; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.reservas (id, codigo_reserva, cliente_id, sucursal_id, fecha_reserva, hora_inicio, estado_general, fecha_creacion) FROM stdin;
431	RS-00431	4961	1652	2026-10-24	12:00:00	EN_ATENCION	2026-10-23 02:51:17.398569+00
259	RS-00259	4178	1258	2026-09-18	12:00:00	PENDIENTE	2026-09-17 02:31:58.458682+00
260	RS-00260	4179	1259	2026-09-18	12:00:00	PENDIENTE	2026-09-17 02:32:20.591923+00
261	RS-00261	4180	1260	2026-09-18	12:00:00	PENDIENTE	2026-09-17 02:32:40.310408+00
97	RS-00097	3658	1000	2026-09-18	12:00:00	PENDIENTE	2026-09-17 00:15:55.503577+00
262	RS-00262	4181	1261	2026-09-18	12:00:00	PENDIENTE	2026-09-17 02:32:58.423164+00
263	RS-00263	4182	1262	2026-09-18	12:00:00	PREPARADA	2026-09-17 02:33:18.537711+00
34	RS-00034	3536	910	2026-09-17	12:00:00	PENDIENTE	2026-09-16 23:37:04.022756+00
264	RS-00264	4184	1263	2026-09-18	12:00:00	CANCELADA	2026-09-17 02:33:42.0321+00
265	RS-00265	4185	1264	2026-09-18	12:00:00	PENDIENTE	2026-09-17 02:34:10.739763+00
266	RS-00266	4187	1265	2026-09-18	12:00:00	PENDIENTE	2026-09-17 02:34:31.447751+00
413	RS-00413	4608	1	2026-09-21	10:00:00	CANCELADA	2026-09-21 00:41:28.431001+00
411	RS-00411	4609	1	2026-09-21	10:00:00	VENCIDA	2026-09-20 19:34:37.479356+00
412	RS-00412	4609	1	2026-09-21	10:00:00	VENCIDA	2026-09-20 21:14:33.175398+00
144	RS-00144	3759	1063	2026-09-18	12:00:00	PENDIENTE	2026-09-17 00:44:24.508696+00
414	RS-00414	4608	1	2026-09-29	13:00:00	PENDIENTE	2026-09-29 11:38:04.981062+00
\.


--
-- Data for Name: stock_sucursal; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.stock_sucursal (id, sucursal_id, producto_variante_id, cantidad, stock_reservado) FROM stdin;
964	1258	1879	5	1
57	1	684	18	0
56	282	55	99	0
1597	1652	2807	5	1
106	430	883	13	0
107	431	884	8	0
726	1051	1592	5	0
113	437	890	10	0
114	438	891	20	0
115	437	891	5	0
117	440	893	20	0
116	439	892	15	0
118	441	894	13	0
727	1051	1593	5	0
37	1	6	0	0
120	443	896	21	0
728	1051	1594	5	0
623	961	1491	5	0
624	961	1492	5	0
625	961	1493	5	0
626	962	1494	5	0
627	962	1495	5	0
628	962	1496	5	0
629	963	1497	5	0
630	963	1498	5	0
631	963	1499	5	0
632	964	1500	5	0
34	1	3	2	0
35	1	4	1	0
633	964	1501	5	0
47	1	56	1	0
48	1	57	0	0
441	786	1312	10	0
132	455	908	20	0
133	454	908	5	0
634	964	1502	5	0
635	965	1503	5	0
324	682	1197	10	0
638	966	1506	5	0
729	1052	1595	5	0
730	1052	1596	5	0
731	1052	1597	5	0
732	1053	1598	5	0
733	1053	1599	5	0
734	1053	1600	5	0
735	1054	1601	5	0
736	1054	1602	5	0
737	1054	1603	5	0
738	1055	1604	5	0
572	910	1440	1	1
190	531	1015	5	0
191	532	1016	5	0
192	533	1017	5	0
193	534	1018	5	0
194	535	1019	5	0
195	536	1020	10	0
196	537	1021	5	0
197	538	1022	5	0
198	539	1023	10	0
199	540	1024	10	0
200	541	1025	10	0
201	542	1026	10	0
202	543	1027	10	0
203	544	1028	10	0
204	545	1029	10	0
205	546	1030	10	0
206	547	1031	3	0
207	548	1032	5	0
208	549	1033	0	0
209	550	1034	10	0
210	551	1035	10	0
211	552	1036	10	0
213	554	1038	10	0
214	555	1039	10	0
216	557	1041	10	0
217	558	1042	10	0
218	559	1043	5	0
219	560	1043	5	0
220	561	1044	10	0
221	562	1045	10	0
222	563	1046	10	0
741	1056	1607	5	0
742	1056	1608	5	0
743	1056	1609	5	0
748	1061	1614	5	0
749	1061	1615	5	0
750	1061	1616	5	0
752	1063	1618	1	1
967	1259	1882	5	0
966	1259	1881	5	1
1598	1653	2808	5	0
969	1260	1884	5	0
968	1260	1883	5	1
675	1000	1541	1	1
971	1261	1886	1	0
965	1258	1880	5	0
970	1261	1885	5	1
973	1262	1888	5	0
972	1262	1887	5	1
975	1263	1890	5	0
974	1263	1889	5	0
977	1264	1892	5	0
976	1264	1891	5	1
979	1265	1894	5	0
978	1265	1893	5	1
1274	1424	2172	0	0
1275	1424	2173	0	0
1563	1	2447	5	0
36	1	5	0	0
1564	1	2596	15	0
32	1	1	11	1
49	1	58	14	0
1565	1	2441	2	0
1566	1	2442	7	0
1567	1	2445	14	0
1568	1	2443	10	0
1569	1	2444	7	0
1570	1	2446	7	0
31	1	55	3	0
33	1	2	3	0
\.


--
-- Data for Name: sucursales; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.sucursales (id, nombre, ciudad_id, direccion, telefono, is_active, empresa_id) FROM stdin;
1	Mall ventura	1	Mall ventura	75553135	t	\N
282	Sucursal QA Otra	1	Test 123	70000000	f	\N
546	Sucursal adcd7e76	620	Av. Siempre Viva 123	70022222	f	\N
964	Sucursal 1c92491f	1043	Av. Siempre Viva 123	70022222	f	\N
562	Sucursal 53aa0a23	636	Av. Siempre Viva 123	70022222	f	\N
547	Sucursal 25437a6f	621	Av. Siempre Viva 123	70022222	f	\N
560	Sucursal 279ebbca	634	Otra Av. 456	70033333	f	\N
548	Sucursal 6b1bdab3	622	Av. Siempre Viva 123	70022222	f	\N
1055	Sucursal f9546c40	1134	Av. Siempre Viva 123	70022222	f	\N
559	Sucursal 22e75069	633	Av. Siempre Viva 123	70022222	f	\N
1053	Sucursal 2b6351c6	1132	Av. Siempre Viva 123	70022222	f	\N
1262	Sucursal 2cf9cdb7	1346	Av. Siempre Viva 123	70022222	f	\N
1052	Sucursal 32552d32	1131	Av. Siempre Viva 123	70022222	f	\N
544	Sucursal 3346c688	618	Av. Siempre Viva 123	70022222	f	\N
549	Sucursal 377ac1c9	623	Av. Siempre Viva 123	70022222	f	\N
963	Sucursal 382ab4db	1042	Av. Siempre Viva 123	70022222	f	\N
441	Sucursal 421c84aa	510	Av. Siempre Viva 123	70022222	f	\N
543	Sucursal 43a81482	617	Av. Siempre Viva 123	70022222	f	\N
558	Sucursal 4477a021	632	Av. Siempre Viva 123	70022222	f	\N
455	Sucursal 4b8b0f60	524	Av. Siempre Viva 123	70022222	f	\N
439	Sucursal 4bd088be	508	Av. Siempre Viva 123	70022222	f	\N
443	Sucursal 3770f276	512	Av. Siempre Viva 123	70022222	f	\N
961	Sucursal ee8178f6	1040	Av. Siempre Viva 123	70022222	f	\N
1263	Sucursal 4df10f2b	1347	Av. Siempre Viva 123	70022222	f	\N
539	Sucursal 55b81b1d	613	Av. Siempre Viva 123	70022222	f	\N
1063	Sucursal 5f6a3251	1142	Av. Siempre Viva 123	70022222	f	\N
557	Sucursal 61e45d64	631	Av. Siempre Viva 123	70022222	f	\N
1056	Sucursal 655d0f55	1135	Av. Siempre Viva 123	70022222	f	\N
533	Sucursal 70770165	607	Av. Siempre Viva 123	70022222	f	\N
440	Sucursal 85e3b477	509	Av. Siempre Viva 123	70022222	f	\N
1054	Sucursal 8a6b2a5f	1133	Av. Siempre Viva 123	70022222	f	\N
1258	Sucursal 8b98d6ec	1342	Av. Siempre Viva 123	70022222	f	\N
786	Sucursal 6859fcd3	865	Av. Siempre Viva 123	70022222	f	\N
550	Sucursal 984cc384	624	Av. Siempre Viva 123	70022222	f	\N
1256	Sucursal 9a855af9	1340	Otra Av. 1	70055555	f	\N
1267	Sucursal 9cb04bec	1351	Otra Av. 1	70055555	f	\N
910	Sucursal 9d0d301a	989	Av. Siempre Viva 123	70022222	f	\N
535	Sucursal 8bac4271	609	Av. Siempre Viva 123	70022222	f	\N
541	Sucursal 9fb83135	615	Av. Siempre Viva 123	70022222	f	\N
540	Sucursal 9ff37315	614	Av. Siempre Viva 123	70022222	f	\N
1265	Sucursal a1208af1	1349	Av. Siempre Viva 123	70022222	f	\N
1261	Sucursal a401dd69	1345	Av. Siempre Viva 123	70022222	f	\N
1424	Sucursal aa997ffe	1493	Av. Siempre Viva 123	70022222	f	\N
554	Sucursal afb35648	628	Av. Siempre Viva 123	70022222	f	\N
1260	Sucursal b35cd479	1344	Av. Siempre Viva 123	70022222	f	\N
536	Sucursal b68c1bc2	610	Av. Siempre Viva 123	70022222	f	\N
454	Sucursal b7dce728	523	Av. Siempre Viva 123	70022222	f	\N
534	Sucursal b82c0b36	608	Av. Siempre Viva 123	70022222	f	\N
438	Sucursal bda000d1	507	Av. Siempre Viva 123	70022222	f	\N
538	Sucursal beddd3f6	612	Av. Siempre Viva 123	70022222	f	\N
1051	Sucursal c161610f	1130	Av. Siempre Viva 123	70022222	f	\N
561	Sucursal c37276ae	635	Av. Siempre Viva 123	70022222	f	\N
679	Sucursal dea9fd01	758	Av. Siempre Viva 123	70012345	f	\N
563	Sucursal ea240691	637	Av. Siempre Viva 123	70022222	f	\N
430	Sucursal e5c8184b	499	Av. Siempre Viva 123	70022222	f	\N
1061	Sucursal c3c691e4	1140	Av. Siempre Viva 123	70022222	f	\N
965	Sucursal d38c1f76	1044	Av. Siempre Viva 123	70022222	f	\N
542	Sucursal c4be23ec	616	Av. Siempre Viva 123	70022222	f	\N
1264	Sucursal d9badbc1	1348	Av. Siempre Viva 123	70022222	f	\N
545	Sucursal de20e805	619	Av. Siempre Viva 123	70022222	f	\N
531	Sucursal f1e3931f	605	Av. Siempre Viva 123	70022222	f	\N
682	Sucursal f6b48186	761	Av. Siempre Viva 123	70022222	f	\N
1000	La brisas	1	4to anillo	70022222	t	\N
1620	centro comercial	1649	Av. Montevideo	75426459	t	\N
752	Centro comercial Norte	1	2do anillo	70022222	t	\N
1621	Comercial Cobija	1651	Av. pando	79545368	t	\N
437	Sucursal f15a7b4f	506	Av. Siempre Viva 123	70022222	f	\N
556	Sucursal 07930464	630	Av. Siempre Viva 123	70022222	f	\N
555	Sucursal 0bdc0b33	629	Av. Siempre Viva 123	70022222	f	\N
966	Sucursal 118b5add	1045	Av. Siempre Viva 123	70022222	f	\N
1259	Sucursal 29e80fbf	1343	Av. Siempre Viva 123	70022222	f	\N
431	Sucursal 2a5c9552	500	Av. Siempre Viva 123	70022222	f	\N
551	Sucursal 49080b4b	625	Av. Siempre Viva 123	70022222	f	\N
552	Sucursal a0a504d8	626	Av. Siempre Viva 123	70022222	f	\N
532	Sucursal 12bdaa56	606	Av. Siempre Viva 123	70022222	f	\N
537	Sucursal 1654bcf4	611	Av. Siempre Viva 123	70022222	f	\N
553	Sucursal 1c5297d9	627	Av. Siempre Viva 123	70022222	f	\N
962	Sucursal 1e624154	1041	Av. Siempre Viva 123	70022222	f	\N
1634	Sucursal 56f66d1e	1664	Otra Av. 1	70055555	t	\N
1652	Sucursal 72c15306	1682	Av. Siempre Viva 123	70022222	t	\N
1653	Sucursal e0a40b13	1683	Av. Siempre Viva 123	70022222	t	\N
\.


--
-- Data for Name: tallas; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.tallas (id, nombre, is_active, empresa_id) FROM stdin;
1	S	t	\N
2	M	t	\N
3	XL	t	\N
955	M-22e75069	f	\N
951	M-0bdc0b33	f	\N
933	M-1654bcf4	f	\N
1413	M-118b5add	f	\N
949	M-1c5297d9	f	\N
928	M-12bdaa56	f	\N
943	M-25437a6f	f	\N
947	M-49080b4b	f	\N
345	M-257957b7	f	\N
1407	M-1c92491f	f	\N
1786	M-29e80fbf	f	\N
797	M-2a5c9552	f	\N
957	M-53aa0a23	f	\N
1408	Talla-8195d28a	f	\N
807	M-421c84aa	f	\N
945	M-377ac1c9	f	\N
1505	M-2b6351c6	f	\N
1404	M-382ab4db	f	\N
929	M-70770165	f	\N
806	M-85e3b477	f	\N
1522	Talla-dfee75e1	f	\N
1409	Talla-059e07f8	f	\N
950	M-afb35648	f	\N
935	M-55b81b1d	f	\N
953	M-61e45d64	f	\N
944	M-6b1bdab3	f	\N
1502	M-32552d32	f	\N
1525	M-5f6a3251	f	\N
940	M-3346c688	f	\N
1790	M-a401dd69	f	\N
809	M-3770f276	f	\N
931	M-8bac4271	f	\N
821	M-4b8b0f60	f	\N
1784	M-8b98d6ec	f	\N
937	M-9fb83135	f	\N
936	M-9ff37315	f	\N
948	M-a0a504d8	f	\N
1514	M-655d0f55	f	\N
1347	M-9d0d301a	f	\N
932	M-b68c1bc2	f	\N
805	M-4bd088be	f	\N
1508	M-8a6b2a5f	f	\N
934	M-beddd3f6	f	\N
1788	M-b35cd479	f	\N
956	M-c37276ae	f	\N
1794	M-4df10f2b	f	\N
1225	M-6859fcd3	f	\N
1798	M-a1208af1	f	\N
344	S-257957b7	f	\N
1108	M-f6b48186	f	\N
796	M-e5c8184b	f	\N
938	M-c4be23ec	f	\N
1499	M-c161610f	f	\N
942	M-adcd7e76	f	\N
930	M-b82c0b36	f	\N
820	M-b7dce728	f	\N
804	M-bda000d1	f	\N
2276	L	t	\N
2277	40	t	\N
452	M-da4775e8	f	\N
2022	34	t	\N
2278	36	t	\N
1406	Talla-ddc20b66	f	\N
1448	M-ff6a971f	f	\N
1401	M-1e624154	f	\N
954	M-4477a021	f	\N
1521	M-c3c691e4	f	\N
1511	M-f9546c40	f	\N
946	M-984cc384	f	\N
1792	M-2cf9cdb7	f	\N
939	M-43a81482	f	\N
1796	M-d9badbc1	f	\N
1410	M-d38c1f76	f	\N
927	M-f1e3931f	f	\N
1412	Talla-065dae11	f	\N
941	M-de20e805	f	\N
958	M-ea240691	f	\N
1403	Talla-06b5a535	f	\N
1398	M-ee8178f6	f	\N
803	M-f15a7b4f	f	\N
1513	Talla-36a9ae29	f	\N
1523	Talla-24891113	f	\N
1516	Talla-22972cfc	f	\N
1793	Talla-08525170	f	\N
1402	Talla-149429c4	f	\N
1415	Talla-2421d8c0	f	\N
1504	Talla-3f44e902	f	\N
1797	Talla-51f29a70	f	\N
1501	Talla-58c42530	f	\N
1507	Talla-591a5a03	f	\N
1791	Talla-6c225a08	f	\N
1405	Talla-71a4bf1a	f	\N
1799	Talla-73efaea4	f	\N
1503	Talla-5293a550	f	\N
1509	Talla-79a4092b	f	\N
1787	Talla-db7e582e	f	\N
1785	Talla-cb7951d7	f	\N
1411	Talla-b68e9196	f	\N
1795	Talla-af60b00e	f	\N
1510	Talla-9fd161f1	f	\N
1414	Talla-b4092025	f	\N
1506	Talla-6d6bcdd9	f	\N
1515	Talla-85cc9de0	f	\N
1789	Talla-90e2bddb	f	\N
1400	Talla-c1c9fb65	f	\N
1399	Talla-cd1361e6	f	\N
1500	Talla-e38c5c91	f	\N
1512	32	t	\N
2023	30	t	\N
1191	38	t	\N
952	Xs	t	\N
2301	S-28d1ee	t	\N
2470	M-72c15306	t	\N
2471	M-e0a40b13	t	\N
\.


--
-- Data for Name: temporadas; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.temporadas (id, nombre, fecha_inicio, fecha_fin, is_active, empresa_id) FROM stdin;
1	Primavera-Verano 2026	2026-09-01	2026-09-30	t	\N
2616	Temporada 72c15306	2026-01-01	2026-03-31	t	\N
1225	Temporada 4b8b0f60	2026-01-01	2026-03-31	f	\N
1733	Temporada 9d0d301a	2026-01-01	2026-03-31	f	\N
1335	Temporada f1e3931f	2026-01-01	2026-03-31	f	\N
1224	Temporada b7dce728	2026-01-01	2026-03-31	f	\N
2116	Temporada a1208af1	2026-01-01	2026-03-31	f	\N
2110	Temporada 29e80fbf	2026-01-01	2026-03-31	f	\N
2115	Temporada d9badbc1	2026-01-01	2026-03-31	f	\N
1882	Temporada c3c691e4	2026-01-01	2026-03-31	f	\N
1821	Temporada ff6a971f	2026-01-01	2026-03-31	f	\N
1884	Temporada 5f6a3251	2026-01-01	2026-03-31	f	\N
1789	Temporada 118b5add	2026-01-01	2026-03-31	f	\N
1877	Temporada 655d0f55	2026-01-01	2026-03-31	f	\N
1788	Temporada d38c1f76	2026-01-01	2026-03-31	f	\N
2113	Temporada 2cf9cdb7	2026-01-01	2026-03-31	f	\N
2109	Temporada 8b98d6ec	2026-01-01	2026-03-31	f	\N
1786	Temporada 382ab4db	2026-01-01	2026-03-31	f	\N
1784	Temporada ee8178f6	2026-01-01	2026-03-31	f	\N
1785	Temporada 1e624154	2026-01-01	2026-03-31	f	\N
1211	Temporada 421c84aa	2026-01-01	2026-03-31	f	\N
1520	Temporada f6b48186	2026-01-01	2026-03-31	f	\N
2111	Temporada b35cd479	2026-01-01	2026-03-31	f	\N
1787	Temporada 1c92491f	2026-01-01	2026-03-31	f	\N
2114	Temporada 4df10f2b	2026-01-01	2026-03-31	f	\N
1336	Temporada 12bdaa56	2026-01-01	2026-03-31	f	\N
1337	Temporada 70770165	2026-01-01	2026-03-31	f	\N
1338	Temporada b82c0b36	2026-01-01	2026-03-31	f	\N
1339	Temporada 8bac4271	2026-01-01	2026-03-31	f	\N
2112	Temporada a401dd69	2026-01-01	2026-03-31	f	\N
1343	Temporada 55b81b1d	2026-01-01	2026-03-31	f	\N
1876	Temporada f9546c40	2026-01-01	2026-03-31	f	\N
1618	Temporada 6859fcd3	2026-01-01	2026-03-31	f	\N
741	Temporada da4775e8	2026-01-01	2026-03-31	f	\N
1584	Temporada 05c8d4d9	2026-01-01	2026-03-31	f	\N
1340	Temporada b68c1bc2	2026-01-01	2026-03-31	f	\N
1357	Temporada 1c5297d9	2026-01-01	2026-03-31	f	\N
1875	Temporada 8a6b2a5f	2026-01-01	2026-03-31	f	\N
1873	Temporada 32552d32	2026-01-01	2026-03-31	f	\N
1874	Temporada 2b6351c6	2026-01-01	2026-03-31	f	\N
1872	Temporada c161610f	2026-01-01	2026-03-31	f	\N
2617	Temporada e0a40b13	2026-01-01	2026-03-31	t	\N
1213	Temporada 3770f276	2026-01-01	2026-03-31	f	\N
1210	Temporada 85e3b477	2026-01-01	2026-03-31	f	\N
1341	Temporada 1654bcf4	2026-01-01	2026-03-31	f	\N
1345	Temporada 9fb83135	2026-01-01	2026-03-31	f	\N
1356	Temporada a0a504d8	2026-01-01	2026-03-31	f	\N
119	Temporada 0da4b08f	2026-01-01	2026-03-31	f	\N
1349	Temporada de20e805	2026-01-01	2026-03-31	f	\N
1347	Temporada 43a81482	2026-01-01	2026-03-31	f	\N
1346	Temporada c4be23ec	2026-01-01	2026-03-31	f	\N
1351	Temporada 25437a6f	2026-01-01	2026-03-31	f	\N
1348	Temporada 3346c688	2026-01-01	2026-03-31	f	\N
1355	Temporada 49080b4b	2026-01-01	2026-03-31	f	\N
1353	Temporada 377ac1c9	2026-01-01	2026-03-31	f	\N
1358	Temporada afb35648	2026-01-01	2026-03-31	f	\N
1354	Temporada 984cc384	2026-01-01	2026-03-31	f	\N
1361	Temporada 61e45d64	2026-01-01	2026-03-31	f	\N
1352	Temporada 6b1bdab3	2026-01-01	2026-03-31	f	\N
1360	Temporada 07930464	2026-01-01	2026-03-31	f	\N
1365	Temporada 53aa0a23	2026-01-01	2026-03-31	f	\N
1366	Temporada ea240691	2026-01-01	2026-03-31	f	\N
1200	Temporada e5c8184b	2026-01-01	2026-03-31	f	\N
1209	Temporada 4bd088be	2026-01-01	2026-03-31	f	\N
1342	Temporada beddd3f6	2026-01-01	2026-03-31	f	\N
1208	Temporada bda000d1	2026-01-01	2026-03-31	f	\N
1207	Temporada f15a7b4f	2026-01-01	2026-03-31	f	\N
1201	Temporada 2a5c9552	2026-01-01	2026-03-31	f	\N
1364	Temporada c37276ae	2026-01-01	2026-03-31	f	\N
1363	Temporada 22e75069	2026-01-01	2026-03-31	f	\N
1362	Temporada 4477a021	2026-01-01	2026-03-31	f	\N
1359	Temporada 0bdc0b33	2026-01-01	2026-03-31	f	\N
1344	Temporada 9ff37315	2026-01-01	2026-03-31	f	\N
1350	Temporada adcd7e76	2026-01-01	2026-03-31	f	\N
538	Temporada 257957b7	2026-01-01	2026-03-31	f	\N
539	Otoño	2026-06-01	2026-08-31	t	\N
2257	Invierno	2026-01-01	2026-03-31	t	\N
2416	Temporada db2105ac	2026-01-01	2026-03-31	t	\N
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.usuarios (id, nombre, correo, password_hash, rol, is_active, created_at, sucursal_id, proveedor_id, telefono, empresa_id) FROM stdin;
2098	Test Final Happy	test-final-happy@fashionstore.com	$2b$12$pDgMiw0BKQbLG5mGVmLTtuHkclSLuo1B6FIfLvLYa61q1cYshtGYu	ENCARGADO_SUCURSAL	f	2026-09-13 00:59:17.094156+00	1	\N	\N	\N
2099	Test Validacion	test-validacion@fashionstore.com	$2b$12$lKTY1eVHdyxzeu9VNNzTTeFpRu1JUGt/czQffrD7fOEgRs8pZWw.2	ENCARGADO_SUCURSAL	f	2026-09-13 01:31:19.629033+00	1	\N	\N	\N
2661	QA CU16 Encargado	qa-cu16-encargado@fashionstore.com	$2b$12$mH5IxSlagchaZYJGx75Zv.afoMOcjoT4Gt8Hf6apTC23IoUdZyf1y	ENCARGADO_SUCURSAL	t	2026-09-13 20:21:24.946538+00	1	\N	\N	\N
2101	QA Auditoria Proveedor	qa-auditoria-proveedor@fashionstore.com	$2b$12$HBBoh9WawBgYVEeFO5NyTOccLP3JWB1Okb8JrTs8bwhoNcxQzVvs6	PROVEEDOR	t	2026-09-13 03:21:55.440206+00	\N	1	\N	\N
2102	QA Auditoria Proveedor B	qa-auditoria-proveedor-b@fashionstore.com	$2b$12$lMtlc7.d8BeZJ3C44sZNz.QBfCtXJjc.fCRGMXc6o.40NfPv4wC0u	PROVEEDOR	t	2026-09-13 03:23:34.004306+00	\N	378	\N	\N
2044	Test Encargado Rename	test-encargado-rename@fashionstore.com	$2b$12$p84f43rlBkrcRipS7keKievADKudulZ23/U0ZLXWV9NPQndMZ1SyW	ENCARGADO_SUCURSAL	f	2026-09-12 22:59:33.460324+00	1	\N	\N	\N
2103	QA Auditoria Encargado CU15	qa-auditoria-encargado-cu15@fashionstore.com	$2b$12$0NjKA2oeYIfAKnAJvezCtuDvMgg5pUXFH/Jx0QtZBoaRnkpHvjNRm	ENCARGADO_SUCURSAL	t	2026-09-13 03:42:20.472038+00	1	\N	\N	\N
2104	QA Cliente CU15	qa-cliente-cu15@fashionstore.com	$2b$12$TtfsFkxSGSdtbP1UERlA8.0uZRm3UWRd1EyCJx.s7xey7YNxt2XW6	CLIENTE	t	2026-09-13 03:45:51.406854+00	\N	\N	\N	\N
2662	QA CU16 Cliente	qa-cu16-cliente@fashionstore.com	$2b$12$4H6E0MIsHE1Q.5NbUo.rzeh1jS5mIs5HmO2zTo5EMmjEu.Urwjp6i	CLIENTE	t	2026-09-13 20:24:37.541152+00	\N	\N	\N	\N
1909	Test Encargado Nav	test-encargado-nav@fashionstore.com	$2b$12$jRHVOobTqgHyJ6.edf65EuuFjvCEZ50txltDKGVSqdi7L3pKNM.ou	ENCARGADO_SUCURSAL	f	2026-09-12 21:57:55.992501+00	1	\N	\N	\N
3657	Usuario de prueba	test-1a3aa8d21a@fashionstore.com	$2b$12$wnwAoxoj8dcoEBh3VYPC6eLILH9LENT43W5AjYpLpFaVS4CdCZnC2	CLIENTE	t	2026-09-17 00:15:52.053103+00	\N	\N	\N	\N
1911	Test Encargado Inv	test-encargado-inv@fashionstore.com	$2b$12$6c6/ul.vMzTkG7yePycI/ei/bNMTKHGjKBVr0P4C7atz8leBAgsli	ENCARGADO_SUCURSAL	f	2026-09-12 22:25:55.158224+00	1	\N	\N	\N
2669	Usuario de prueba	test-82cdcf9576@fashionstore.com	$2b$12$U4iiN4vDFFSPyK9BHcMmKOnDrbJ5WwlloWUckngCyFXYsFErFMSB2	ENCARGADO_SUCURSAL	t	2026-09-13 20:35:01.924677+00	430	\N	\N	\N
1190	Usuario de prueba	test-dd0e1f9a3e@fashionstore.com	$2b$12$LS0MFZaFKFta9bJPNsDfDOkTleXzJcuuA9UcwBTygQ0QPo8TDiVIW	ADMINISTRADOR	t	2026-09-12 05:05:22.399911+00	\N	\N	\N	\N
2670	Usuario de prueba	test-047f1b6a71@fashionstore.com	$2b$12$pGYg1FRtiHaL7MhwOezx.OVOKheLG4sLac6mJaClPru264ZIfPRs2	ENCARGADO_SUCURSAL	t	2026-09-13 20:35:16.93889+00	431	\N	\N	\N
2676	Usuario de prueba	test-6ef6eada3d@fashionstore.com	$2b$12$TVoX.Kn2mmN0OErdEXkXxe4V6Ic2hWDjzblgP4fOsr8Ctfa/dAmrO	ENCARGADO_SUCURSAL	t	2026-09-13 20:37:00.871306+00	437	\N	\N	\N
2677	Usuario de prueba	test-a8d5262791@fashionstore.com	$2b$12$cMNt9ynNKey.uBon1vOqJ.VIaJpWq98ll6ug7vyfSB6FlMlrOhVe2	ENCARGADO_SUCURSAL	t	2026-09-13 20:37:10.111769+00	438	\N	\N	\N
2678	Usuario de prueba	test-dec392d668@fashionstore.com	$2b$12$oFNdwKqfXPrraCmFS4Y8fe54Qa3FJXLxExi0g67SaVc8MhdEhQMvW	ENCARGADO_SUCURSAL	t	2026-09-13 20:37:24.026002+00	439	\N	\N	\N
2679	Usuario de prueba	test-dad0854c49@fashionstore.com	$2b$12$aXAQqqZVwdJq/6QkG5IOce06ENelmvfuBACRt45/MElSh/f.A3O3m	ENCARGADO_SUCURSAL	t	2026-09-13 20:37:33.26277+00	440	\N	\N	\N
2680	Usuario de prueba	test-32f87a827b@fashionstore.com	$2b$12$6YXXSglZPhtCRo1ZakZBvus.zb2GoTH7QRJ9Oxs13tMZDOCCJjzwS	ENCARGADO_SUCURSAL	t	2026-09-13 20:37:47.589285+00	441	\N	\N	\N
1906	Eliana	elianaalv@gamil.com	$2b$12$ilOMM7EnJCYYkG5FUhWjZ.J7J/mbgdECTsEcZsngujoZWSw2nEehC	ENCARGADO_SUCURSAL	t	2026-09-12 21:05:31.152169+00	1	\N	\N	\N
2682	Usuario de prueba	test-63a60cc0b4@fashionstore.com	$2b$12$kxCjBGtM6dKDyH3TgOz42O2KHPwVjW272vgVGmVqDMqRBDiubbNmW	ENCARGADO_SUCURSAL	t	2026-09-13 20:38:15.317262+00	443	\N	\N	\N
1907	Test Encargado QA	test-encargado-qa@fashionstore.com	$2b$12$yw104ebXChV2cRs0x71qwuklsNskvqPjyuO3tPBVBCmZoF87UC1l6	ENCARGADO_SUCURSAL	f	2026-09-12 21:26:27.411826+00	1	\N	\N	\N
149	Usuario de prueba	test-4c686a2140@fashionstore.com	$2b$12$p/FdPaVteVUrnC.lddJW3O.dWx.ANwakQYmyoI6SqjBWqotMKpBNO	ADMINISTRADOR	t	2026-09-11 01:42:56.058276+00	\N	\N	\N	\N
2936	Usuario de prueba	test-b365f7d797@fashionstore.com	$2b$12$sRcPNltewmgHU2TBQBGCfeJacZnvWFI9hcJuV6b5j6BYZRk.siS/C	CLIENTE	t	2026-09-16 04:17:08.718719+00	\N	\N	\N	\N
2937	Usuario de prueba	test-d7a33d9cb0@fashionstore.com	$2b$12$sqm/5VUDlo6xrlK5du.NbOHX9Ye/VES/LxBRVTBhEL3WZtGj19plK	CLIENTE	t	2026-09-16 04:17:22.651483+00	\N	\N	\N	\N
2938	Usuario de prueba	test-354f7a23f8@fashionstore.com	$2b$12$uo53nZBAgdWvuY5inyYCo.6eNe5u8BXqwzcgBRcmWniptASvmfpR6	CLIENTE	t	2026-09-16 04:17:30.552779+00	\N	\N	\N	\N
2939	Usuario de prueba	test-fcf55f5a81@fashionstore.com	$2b$12$Xf49iOEJfpwhD7xAzHZ/feP0PVdUiHTgzXrxBekd6WV9Asz7TZEGi	CLIENTE	t	2026-09-16 04:17:43.321938+00	\N	\N	\N	\N
2940	Usuario de prueba	test-0071d28c52@fashionstore.com	$2b$12$AyI3IIyqHLXmJSSDdFTzWOspAurO0yAN8mivwgfruX27a2DeRLo/6	CLIENTE	t	2026-09-16 04:17:51.121938+00	\N	\N	\N	\N
2697	Usuario de prueba	test-81891d8a4d@fashionstore.com	$2b$12$ZdLglIfcHEHjrGV744mtt.6wwMABFYYqSCQF3xths39wYC316T2Em	ENCARGADO_SUCURSAL	t	2026-09-13 20:42:43.39694+00	455	\N	\N	\N
2941	Usuario de prueba	test-187489b051@fashionstore.com	$2b$12$XFwHbT5PsQgds41fNEKLjefr5AtBz3T/YLZ1T1q3ZfUnkNrRHPlga	CLIENTE	t	2026-09-16 04:18:03.483369+00	\N	\N	\N	\N
2943	Usuario de prueba	test-1486d7351d@fashionstore.com	$2b$12$W8KgPyvdKpVeeYeQplX5ieJp/ionfvVso0Z6X.sT72r6jEUu80T.W	CLIENTE	t	2026-09-16 04:18:16.381565+00	\N	\N	\N	\N
2944	Usuario de prueba	test-c21f41cf15@fashionstore.com	$2b$12$qmVUiNMfF7gf0KZyaqTZiexg/yqiRuDeNhohyo8HB/vc.Niq2FlVO	CLIENTE	t	2026-09-16 04:18:28.064069+00	\N	\N	\N	\N
2095	Test Encargado Final A	test-encargado-final-a@fashionstore.com	$2b$12$De/tnw8cCL0ANcKYol96muuZyjMF7.RnznYnzXB55qOjuSnasdP4W	ENCARGADO_SUCURSAL	f	2026-09-12 23:10:31.297988+00	1	\N	\N	\N
2096	Test Encargado Final B	test-encargado-final-b@fashionstore.com	$2b$12$FWWfZ9oH.pQgTbc1YTbZLu3OePdRWLNRBQFW9hEZMuc2yqbv1S1VO	ENCARGADO_SUCURSAL	f	2026-09-12 23:10:33.80248+00	282	\N	\N	\N
2097	Test Encargado Jerarquia	test-encargado-jerarquia@fashionstore.com	$2b$12$OytOmzvlg7jfDOz8FgZx.OCSCV0DTf.7nTVc0hWgHZo20OeMKzRu6	ENCARGADO_SUCURSAL	f	2026-09-12 23:56:06.240522+00	1	\N	\N	\N
2945	Usuario de prueba	test-78233944aa@fashionstore.com	$2b$12$dR5wPBX3QuBnR7zo9b.Vw.qkuB7.rEHPf/U9P0KtlTF12zst.5EN.	CLIENTE	t	2026-09-16 04:18:41.310555+00	\N	\N	\N	\N
2947	Usuario de prueba	test-224fcdd6d4@fashionstore.com	$2b$12$hwdq9hcwXyMyI8Kau0LhWuFa8oy.5um7GZ4yhlC4diE5oIYTdQtNe	CLIENTE	t	2026-09-16 04:18:54.489605+00	\N	\N	\N	\N
2948	Usuario de prueba	test-f1a0bfa658@fashionstore.com	$2b$12$RfmnzNB8omqI3NZuC.uz1e2S3nJcX8IEIiPpgcot2JYPWxTqT7wL6	CLIENTE	t	2026-09-16 04:19:08.773929+00	\N	\N	\N	\N
2949	Usuario de prueba	test-f36515c004@fashionstore.com	$2b$12$ukRNFGBIkkCxkc20Zck0IuUHUExOEgUQltsZv0A2fupkay935FySS	CLIENTE	t	2026-09-16 04:19:22.426451+00	\N	\N	\N	\N
2950	Usuario de prueba	test-a02710250f@fashionstore.com	$2b$12$o9s6jwjWG7Cy//0MukX2SeGjuqmBgcixh66vsAlGZgYgE4yXyTs7e	CLIENTE	t	2026-09-16 04:19:33.927614+00	\N	\N	\N	\N
2951	Usuario de prueba	test-da65bc56ae@fashionstore.com	$2b$12$CXxbQ4x.QrS2WDasJFjBTeRQJUzNRcfBFpdEnwUqrRNiXXhy0qR.S	CLIENTE	t	2026-09-16 04:19:44.911923+00	\N	\N	\N	\N
2952	Usuario de prueba	test-58a355aab1@fashionstore.com	$2b$12$bGOFsOtj4RW0yMErKscWY.jD9XXNmo7nxactJ53CNkbjjiI1.H/Ae	CLIENTE	t	2026-09-16 04:19:55.11914+00	\N	\N	\N	\N
2953	Usuario de prueba	test-5d82d9630d@fashionstore.com	$2b$12$vmrlw6t1.OmSYUySYfVSaeNkbTBpMlE2dUxgQU8clPdpPe0/Q5Z46	CLIENTE	t	2026-09-16 04:20:05.593381+00	\N	\N	\N	\N
2954	Usuario de prueba	test-88ffd1d87c@fashionstore.com	$2b$12$veiGuX8eKXMv4xnXcEtqJOqO4BbtZsNiiNc./cn9dNj9NQpBwxAeG	CLIENTE	t	2026-09-16 04:20:16.380783+00	\N	\N	\N	\N
2955	Usuario de prueba	test-7940770313@fashionstore.com	$2b$12$6NiBLbVBrVyf8JaaMitvyuvXBeGru9pdA1MjI120ii98.pbDAe6ha	CLIENTE	t	2026-09-16 04:20:31.198158+00	\N	\N	\N	\N
2956	Usuario de prueba	test-3997cf28cd@fashionstore.com	$2b$12$Hb/Zs/ViFBcaJcsSPzBaC.rKS60FyZLkkuTDOP6EO1C7UVX4MeumW	CLIENTE	t	2026-09-16 04:20:44.581962+00	\N	\N	\N	\N
2957	Usuario de prueba	test-930b2b757b@fashionstore.com	$2b$12$iGfyFZWzFm.FyBwlQmCmO.5QDkq6ntMNrB6tTCdq8u5zXi1os8OKe	CLIENTE	t	2026-09-16 04:20:57.047605+00	\N	\N	\N	\N
2958	Usuario de prueba	test-03debeb64f@fashionstore.com	$2b$12$t.G4sAfApvL73TrqD9N/ieTtLxe5Z3Q0/PxI6WVUQJY5Tvw7UPPlK	CLIENTE	t	2026-09-16 04:21:09.541286+00	\N	\N	\N	\N
2959	Usuario de prueba	test-751637c6be@fashionstore.com	$2b$12$JO/ouUa1BMM5FJ2NpEykBeHufxPUNmlh.Qgd6Yceb0dWowEt.T2ra	CLIENTE	t	2026-09-16 04:21:24.451816+00	\N	\N	\N	\N
2960	Usuario de prueba	test-3a16261c73@fashionstore.com	$2b$12$Zzs1IXZRE3Eb800A8EhYdewmOkagp75Qxt/CemVGrMFszO/D0.cIK	CLIENTE	t	2026-09-16 04:21:39.777018+00	\N	\N	\N	\N
2961	Usuario de prueba	test-ba6240fe0d@fashionstore.com	$2b$12$vZRUPQMNmObKnsVRZytVWev/qkDZg6kpC34/.PrTCT4DZ5Z1CO8si	CLIENTE	t	2026-09-16 04:21:51.194623+00	\N	\N	\N	\N
2962	Usuario de prueba	test-838afc9f41@fashionstore.com	$2b$12$9RJruU7gSMYsb.htfYDuBeQEQrn8Z1YZEgynkJu3vAmCbr2dYCtdS	CLIENTE	t	2026-09-16 04:22:01.593734+00	\N	\N	\N	\N
2963	Usuario de prueba	test-96377f8989@fashionstore.com	$2b$12$G9EM.ii8/Pai41DLgJYjqegUBedoK3anZCV05dWZUGmC9fHGpGNh.	CLIENTE	t	2026-09-16 04:22:11.755672+00	\N	\N	\N	\N
2964	Usuario de prueba	test-78958a1d1a@fashionstore.com	$2b$12$jLWWkxpk7ib1dAWuNxKZYOD.DXOf7t2P66ynmFWwkokacpqZtzJZu	CLIENTE	t	2026-09-16 04:22:22.290057+00	\N	\N	\N	\N
2965	Usuario de prueba	test-c3116904c3@fashionstore.com	$2b$12$3OPJ5ZTnGo15Yko6EbjS/us7rNaUN2i10iCLW1lgKCuK7CDC2eCbK	CLIENTE	t	2026-09-16 04:22:35.749205+00	\N	\N	\N	\N
2966	Usuario de prueba	test-53e264f5ac@fashionstore.com	$2b$12$381.9UFIYTy35tPRDZLNhu0OaL.wuVCp0ZIUtB4gJQJGrSEQlqS5y	CLIENTE	t	2026-09-16 04:22:47.547569+00	\N	\N	\N	\N
3658	Usuario de prueba	test-398021d6d1@fashionstore.com	$2b$12$omowgUx61gyQwDNsLzj8duAoCGK/RBrkQLFR.QfNR1cz6Z7rWYt56	CLIENTE	t	2026-09-17 00:15:53.700121+00	\N	\N	\N	\N
3390	Usuario de prueba	test-c092a1cef4@fashionstore.com	$2b$12$iIu4QEiLScEFKls8gmrFkeLbSO.FIZbRrw3ytGR7KaVRL7T0jHZiO	CLIENTE	t	2026-09-16 21:18:32.48965+00	\N	\N	\N	\N
4961	Usuario de prueba	test-84fa331b68@fashionstore.com	$2b$12$3v4/kGNelLM1nJsM.n5vXuckoPEwvqo4oMbJ1oRKvZgJQfwg85BQu	CLIENTE	t	2026-10-23 02:50:54.458191+00	\N	\N	\N	\N
4962	Usuario de prueba	test-7e60e0149b@fashionstore.com	$2b$12$5OEAGh1oztj3q4XLFhdRueXA6K3jW5EEDGfSHycU6PLpLx2LRXG9m	CLIENTE	t	2026-10-23 02:51:07.479237+00	\N	\N	\N	\N
4964	Usuario de prueba	test-9d8fab7564@fashionstore.com	$2b$12$ghY6FrKxlbexCJhdRZFCpO7dls5vGjhqUP/Oq41qUboAjUYqMs6pi	ENCARGADO_SUCURSAL	t	2026-10-23 02:51:14.961966+00	1653	\N	\N	\N
3739	Usuario de prueba	test-0b8dde8830@fashionstore.com	$2b$12$qG0iZqXtgOmBv8NZX0oW.u16FPmsMPxCMdJSKNUAoQggsoiW1Cz0O	CLIENTE	t	2026-09-17 00:37:20.660917+00	\N	\N	\N	\N
3742	Usuario de prueba	test-ab8afe025a@fashionstore.com	$2b$12$8yc6PwiQgM5wh4wzb/Wjo..8pj133000Evdyxq.jXJaRQtM1mJHWO	CLIENTE	t	2026-09-17 00:37:54.516049+00	\N	\N	\N	\N
3745	Usuario de prueba	test-cc9e89cf7c@fashionstore.com	$2b$12$vbzNIGpXQB9oGiZEEaAbGOIFs04QNR7wnJLFlft5wvuiGJVIyIy6G	CLIENTE	t	2026-09-17 00:38:29.723149+00	\N	\N	\N	\N
4608	Maria	maria@gmail.com	$2b$12$xvO7QOEeDVeJ1ISkJNZtnuoK7/Rl7v.fiA4w5/R2LFCXy76Izxn/6	CLIENTE	t	2026-09-20 17:02:16.60057+00	\N	\N	78568111	\N
3617	Usuario de prueba	test-d0886d097b@fashionstore.com	$2b$12$Vuq6ZEnGWuhm/ua3YVjoHuufXkilBFEGl4XXtkabHsAVjBwPDsrcq	CLIENTE	t	2026-09-16 23:58:01.756426+00	\N	\N	\N	\N
3755	Usuario de prueba	test-e597df6cdb@fashionstore.com	$2b$12$2JkTDMmfBFnUTx7xU.gSyemgtDPLkwuc8vl4oX6lxiy2zV.Ju.pLy	CLIENTE	t	2026-09-17 00:42:43.962806+00	\N	\N	\N	\N
3620	Usuario de prueba	test-359abfe862@fashionstore.com	$2b$12$zf4egTCzbgHUe6VtjyOeCOUg2eGE6h5SFhCFhrlALNrW/pkOnv1vq	CLIENTE	t	2026-09-16 23:58:34.553673+00	\N	\N	\N	\N
4609	Vicente	vicentelimacristelaracely@gmail.com	$2b$12$doFIl6CXjkiZQKLEXX3W.uMTUITB8PI56cZKL1bjTcxB2kLvHxlIm	CLIENTE	t	2026-09-20 19:02:10.474855+00	\N	\N	75553135	\N
3623	Usuario de prueba	test-741acf5f3c@fashionstore.com	$2b$12$e2uObhAPuEQ.ZVOv7ldZzeFqOohDMPBFRBXFK9PJ4XWVqUtx0GXmy	CLIENTE	t	2026-09-16 23:59:08.814946+00	\N	\N	\N	\N
3759	Usuario de prueba	test-ca9bd9a380@fashionstore.com	$2b$12$IgYrH1X9gHSaE8pHlb2ZS.j9/IU4ggzBQmANlV4n/DwUFyPC4MqxS	CLIENTE	t	2026-09-17 00:44:21.799707+00	\N	\N	\N	\N
4750	Usuario de prueba	test-76520ce0ac@fashionstore.com	$2b$12$FPaOslxYVDoEGTFfd28j5..EpQJtRkRSQx5tQK/lZ.G89gqZgPery	ADMINISTRADOR	t	2026-10-23 01:39:20.259371+00	\N	\N	\N	\N
4618	prove	prov@fashionstore.com	$2b$12$Q5Nc8HB9KV0J1.lxjAOn.u05vhQ9/9rWsev24CiLjQyseJpyTR24m	CLIENTE	t	2026-09-22 11:52:20.236181+00	\N	\N	78925463	\N
4619	provedor1234	prov1@fashionstore.com	$2b$12$6KmpIKZCyrR85y3k./8f2.dSQGAPj6L9qeH4rwVxoggNKegsj1gpO	CLIENTE	t	2026-09-22 11:54:07.452058+00	\N	\N	315154845	\N
4621	Andres	andres@gmail.com	$2b$12$VIjuFQEA.s//Ho4GJtB/TuPfKISYzIuSVz1.8PYDNTZw5k7fg.UtS	CAJERO	t	2026-09-22 12:04:10.951864+00	1	\N	\N	\N
4179	Usuario de prueba	test-45741c10a3@fashionstore.com	$2b$12$d/PSCPR5CF89OTzXEkeXL.FbJhXwUY131c.BoCkjOhtcJWP.JrlTu	CLIENTE	t	2026-09-17 02:32:14.361391+00	\N	\N	\N	\N
4182	Usuario de prueba	test-1333346b4b@fashionstore.com	$2b$12$eAI/Go0FS0mu/.6Bn0qHpes/VzxJbBDYikDIp7EyADe2aqOyq9122	CLIENTE	t	2026-09-17 02:33:11.156463+00	\N	\N	\N	\N
4623	Jhoan	chonaca601@gmail.com	$2b$12$hRx9Jubdxts.uhDZcPi9UOZk84aKgMToDBu3xs1lpnRTuSrxExcxm	CLIENTE	t	2026-09-22 12:07:58.427187+00	\N	\N	78925463	\N
3239	Usuario de prueba	test-c77932abf4@fashionstore.com	$2b$12$EB6gojCY87/IPy3S6UTlF.7TNeuu8ZdPAkj8A3XgEV5Xy8yL2OtgS	ADMINISTRADOR	t	2026-09-16 05:18:05.040901+00	\N	\N	\N	\N
3243	Usuario de prueba	test-ca5d43c851@fashionstore.com	$2b$12$dJNIZFBYt3nXPL.I3heNlekHxwDI6Q6vN.tuTZzE/xy/y829bgZUa	CLIENTE	t	2026-09-16 19:18:39.691548+00	\N	\N	\N	\N
2967	Usuario de prueba	test-fa4fed8b06@fashionstore.com	$2b$12$qZ4nCeLSAvGK3U0rzskr9OdqZbIYMJmMj5Bdl4GLGU3D4go3UhX8.	CLIENTE	t	2026-09-16 04:23:07.218893+00	\N	\N	\N	\N
2968	Usuario de prueba	test-4b9fc737de@fashionstore.com	$2b$12$QjyNlL4covwkXv5YT39nCeurR67swTKy5iV.tx6HuCLXx2wQTTLDm	CLIENTE	t	2026-09-16 04:23:20.538299+00	\N	\N	\N	\N
2969	Usuario de prueba	test-2b215aa0ce@fashionstore.com	$2b$12$ohu8EKeYOAEBuvYHFqJ6NegBhlq5urOA7ncoldRzD9H5KRbpe.Pq2	CLIENTE	t	2026-09-16 04:23:28.282733+00	\N	\N	\N	\N
3616	Usuario de prueba	test-5f2353b2fa@fashionstore.com	$2b$12$/oURtBQWZG7t2fMrbW9QdOp4Coz1yM29N47AbZjlhdU87bvQCViLy	CLIENTE	t	2026-09-16 23:57:46.651429+00	\N	\N	\N	\N
3618	Usuario de prueba	test-e64ba54ca9@fashionstore.com	$2b$12$hBiZnKwuizOr2A7GMdHnceAMHbmEKsmKWXzUoQWQsefLdtTHPBZXy	CLIENTE	t	2026-09-16 23:58:17.169888+00	\N	\N	\N	\N
3621	Usuario de prueba	test-1a98570432@fashionstore.com	$2b$12$zubsr6JmpCtxtPSeHdMYSunxWNVB9YHZ64QS/3NijK9e9zfBQCPg.	CLIENTE	t	2026-09-16 23:58:50.063284+00	\N	\N	\N	\N
4178	Usuario de prueba	test-29faef70d4@fashionstore.com	$2b$12$7DPSOQtKg6L9KQBKLBS8NeJHu/Mn1avhRE23h5f8/oae4sf.nu0WO	CLIENTE	t	2026-09-17 02:31:52.20863+00	\N	\N	\N	\N
4180	Usuario de prueba	test-e2e9cd3b04@fashionstore.com	$2b$12$jIMiLb2GWXvB.6mhEheaTexXcR3dpgKu1OB5fC4geZQkl4unsDRXC	CLIENTE	t	2026-09-17 02:32:35.449117+00	\N	\N	\N	\N
4181	Usuario de prueba	test-4ef5b2fd72@fashionstore.com	$2b$12$D/oOm9dw/yG8fn0okrFApeSUpwQ1tXScglvvFC5zjQ/Er7VH9GJf6	CLIENTE	t	2026-09-17 02:32:51.345631+00	\N	\N	\N	\N
3535	Usuario de prueba	test-a4285e1d0b@fashionstore.com	$2b$12$5Ht1PH56d1JthOVRHfN2XuqwTU4bo/mnz1BofqY/C1p2AfXCxEj2O	CLIENTE	t	2026-09-16 23:37:00.828899+00	\N	\N	\N	\N
3536	Usuario de prueba	test-8f5566d4fc@fashionstore.com	$2b$12$44UZq3KXt8CaxWnmyZZ9GOHvboyz7WJ/GsaXMuPsuB8aWpCC0LiUa	CLIENTE	t	2026-09-16 23:37:02.24184+00	\N	\N	\N	\N
4963	Usuario de prueba	test-d23c2b297d@fashionstore.com	$2b$12$yAbsE.QbRk3cE.f5yanJieWRN4zFRFCWLbqCYrmz/xox0fUBKdDC.	ENCARGADO_SUCURSAL	t	2026-10-23 02:51:11.450605+00	1652	\N	\N	\N
4184	Usuario de prueba	test-e8fbf86fd2@fashionstore.com	$2b$12$LqNnEIDXr34d7yQBjR/3fenCpo1QwEEW/OI/k.dpMDjrL.PWmnJTO	CLIENTE	t	2026-09-17 02:33:35.861153+00	\N	\N	\N	\N
4185	Usuario de prueba	test-399269c8ba@fashionstore.com	$2b$12$4z63pnZSw9nbt99rzULUZe0GQuk6S9JTjrRzyJJL7wXef853./8GC	CLIENTE	t	2026-09-17 02:34:01.110516+00	\N	\N	\N	\N
3738	Usuario de prueba	test-494f407eac@fashionstore.com	$2b$12$zFHAmdZZUndvB5MQhsDxbOIxN1mfifIpKhMv57zWHtFzg/yticcKC	CLIENTE	t	2026-09-17 00:37:05.186814+00	\N	\N	\N	\N
3740	Usuario de prueba	test-d654d0bd05@fashionstore.com	$2b$12$VDOQoeiW3tmZB0ztg1cURu8/gX1rQAO2MzlHywyXez2tU7cMGG2MW	CLIENTE	t	2026-09-17 00:37:36.252561+00	\N	\N	\N	\N
3743	Usuario de prueba	test-d321337cc9@fashionstore.com	$2b$12$CsuExzwzCEgj6A6/oqDwwu1su4mfjVaZbUBY8rBtCTU9vwcc1lwlG	CLIENTE	t	2026-09-17 00:38:10.122428+00	\N	\N	\N	\N
4187	Usuario de prueba	test-2b8e91e5d5@fashionstore.com	$2b$12$dB3sQC0ciuFfFsLCckhMlOFXwV2xlkL8qYMj/V3TLD/.x0IStgfZ6	CLIENTE	t	2026-09-17 02:34:26.271+00	\N	\N	\N	\N
3757	Usuario de prueba	test-62b5c267c6@fashionstore.com	$2b$12$j0JPYGRGtwCIyiRJi007g.Qwk6l7ztBCpXisaPotIQyJjUBbJmJry	CLIENTE	t	2026-09-17 00:44:20.040586+00	\N	\N	\N	\N
4620	Noelia	noe@gmail.com	$2b$12$nvdnMObOwzgeY4GZIqiPfOSkrDlj91turNpcNhy2odJlmvlKwPdh.	ENCARGADO_SUCURSAL	t	2026-09-22 11:59:38.592256+00	1	\N	\N	\N
4622	Daniel	daniel@gmail.com	$2b$12$Lnc5GDO3AeceBE4xXD75pu9EbdmMR/WhW/8GAkMk4Ex0UjHAh1K5C	PROVEEDOR	t	2026-09-22 12:05:51.928429+00	\N	892	\N	\N
5020	SuperAdmin FashionStore	superadmin@fashionstore.com	$2b$12$fJyJwSqJhtLmJBBEb0oyFe1wP62r35XPsvjUum6a5wigsrc1IZrmO	SUPERADMIN	t	2026-10-24 23:30:51.415124+00	\N	\N	\N	\N
1	Administrador FashionStore	admin@fashionstore.com	$2b$12$SRKbBYJHCE6dMuWzm/tTq.wBfR.huqgUJG4LeurYzIy.LTN4S9G3.	ADMINISTRADOR	t	2026-09-10 13:39:59.909902+00	\N	\N	\N	1
4360	Usuario de prueba	test-c5eaecce21@fashionstore.com	$2b$12$5IC4yVsTsQhnvvupB7CS9O0..mMGxGbMJZhnTVMSxlN7aSoin90Me	CLIENTE	t	2026-09-17 22:21:04.640182+00	\N	\N	\N	\N
\.


--
-- Data for Name: venta_detalles; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.venta_detalles (id, venta_id, producto_variante_id, cantidad, precio_unitario, subtotal, carrito_item_id) FROM stdin;
76	58	5	1	100.00	100.00	\N
77	59	5	1	100.00	100.00	\N
78	60	5	1	100.00	100.00	\N
67	50	5	1	100.00	100.00	\N
79	61	5	1	100.00	100.00	\N
65	48	5	1	100.00	100.00	\N
66	49	5	1	100.00	100.00	\N
80	62	5	1	100.00	100.00	\N
81	63	5	1	100.00	100.00	\N
82	64	55	1	90.00	90.00	\N
83	65	55	1	90.00	90.00	\N
84	66	55	1	90.00	90.00	\N
85	67	2	1	100.00	100.00	\N
\.


--
-- Data for Name: ventas; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.ventas (id, codigo_venta, cliente_id, sucursal_id, tipo, estado, total, fecha_creacion, cajero_id, origen, reserva_id) FROM stdin;
48	VT-00048	4609	1	DIGITAL	PENDIENTE_PAGO	100.00	2026-09-20 23:43:59.022176+00	\N	\N	\N
49	VT-00049	4609	1	DIGITAL	PENDIENTE_PAGO	100.00	2026-09-21 00:01:07.874967+00	\N	\N	\N
50	VT-00050	4608	1	DIGITAL	PENDIENTE_PAGO	100.00	2026-09-21 00:27:33.733232+00	\N	\N	\N
58	VT-00058	4608	1	DIGITAL	PENDIENTE_PAGO	100.00	2026-09-21 00:45:34.023477+00	\N	\N	\N
59	VT-00059	4608	1	DIGITAL	PENDIENTE_PAGO	100.00	2026-09-21 00:59:20.9547+00	\N	\N	\N
60	VT-00060	4608	1	DIGITAL	PAGADA	100.00	2026-09-21 02:28:02.868066+00	\N	\N	\N
61	VT-00061	4608	1	DIGITAL	PAGADA	100.00	2026-09-22 11:45:36.578468+00	\N	\N	\N
62	VT-00062	4609	1	DIGITAL	PAGADA	100.00	2026-09-22 11:50:48.609243+00	\N	\N	\N
63	VT-00063	4623	1	DIGITAL	PAGADA	100.00	2026-09-22 12:09:06.954457+00	\N	\N	\N
64	VT-00064	4623	1	DIGITAL	PAGADA	90.00	2026-09-29 11:47:52.217394+00	\N	\N	\N
66	VT-00066	4623	1	DIGITAL	PENDIENTE_PAGO	90.00	2026-09-29 11:56:53.426631+00	\N	\N	\N
65	VT-00065	4623	1	DIGITAL	PAGADA	90.00	2026-09-29 11:52:58.172819+00	\N	\N	\N
67	VT-00067	4608	1	DIGITAL	PAGADA	100.00	2026-09-29 12:16:43.9031+00	\N	\N	\N
\.


--
-- Name: carrito_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.carrito_items_id_seq', 209, true);


--
-- Name: carritos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.carritos_id_seq', 119, true);


--
-- Name: categorias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.categorias_id_seq', 1805, true);


--
-- Name: ciudades_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.ciudades_id_seq', 1694, true);


--
-- Name: colecciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.colecciones_id_seq', 2141, true);


--
-- Name: colores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.colores_id_seq', 2364, true);


--
-- Name: detalles_recepcion_mercaderia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.detalles_recepcion_mercaderia_id_seq', 6, true);


--
-- Name: devoluciones_cambios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.devoluciones_cambios_id_seq', 1, false);


--
-- Name: empresas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.empresas_id_seq', 1, true);


--
-- Name: movimientos_inventario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.movimientos_inventario_id_seq', 48, true);


--
-- Name: pagos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pagos_id_seq', 38, true);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 73, true);


--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.producto_imagenes_id_seq', 192, true);


--
-- Name: producto_variantes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.producto_variantes_id_seq', 2808, true);


--
-- Name: productos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.productos_id_seq', 1505, true);


--
-- Name: productos_proveedor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.productos_proveedor_id_seq', 258, true);


--
-- Name: promociones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.promociones_id_seq', 3, true);


--
-- Name: proveedores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.proveedores_id_seq', 2172, true);


--
-- Name: recepciones_mercaderia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.recepciones_mercaderia_id_seq', 5, true);


--
-- Name: reserva_detalles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.reserva_detalles_id_seq', 632, true);


--
-- Name: reservas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.reservas_id_seq', 431, true);


--
-- Name: stock_sucursal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.stock_sucursal_id_seq', 1598, true);


--
-- Name: sucursales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.sucursales_id_seq', 1664, true);


--
-- Name: tallas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.tallas_id_seq', 2471, true);


--
-- Name: temporadas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.temporadas_id_seq', 2617, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 5020, true);


--
-- Name: venta_detalles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.venta_detalles_id_seq', 85, true);


--
-- Name: ventas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.ventas_id_seq', 67, true);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (id);


--
-- Name: invitation invitation_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT invitation_pkey PRIMARY KEY (id);


--
-- Name: jwks jwks_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.jwks
    ADD CONSTRAINT jwks_pkey PRIMARY KEY (id);


--
-- Name: member member_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT member_pkey PRIMARY KEY (id);


--
-- Name: organization organization_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.organization
    ADD CONSTRAINT organization_pkey PRIMARY KEY (id);


--
-- Name: organization organization_slug_key; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.organization
    ADD CONSTRAINT organization_slug_key UNIQUE (slug);


--
-- Name: project_config project_config_endpoint_id_key; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.project_config
    ADD CONSTRAINT project_config_endpoint_id_key UNIQUE (endpoint_id);


--
-- Name: project_config project_config_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.project_config
    ADD CONSTRAINT project_config_pkey PRIMARY KEY (id);


--
-- Name: session session_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT session_pkey PRIMARY KEY (id);


--
-- Name: session session_token_key; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT session_token_key UNIQUE (token);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: verification verification_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.verification
    ADD CONSTRAINT verification_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: carrito_items carrito_items_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.carrito_items
    ADD CONSTRAINT carrito_items_pkey PRIMARY KEY (id);


--
-- Name: carritos carritos_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.carritos
    ADD CONSTRAINT carritos_pkey PRIMARY KEY (id);


--
-- Name: categorias categorias_nombre_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_nombre_key UNIQUE (nombre);


--
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- Name: ciudades ciudades_nombre_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT ciudades_nombre_key UNIQUE (nombre);


--
-- Name: ciudades ciudades_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT ciudades_pkey PRIMARY KEY (id);


--
-- Name: colecciones colecciones_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT colecciones_pkey PRIMARY KEY (id);


--
-- Name: colores colores_nombre_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.colores
    ADD CONSTRAINT colores_nombre_key UNIQUE (nombre);


--
-- Name: colores colores_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.colores
    ADD CONSTRAINT colores_pkey PRIMARY KEY (id);


--
-- Name: detalles_recepcion_mercaderia detalles_recepcion_mercaderia_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.detalles_recepcion_mercaderia
    ADD CONSTRAINT detalles_recepcion_mercaderia_pkey PRIMARY KEY (id);


--
-- Name: devoluciones_cambios devoluciones_cambios_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_pkey PRIMARY KEY (id);


--
-- Name: empresas empresas_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_pkey PRIMARY KEY (id);


--
-- Name: movimientos_inventario movimientos_inventario_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.movimientos_inventario
    ADD CONSTRAINT movimientos_inventario_pkey PRIMARY KEY (id);


--
-- Name: pagos pagos_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: producto_colores producto_colores_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_pkey PRIMARY KEY (producto_id, color_id);


--
-- Name: producto_imagenes producto_imagenes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_imagenes
    ADD CONSTRAINT producto_imagenes_pkey PRIMARY KEY (id);


--
-- Name: producto_tallas producto_tallas_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_pkey PRIMARY KEY (producto_id, talla_id);


--
-- Name: producto_variantes producto_variantes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_pkey PRIMARY KEY (id);


--
-- Name: producto_variantes producto_variantes_producto_id_talla_id_color_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_producto_id_talla_id_color_id_key UNIQUE (producto_id, talla_id, color_id);


--
-- Name: productos productos_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_pkey PRIMARY KEY (id);


--
-- Name: productos productos_producto_proveedor_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_producto_proveedor_id_key UNIQUE (producto_proveedor_id);


--
-- Name: productos_proveedor productos_proveedor_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos_proveedor
    ADD CONSTRAINT productos_proveedor_pkey PRIMARY KEY (id);


--
-- Name: promocion_productos promocion_productos_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT promocion_productos_pkey PRIMARY KEY (promocion_id, producto_id);


--
-- Name: promociones promociones_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.promociones
    ADD CONSTRAINT promociones_pkey PRIMARY KEY (id);


--
-- Name: proveedores proveedores_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT proveedores_pkey PRIMARY KEY (id);


--
-- Name: proveedores proveedores_razon_social_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT proveedores_razon_social_key UNIQUE (razon_social);


--
-- Name: recepciones_mercaderia recepciones_mercaderia_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_pkey PRIMARY KEY (id);


--
-- Name: reserva_detalles reserva_detalles_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reserva_detalles
    ADD CONSTRAINT reserva_detalles_pkey PRIMARY KEY (id);


--
-- Name: reservas reservas_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_pkey PRIMARY KEY (id);


--
-- Name: stock_sucursal stock_sucursal_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_pkey PRIMARY KEY (id);


--
-- Name: stock_sucursal stock_sucursal_sucursal_id_producto_variante_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_sucursal_id_producto_variante_id_key UNIQUE (sucursal_id, producto_variante_id);


--
-- Name: sucursales sucursales_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT sucursales_pkey PRIMARY KEY (id);


--
-- Name: tallas tallas_nombre_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT tallas_nombre_key UNIQUE (nombre);


--
-- Name: tallas tallas_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT tallas_pkey PRIMARY KEY (id);


--
-- Name: temporadas temporadas_nombre_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.temporadas
    ADD CONSTRAINT temporadas_nombre_key UNIQUE (nombre);


--
-- Name: temporadas temporadas_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.temporadas
    ADD CONSTRAINT temporadas_pkey PRIMARY KEY (id);


--
-- Name: carritos uq_carritos_cliente_id; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.carritos
    ADD CONSTRAINT uq_carritos_cliente_id UNIQUE (cliente_id);


--
-- Name: empresas uq_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT uq_empresa_nombre UNIQUE (nombre);


--
-- Name: empresas uq_empresa_slug; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT uq_empresa_slug UNIQUE (slug);


--
-- Name: pagos uq_pagos_stripe_checkout_session_id; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT uq_pagos_stripe_checkout_session_id UNIQUE (stripe_checkout_session_id);


--
-- Name: reservas uq_reservas_codigo_reserva; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT uq_reservas_codigo_reserva UNIQUE (codigo_reserva);


--
-- Name: ventas uq_ventas_codigo_venta; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT uq_ventas_codigo_venta UNIQUE (codigo_venta);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_proveedor_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_proveedor_id_key UNIQUE (proveedor_id);


--
-- Name: venta_detalles venta_detalles_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT venta_detalles_pkey PRIMARY KEY (id);


--
-- Name: ventas ventas_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_pkey PRIMARY KEY (id);


--
-- Name: account_userId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "account_userId_idx" ON neon_auth.account USING btree ("userId");


--
-- Name: invitation_email_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX invitation_email_idx ON neon_auth.invitation USING btree (email);


--
-- Name: invitation_organizationId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "invitation_organizationId_idx" ON neon_auth.invitation USING btree ("organizationId");


--
-- Name: member_organizationId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "member_organizationId_idx" ON neon_auth.member USING btree ("organizationId");


--
-- Name: member_userId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "member_userId_idx" ON neon_auth.member USING btree ("userId");


--
-- Name: organization_slug_uidx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE UNIQUE INDEX organization_slug_uidx ON neon_auth.organization USING btree (slug);


--
-- Name: session_userId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "session_userId_idx" ON neon_auth.session USING btree ("userId");


--
-- Name: verification_identifier_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX verification_identifier_idx ON neon_auth.verification USING btree (identifier);


--
-- Name: ix_colecciones_una_destacada_inicio; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE UNIQUE INDEX ix_colecciones_una_destacada_inicio ON public.colecciones USING btree (es_destacada_inicio) WHERE es_destacada_inicio;


--
-- Name: ix_password_reset_tokens_token_hash; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE UNIQUE INDEX ix_password_reset_tokens_token_hash ON public.password_reset_tokens USING btree (token_hash);


--
-- Name: ix_password_reset_tokens_usuario_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_password_reset_tokens_usuario_id ON public.password_reset_tokens USING btree (usuario_id);


--
-- Name: ix_reserva_detalles_reserva_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_reserva_detalles_reserva_id ON public.reserva_detalles USING btree (reserva_id);


--
-- Name: ix_usuarios_correo; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE UNIQUE INDEX ix_usuarios_correo ON public.usuarios USING btree (correo);


--
-- Name: account account_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.account
    ADD CONSTRAINT "account_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: invitation invitation_inviterId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT "invitation_inviterId_fkey" FOREIGN KEY ("inviterId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: invitation invitation_organizationId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT "invitation_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES neon_auth.organization(id) ON DELETE CASCADE;


--
-- Name: member member_organizationId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT "member_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES neon_auth.organization(id) ON DELETE CASCADE;


--
-- Name: member member_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT "member_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: session session_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT "session_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: carrito_items carrito_items_carrito_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.carrito_items
    ADD CONSTRAINT carrito_items_carrito_id_fkey FOREIGN KEY (carrito_id) REFERENCES public.carritos(id) ON DELETE CASCADE;


--
-- Name: carrito_items carrito_items_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.carrito_items
    ADD CONSTRAINT carrito_items_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: carritos carritos_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.carritos
    ADD CONSTRAINT carritos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id);


--
-- Name: colecciones colecciones_temporada_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT colecciones_temporada_id_fkey FOREIGN KEY (temporada_id) REFERENCES public.temporadas(id);


--
-- Name: detalles_recepcion_mercaderia detalles_recepcion_mercaderia_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.detalles_recepcion_mercaderia
    ADD CONSTRAINT detalles_recepcion_mercaderia_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: detalles_recepcion_mercaderia detalles_recepcion_mercaderia_recepcion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.detalles_recepcion_mercaderia
    ADD CONSTRAINT detalles_recepcion_mercaderia_recepcion_id_fkey FOREIGN KEY (recepcion_id) REFERENCES public.recepciones_mercaderia(id) ON DELETE CASCADE;


--
-- Name: devoluciones_cambios devoluciones_cambios_cajero_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_cajero_id_fkey FOREIGN KEY (cajero_id) REFERENCES public.usuarios(id);


--
-- Name: devoluciones_cambios devoluciones_cambios_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: devoluciones_cambios devoluciones_cambios_variante_nueva_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_variante_nueva_id_fkey FOREIGN KEY (variante_nueva_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: devoluciones_cambios devoluciones_cambios_variante_original_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_variante_original_id_fkey FOREIGN KEY (variante_original_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: devoluciones_cambios devoluciones_cambios_venta_detalle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_venta_detalle_id_fkey FOREIGN KEY (venta_detalle_id) REFERENCES public.venta_detalles(id) ON DELETE CASCADE;


--
-- Name: devoluciones_cambios devoluciones_cambios_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas(id) ON DELETE CASCADE;


--
-- Name: categorias fk_categorias_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT fk_categorias_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: ciudades fk_ciudades_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT fk_ciudades_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: colecciones fk_colecciones_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT fk_colecciones_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: colores fk_colores_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.colores
    ADD CONSTRAINT fk_colores_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: pagos fk_pagos_cajero_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT fk_pagos_cajero_id FOREIGN KEY (cajero_id) REFERENCES public.usuarios(id);


--
-- Name: productos fk_productos_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT fk_productos_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: proveedores fk_proveedores_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT fk_proveedores_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: reserva_detalles fk_reserva_detalles_reserva_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reserva_detalles
    ADD CONSTRAINT fk_reserva_detalles_reserva_id FOREIGN KEY (reserva_id) REFERENCES public.reservas(id) ON DELETE CASCADE;


--
-- Name: sucursales fk_sucursales_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT fk_sucursales_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: tallas fk_tallas_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT fk_tallas_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: temporadas fk_temporadas_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.temporadas
    ADD CONSTRAINT fk_temporadas_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: usuarios fk_usuarios_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_usuarios_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: venta_detalles fk_venta_detalles_carrito_item_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT fk_venta_detalles_carrito_item_id FOREIGN KEY (carrito_item_id) REFERENCES public.carrito_items(id) ON DELETE SET NULL;


--
-- Name: ventas fk_ventas_cajero_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_cajero_id FOREIGN KEY (cajero_id) REFERENCES public.usuarios(id);


--
-- Name: ventas fk_ventas_reserva_id; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_reserva_id FOREIGN KEY (reserva_id) REFERENCES public.reservas(id) ON DELETE SET NULL;


--
-- Name: movimientos_inventario movimientos_inventario_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.movimientos_inventario
    ADD CONSTRAINT movimientos_inventario_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: movimientos_inventario movimientos_inventario_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.movimientos_inventario
    ADD CONSTRAINT movimientos_inventario_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: movimientos_inventario movimientos_inventario_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.movimientos_inventario
    ADD CONSTRAINT movimientos_inventario_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: pagos pagos_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas(id) ON DELETE CASCADE;


--
-- Name: password_reset_tokens password_reset_tokens_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: producto_colores producto_colores_color_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_color_id_fkey FOREIGN KEY (color_id) REFERENCES public.colores(id);


--
-- Name: producto_colores producto_colores_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: producto_imagenes producto_imagenes_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_imagenes
    ADD CONSTRAINT producto_imagenes_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: producto_tallas producto_tallas_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: producto_tallas producto_tallas_talla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_talla_id_fkey FOREIGN KEY (talla_id) REFERENCES public.tallas(id);


--
-- Name: producto_variantes producto_variantes_color_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_color_id_fkey FOREIGN KEY (color_id) REFERENCES public.colores(id);


--
-- Name: producto_variantes producto_variantes_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: producto_variantes producto_variantes_talla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_talla_id_fkey FOREIGN KEY (talla_id) REFERENCES public.tallas(id);


--
-- Name: productos productos_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id);


--
-- Name: productos productos_coleccion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_coleccion_id_fkey FOREIGN KEY (coleccion_id) REFERENCES public.colecciones(id);


--
-- Name: productos productos_producto_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_producto_proveedor_id_fkey FOREIGN KEY (producto_proveedor_id) REFERENCES public.productos_proveedor(id);


--
-- Name: productos productos_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedores(id);


--
-- Name: productos_proveedor productos_proveedor_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos_proveedor
    ADD CONSTRAINT productos_proveedor_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedores(id);


--
-- Name: productos productos_temporada_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_temporada_id_fkey FOREIGN KEY (temporada_id) REFERENCES public.temporadas(id);


--
-- Name: promocion_productos promocion_productos_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT promocion_productos_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: promocion_productos promocion_productos_promocion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT promocion_productos_promocion_id_fkey FOREIGN KEY (promocion_id) REFERENCES public.promociones(id) ON DELETE CASCADE;


--
-- Name: recepciones_mercaderia recepciones_mercaderia_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedores(id);


--
-- Name: recepciones_mercaderia recepciones_mercaderia_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: recepciones_mercaderia recepciones_mercaderia_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: reserva_detalles reserva_detalles_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reserva_detalles
    ADD CONSTRAINT reserva_detalles_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: reservas reservas_cliente_id_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_cliente_id_fkey1 FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id);


--
-- Name: reservas reservas_sucursal_id_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_sucursal_id_fkey1 FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: stock_sucursal stock_sucursal_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: stock_sucursal stock_sucursal_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: sucursales sucursales_ciudad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT sucursales_ciudad_id_fkey FOREIGN KEY (ciudad_id) REFERENCES public.ciudades(id);


--
-- Name: usuarios usuarios_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedores(id);


--
-- Name: usuarios usuarios_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: venta_detalles venta_detalles_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT venta_detalles_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: venta_detalles venta_detalles_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT venta_detalles_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas(id) ON DELETE CASCADE;


--
-- Name: ventas ventas_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id);


--
-- Name: ventas ventas_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

\unrestrict PduCDWNkezDysSeCsWkpfjW882vzKsY7Ruc8uj3f58MUTzbVzRSgt8gzZh5khAR

