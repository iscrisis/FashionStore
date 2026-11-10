--
-- PostgreSQL database dump
--

\restrict a0QuH1juzS8avZKxPLGExzAzk4IKgURil1opZJjfrO32B1Lf5F0TaRJbkUTdlxO

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: fashionstore
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO fashionstore;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: fashionstore
--

COMMENT ON SCHEMA public IS '';


--
-- Name: estado_pago; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.estado_pago AS ENUM (
    'PENDIENTE',
    'PAGADO',
    'CANCELADO',
    'FALLIDO'
);


ALTER TYPE public.estado_pago OWNER TO fashionstore;

--
-- Name: estado_producto_proveedor; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.estado_producto_proveedor AS ENUM (
    'PENDIENTE',
    'APROBADO',
    'RECHAZADO'
);


ALTER TYPE public.estado_producto_proveedor OWNER TO fashionstore;

--
-- Name: estado_reembolso; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.estado_reembolso AS ENUM (
    'REGISTRADO',
    'COMPLETADO'
);


ALTER TYPE public.estado_reembolso OWNER TO fashionstore;

--
-- Name: estado_reserva; Type: TYPE; Schema: public; Owner: fashionstore
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


ALTER TYPE public.estado_reserva OWNER TO fashionstore;

--
-- Name: estado_venta; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.estado_venta AS ENUM (
    'PENDIENTE_PAGO',
    'PAGADA'
);


ALTER TYPE public.estado_venta OWNER TO fashionstore;

--
-- Name: motivo_devolucion; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.motivo_devolucion AS ENUM (
    'TALLA',
    'DEFECTO',
    'PRODUCTO_INCORRECTO',
    'OTRO'
);


ALTER TYPE public.motivo_devolucion OWNER TO fashionstore;

--
-- Name: origen_venta; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.origen_venta AS ENUM (
    'DIRECTA',
    'RESERVA'
);


ALTER TYPE public.origen_venta OWNER TO fashionstore;

--
-- Name: proveedor_pago; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.proveedor_pago AS ENUM (
    'STRIPE',
    'EFECTIVO',
    'TARJETA',
    'QR'
);


ALTER TYPE public.proveedor_pago OWNER TO fashionstore;

--
-- Name: rol_usuario; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.rol_usuario AS ENUM (
    'SUPERADMIN',
    'ADMINISTRADOR',
    'ENCARGADO_SUCURSAL',
    'CAJERO',
    'PROVEEDOR',
    'CLIENTE'
);


ALTER TYPE public.rol_usuario OWNER TO fashionstore;

--
-- Name: tipo_movimiento_inventario; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.tipo_movimiento_inventario AS ENUM (
    'AJUSTE_POSITIVO',
    'AJUSTE_NEGATIVO'
);


ALTER TYPE public.tipo_movimiento_inventario OWNER TO fashionstore;

--
-- Name: tipo_operacion_devolucion; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.tipo_operacion_devolucion AS ENUM (
    'DEVOLUCION',
    'CAMBIO'
);


ALTER TYPE public.tipo_operacion_devolucion OWNER TO fashionstore;

--
-- Name: tipo_tarjeta; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.tipo_tarjeta AS ENUM (
    'DEBITO',
    'CREDITO'
);


ALTER TYPE public.tipo_tarjeta OWNER TO fashionstore;

--
-- Name: tipo_venta; Type: TYPE; Schema: public; Owner: fashionstore
--

CREATE TYPE public.tipo_venta AS ENUM (
    'DIGITAL',
    'PRESENCIAL'
);


ALTER TYPE public.tipo_venta OWNER TO fashionstore;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.alembic_version (
    version_num character varying(100) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO fashionstore;

--
-- Name: carrito_items; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.carrito_items (
    id integer NOT NULL,
    carrito_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    fecha_agregado timestamp with time zone DEFAULT now() NOT NULL,
    seleccionado boolean DEFAULT true NOT NULL
);


ALTER TABLE public.carrito_items OWNER TO fashionstore;

--
-- Name: carrito_items_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.carrito_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.carrito_items_id_seq OWNER TO fashionstore;

--
-- Name: carrito_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.carrito_items_id_seq OWNED BY public.carrito_items.id;


--
-- Name: carritos; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.carritos (
    id integer NOT NULL,
    cliente_id integer NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    fecha_actualizacion timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.carritos OWNER TO fashionstore;

--
-- Name: carritos_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.carritos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.carritos_id_seq OWNER TO fashionstore;

--
-- Name: carritos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.carritos_id_seq OWNED BY public.carritos.id;


--
-- Name: categorias; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.categorias (
    id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    is_active boolean NOT NULL,
    imagen_url character varying(500),
    empresa_id integer
);


ALTER TABLE public.categorias OWNER TO fashionstore;

--
-- Name: categorias_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorias_id_seq OWNER TO fashionstore;

--
-- Name: categorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;


--
-- Name: ciudades; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.ciudades (
    id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    is_active boolean NOT NULL,
    departamento character varying(120) NOT NULL,
    empresa_id integer
);


ALTER TABLE public.ciudades OWNER TO fashionstore;

--
-- Name: ciudades_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.ciudades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ciudades_id_seq OWNER TO fashionstore;

--
-- Name: ciudades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.ciudades_id_seq OWNED BY public.ciudades.id;


--
-- Name: colecciones; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.colecciones OWNER TO fashionstore;

--
-- Name: colecciones_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.colecciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.colecciones_id_seq OWNER TO fashionstore;

--
-- Name: colecciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.colecciones_id_seq OWNED BY public.colecciones.id;


--
-- Name: colores; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.colores (
    id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    is_active boolean NOT NULL,
    empresa_id integer
);


ALTER TABLE public.colores OWNER TO fashionstore;

--
-- Name: colores_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.colores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.colores_id_seq OWNER TO fashionstore;

--
-- Name: colores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.colores_id_seq OWNED BY public.colores.id;


--
-- Name: detalles_recepcion_mercaderia; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.detalles_recepcion_mercaderia (
    id integer NOT NULL,
    recepcion_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    cantidad_recibida integer NOT NULL,
    CONSTRAINT ck_detalle_recepcion_cantidad_positiva CHECK ((cantidad_recibida > 0))
);


ALTER TABLE public.detalles_recepcion_mercaderia OWNER TO fashionstore;

--
-- Name: detalles_recepcion_mercaderia_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.detalles_recepcion_mercaderia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detalles_recepcion_mercaderia_id_seq OWNER TO fashionstore;

--
-- Name: detalles_recepcion_mercaderia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.detalles_recepcion_mercaderia_id_seq OWNED BY public.detalles_recepcion_mercaderia.id;


--
-- Name: devoluciones_cambios; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.devoluciones_cambios OWNER TO fashionstore;

--
-- Name: devoluciones_cambios_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.devoluciones_cambios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.devoluciones_cambios_id_seq OWNER TO fashionstore;

--
-- Name: devoluciones_cambios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.devoluciones_cambios_id_seq OWNED BY public.devoluciones_cambios.id;


--
-- Name: empresas; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.empresas OWNER TO fashionstore;

--
-- Name: empresas_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.empresas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.empresas_id_seq OWNER TO fashionstore;

--
-- Name: empresas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.empresas_id_seq OWNED BY public.empresas.id;


--
-- Name: movimientos_inventario; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.movimientos_inventario OWNER TO fashionstore;

--
-- Name: movimientos_inventario_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.movimientos_inventario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimientos_inventario_id_seq OWNER TO fashionstore;

--
-- Name: movimientos_inventario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.movimientos_inventario_id_seq OWNED BY public.movimientos_inventario.id;


--
-- Name: operaciones_sincronizacion_log; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.operaciones_sincronizacion_log (
    id integer NOT NULL,
    empresa_id integer NOT NULL,
    uuid_operacion_offline character varying(255) NOT NULL,
    tipo_operacion character varying(50) NOT NULL,
    numero_intento integer DEFAULT 1 NOT NULL,
    fecha_intento timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    estado_resultado character varying(20) NOT NULL,
    motivo character varying(500),
    error_tipo character varying(100),
    http_status integer,
    tiempo_respuesta_ms integer,
    usuario_id integer
);


ALTER TABLE public.operaciones_sincronizacion_log OWNER TO fashionstore;

--
-- Name: operaciones_sincronizacion_log_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.operaciones_sincronizacion_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.operaciones_sincronizacion_log_id_seq OWNER TO fashionstore;

--
-- Name: operaciones_sincronizacion_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.operaciones_sincronizacion_log_id_seq OWNED BY public.operaciones_sincronizacion_log.id;


--
-- Name: pagos; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.pagos OWNER TO fashionstore;

--
-- Name: pagos_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.pagos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pagos_id_seq OWNER TO fashionstore;

--
-- Name: pagos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.pagos_id_seq OWNED BY public.pagos.id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.password_reset_tokens (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    token_hash character varying(64) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.password_reset_tokens OWNER TO fashionstore;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.password_reset_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.password_reset_tokens_id_seq OWNER TO fashionstore;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;


--
-- Name: planes; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.planes (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    slug character varying(50) NOT NULL,
    descripcion text NOT NULL,
    precio numeric(10,2) NOT NULL,
    duracion_dias integer NOT NULL,
    limite_sucursales integer NOT NULL,
    limite_usuarios integer NOT NULL,
    permite_prueba_gratuita boolean NOT NULL,
    duracion_prueba_dias integer,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.planes OWNER TO fashionstore;

--
-- Name: planes_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.planes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.planes_id_seq OWNER TO fashionstore;

--
-- Name: planes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.planes_id_seq OWNED BY public.planes.id;


--
-- Name: producto_colores; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.producto_colores (
    producto_id integer NOT NULL,
    color_id integer NOT NULL
);


ALTER TABLE public.producto_colores OWNER TO fashionstore;

--
-- Name: producto_imagenes; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.producto_imagenes (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    url character varying(500) NOT NULL,
    orden integer NOT NULL
);


ALTER TABLE public.producto_imagenes OWNER TO fashionstore;

--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.producto_imagenes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.producto_imagenes_id_seq OWNER TO fashionstore;

--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.producto_imagenes_id_seq OWNED BY public.producto_imagenes.id;


--
-- Name: producto_tallas; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.producto_tallas (
    producto_id integer NOT NULL,
    talla_id integer NOT NULL
);


ALTER TABLE public.producto_tallas OWNER TO fashionstore;

--
-- Name: producto_variantes; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.producto_variantes (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    talla_id integer NOT NULL,
    color_id integer NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.producto_variantes OWNER TO fashionstore;

--
-- Name: producto_variantes_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.producto_variantes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.producto_variantes_id_seq OWNER TO fashionstore;

--
-- Name: producto_variantes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.producto_variantes_id_seq OWNED BY public.producto_variantes.id;


--
-- Name: productos; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.productos (
    id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    descripcion character varying(500),
    proveedor_id integer NOT NULL,
    producto_proveedor_id integer,
    categoria_id integer NOT NULL,
    temporada_id integer NOT NULL,
    coleccion_id integer NOT NULL,
    precio_venta numeric(10,2) NOT NULL,
    is_active boolean NOT NULL,
    imagen_principal_url character varying(500),
    empresa_id integer
);


ALTER TABLE public.productos OWNER TO fashionstore;

--
-- Name: productos_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.productos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.productos_id_seq OWNER TO fashionstore;

--
-- Name: productos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.productos_id_seq OWNED BY public.productos.id;


--
-- Name: productos_proveedor; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.productos_proveedor OWNER TO fashionstore;

--
-- Name: productos_proveedor_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.productos_proveedor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.productos_proveedor_id_seq OWNER TO fashionstore;

--
-- Name: productos_proveedor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.productos_proveedor_id_seq OWNED BY public.productos_proveedor.id;


--
-- Name: promocion_productos; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.promocion_productos (
    promocion_id integer NOT NULL,
    producto_id integer NOT NULL,
    empresa_id integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.promocion_productos OWNER TO fashionstore;

--
-- Name: promociones; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.promociones (
    id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    porcentaje_descuento numeric(5,2) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    activa boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    empresa_id integer DEFAULT 1 NOT NULL,
    CONSTRAINT ck_promocion_fechas_orden CHECK ((fecha_fin >= fecha_inicio)),
    CONSTRAINT ck_promocion_porcentaje_rango CHECK (((porcentaje_descuento > (0)::numeric) AND (porcentaje_descuento < (100)::numeric)))
);


ALTER TABLE public.promociones OWNER TO fashionstore;

--
-- Name: promociones_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.promociones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.promociones_id_seq OWNER TO fashionstore;

--
-- Name: promociones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.promociones_id_seq OWNED BY public.promociones.id;


--
-- Name: proveedores; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.proveedores OWNER TO fashionstore;

--
-- Name: proveedores_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.proveedores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.proveedores_id_seq OWNER TO fashionstore;

--
-- Name: proveedores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.proveedores_id_seq OWNED BY public.proveedores.id;


--
-- Name: recepciones_mercaderia; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.recepciones_mercaderia (
    id integer NOT NULL,
    proveedor_id integer NOT NULL,
    sucursal_id integer NOT NULL,
    usuario_id integer NOT NULL,
    fecha_hora timestamp with time zone DEFAULT now() NOT NULL,
    observacion character varying(500)
);


ALTER TABLE public.recepciones_mercaderia OWNER TO fashionstore;

--
-- Name: recepciones_mercaderia_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.recepciones_mercaderia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.recepciones_mercaderia_id_seq OWNER TO fashionstore;

--
-- Name: recepciones_mercaderia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.recepciones_mercaderia_id_seq OWNED BY public.recepciones_mercaderia.id;


--
-- Name: reserva_detalles; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.reserva_detalles (
    id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    cantidad integer NOT NULL,
    estado public.estado_reserva NOT NULL,
    reserva_id integer NOT NULL,
    CONSTRAINT ck_reserva_detalle_cantidad_positiva CHECK ((cantidad > 0))
);


ALTER TABLE public.reserva_detalles OWNER TO fashionstore;

--
-- Name: reserva_detalles_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.reserva_detalles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reserva_detalles_id_seq OWNER TO fashionstore;

--
-- Name: reserva_detalles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.reserva_detalles_id_seq OWNED BY public.reserva_detalles.id;


--
-- Name: reservas; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.reservas (
    id integer NOT NULL,
    codigo_reserva character varying(20) NOT NULL,
    cliente_id integer NOT NULL,
    sucursal_id integer NOT NULL,
    fecha_reserva date NOT NULL,
    hora_inicio time without time zone NOT NULL,
    estado_general public.estado_reserva NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    empresa_id integer NOT NULL,
    uuid_operacion_offline character varying(255)
);


ALTER TABLE public.reservas OWNER TO fashionstore;

--
-- Name: reservas_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.reservas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reservas_id_seq OWNER TO fashionstore;

--
-- Name: reservas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.reservas_id_seq OWNED BY public.reservas.id;


--
-- Name: stock_sucursal; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.stock_sucursal OWNER TO fashionstore;

--
-- Name: stock_sucursal_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.stock_sucursal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.stock_sucursal_id_seq OWNER TO fashionstore;

--
-- Name: stock_sucursal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.stock_sucursal_id_seq OWNED BY public.stock_sucursal.id;


--
-- Name: sucursales; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.sucursales OWNER TO fashionstore;

--
-- Name: sucursales_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.sucursales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sucursales_id_seq OWNER TO fashionstore;

--
-- Name: sucursales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.sucursales_id_seq OWNED BY public.sucursales.id;


--
-- Name: suscripciones; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.suscripciones (
    id integer NOT NULL,
    empresa_id integer NOT NULL,
    plan_id integer NOT NULL,
    fecha_inicio timestamp with time zone NOT NULL,
    fecha_vencimiento timestamp with time zone NOT NULL,
    en_prueba boolean NOT NULL,
    fecha_fin_prueba timestamp with time zone,
    activa boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.suscripciones OWNER TO fashionstore;

--
-- Name: suscripciones_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.suscripciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.suscripciones_id_seq OWNER TO fashionstore;

--
-- Name: suscripciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.suscripciones_id_seq OWNED BY public.suscripciones.id;


--
-- Name: tallas; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.tallas (
    id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    is_active boolean NOT NULL,
    empresa_id integer
);


ALTER TABLE public.tallas OWNER TO fashionstore;

--
-- Name: tallas_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.tallas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tallas_id_seq OWNER TO fashionstore;

--
-- Name: tallas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.tallas_id_seq OWNED BY public.tallas.id;


--
-- Name: temporadas; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.temporadas (
    id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    is_active boolean NOT NULL,
    empresa_id integer
);


ALTER TABLE public.temporadas OWNER TO fashionstore;

--
-- Name: temporadas_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.temporadas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.temporadas_id_seq OWNER TO fashionstore;

--
-- Name: temporadas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.temporadas_id_seq OWNED BY public.temporadas.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.usuarios OWNER TO fashionstore;

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO fashionstore;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: venta_detalles; Type: TABLE; Schema: public; Owner: fashionstore
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


ALTER TABLE public.venta_detalles OWNER TO fashionstore;

--
-- Name: venta_detalles_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.venta_detalles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.venta_detalles_id_seq OWNER TO fashionstore;

--
-- Name: venta_detalles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.venta_detalles_id_seq OWNED BY public.venta_detalles.id;


--
-- Name: ventas; Type: TABLE; Schema: public; Owner: fashionstore
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
    reserva_id integer,
    empresa_id integer NOT NULL,
    uuid_operacion_offline character varying(255)
);


ALTER TABLE public.ventas OWNER TO fashionstore;

--
-- Name: ventas_id_seq; Type: SEQUENCE; Schema: public; Owner: fashionstore
--

CREATE SEQUENCE public.ventas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ventas_id_seq OWNER TO fashionstore;

--
-- Name: ventas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fashionstore
--

ALTER SEQUENCE public.ventas_id_seq OWNED BY public.ventas.id;


--
-- Name: carrito_items id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carrito_items ALTER COLUMN id SET DEFAULT nextval('public.carrito_items_id_seq'::regclass);


--
-- Name: carritos id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carritos ALTER COLUMN id SET DEFAULT nextval('public.carritos_id_seq'::regclass);


--
-- Name: categorias id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);


--
-- Name: ciudades id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ciudades ALTER COLUMN id SET DEFAULT nextval('public.ciudades_id_seq'::regclass);


--
-- Name: colecciones id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colecciones ALTER COLUMN id SET DEFAULT nextval('public.colecciones_id_seq'::regclass);


--
-- Name: colores id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colores ALTER COLUMN id SET DEFAULT nextval('public.colores_id_seq'::regclass);


--
-- Name: detalles_recepcion_mercaderia id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.detalles_recepcion_mercaderia ALTER COLUMN id SET DEFAULT nextval('public.detalles_recepcion_mercaderia_id_seq'::regclass);


--
-- Name: devoluciones_cambios id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.devoluciones_cambios ALTER COLUMN id SET DEFAULT nextval('public.devoluciones_cambios_id_seq'::regclass);


--
-- Name: empresas id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.empresas ALTER COLUMN id SET DEFAULT nextval('public.empresas_id_seq'::regclass);


--
-- Name: movimientos_inventario id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.movimientos_inventario ALTER COLUMN id SET DEFAULT nextval('public.movimientos_inventario_id_seq'::regclass);


--
-- Name: operaciones_sincronizacion_log id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.operaciones_sincronizacion_log ALTER COLUMN id SET DEFAULT nextval('public.operaciones_sincronizacion_log_id_seq'::regclass);


--
-- Name: pagos id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.pagos ALTER COLUMN id SET DEFAULT nextval('public.pagos_id_seq'::regclass);


--
-- Name: password_reset_tokens id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq'::regclass);


--
-- Name: planes id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.planes ALTER COLUMN id SET DEFAULT nextval('public.planes_id_seq'::regclass);


--
-- Name: producto_imagenes id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_imagenes ALTER COLUMN id SET DEFAULT nextval('public.producto_imagenes_id_seq'::regclass);


--
-- Name: producto_variantes id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes ALTER COLUMN id SET DEFAULT nextval('public.producto_variantes_id_seq'::regclass);


--
-- Name: productos id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos ALTER COLUMN id SET DEFAULT nextval('public.productos_id_seq'::regclass);


--
-- Name: productos_proveedor id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos_proveedor ALTER COLUMN id SET DEFAULT nextval('public.productos_proveedor_id_seq'::regclass);


--
-- Name: promociones id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promociones ALTER COLUMN id SET DEFAULT nextval('public.promociones_id_seq'::regclass);


--
-- Name: proveedores id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.proveedores ALTER COLUMN id SET DEFAULT nextval('public.proveedores_id_seq'::regclass);


--
-- Name: recepciones_mercaderia id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.recepciones_mercaderia ALTER COLUMN id SET DEFAULT nextval('public.recepciones_mercaderia_id_seq'::regclass);


--
-- Name: reserva_detalles id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reserva_detalles ALTER COLUMN id SET DEFAULT nextval('public.reserva_detalles_id_seq'::regclass);


--
-- Name: reservas id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas ALTER COLUMN id SET DEFAULT nextval('public.reservas_id_seq'::regclass);


--
-- Name: stock_sucursal id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.stock_sucursal ALTER COLUMN id SET DEFAULT nextval('public.stock_sucursal_id_seq'::regclass);


--
-- Name: sucursales id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.sucursales ALTER COLUMN id SET DEFAULT nextval('public.sucursales_id_seq'::regclass);


--
-- Name: suscripciones id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.suscripciones ALTER COLUMN id SET DEFAULT nextval('public.suscripciones_id_seq'::regclass);


--
-- Name: tallas id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.tallas ALTER COLUMN id SET DEFAULT nextval('public.tallas_id_seq'::regclass);


--
-- Name: temporadas id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.temporadas ALTER COLUMN id SET DEFAULT nextval('public.temporadas_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: venta_detalles id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.venta_detalles ALTER COLUMN id SET DEFAULT nextval('public.venta_detalles_id_seq'::regclass);


--
-- Name: ventas id; Type: DEFAULT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas ALTER COLUMN id SET DEFAULT nextval('public.ventas_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.alembic_version (version_num) FROM stdin;
003_crear_operaciones_sincronizacion_log
\.


--
-- Data for Name: carrito_items; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.carrito_items (id, carrito_id, producto_variante_id, fecha_agregado, seleccionado) FROM stdin;
\.


--
-- Data for Name: carritos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.carritos (id, cliente_id, fecha_creacion, fecha_actualizacion) FROM stdin;
\.


--
-- Data for Name: categorias; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.categorias (id, nombre, is_active, imagen_url, empresa_id) FROM stdin;
\.


--
-- Data for Name: ciudades; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.ciudades (id, nombre, is_active, departamento, empresa_id) FROM stdin;
\.


--
-- Data for Name: colecciones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.colecciones (id, nombre, temporada_id, descripcion, is_active, es_destacada_inicio, imagen_destacada_url, empresa_id) FROM stdin;
\.


--
-- Data for Name: colores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.colores (id, nombre, is_active, empresa_id) FROM stdin;
\.


--
-- Data for Name: detalles_recepcion_mercaderia; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.detalles_recepcion_mercaderia (id, recepcion_id, producto_variante_id, cantidad_recibida) FROM stdin;
\.


--
-- Data for Name: devoluciones_cambios; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.devoluciones_cambios (id, venta_id, venta_detalle_id, tipo, cantidad, variante_original_id, variante_nueva_id, motivo, observacion, monto_reembolso, metodo_reembolso, estado_reembolso, stripe_refund_id, cajero_id, sucursal_id, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: empresas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.empresas (id, nombre, slug, razon_social, correo, telefono, is_active, created_at, updated_at) FROM stdin;
1	FashionStore	fashionstore	FashionStore SAS	info@fashionstore.com	+573001234567	t	2026-11-10 01:35:28.402097+00	2026-11-10 01:35:28.402097+00
\.


--
-- Data for Name: movimientos_inventario; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.movimientos_inventario (id, sucursal_id, producto_variante_id, usuario_id, tipo, cantidad, motivo, stock_anterior, stock_resultante, fecha_hora) FROM stdin;
\.


--
-- Data for Name: operaciones_sincronizacion_log; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.operaciones_sincronizacion_log (id, empresa_id, uuid_operacion_offline, tipo_operacion, numero_intento, fecha_intento, estado_resultado, motivo, error_tipo, http_status, tiempo_respuesta_ms, usuario_id) FROM stdin;
\.


--
-- Data for Name: pagos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.pagos (id, venta_id, proveedor, stripe_checkout_session_id, stripe_payment_intent_id, monto, estado, fecha_creacion, fecha_confirmacion, cajero_id, monto_recibido, cambio, tipo_tarjeta, referencia) FROM stdin;
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.password_reset_tokens (id, usuario_id, token_hash, expires_at, used_at, created_at) FROM stdin;
\.


--
-- Data for Name: planes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.planes (id, nombre, slug, descripcion, precio, duracion_dias, limite_sucursales, limite_usuarios, permite_prueba_gratuita, duracion_prueba_dias, is_active, created_at, updated_at) FROM stdin;
1	Plan Gratuito	plan-gratuito	Plan de prueba con características limitadas	0.00	30	1	5	t	30	t	2026-11-10 01:35:28.445451+00	2026-11-10 01:35:28.445451+00
\.


--
-- Data for Name: producto_colores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_colores (producto_id, color_id) FROM stdin;
\.


--
-- Data for Name: producto_imagenes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_imagenes (id, producto_id, url, orden) FROM stdin;
\.


--
-- Data for Name: producto_tallas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_tallas (producto_id, talla_id) FROM stdin;
\.


--
-- Data for Name: producto_variantes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_variantes (id, producto_id, talla_id, color_id, is_active) FROM stdin;
\.


--
-- Data for Name: productos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.productos (id, nombre, descripcion, proveedor_id, producto_proveedor_id, categoria_id, temporada_id, coleccion_id, precio_venta, is_active, imagen_principal_url, empresa_id) FROM stdin;
\.


--
-- Data for Name: productos_proveedor; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.productos_proveedor (id, proveedor_id, nombre, descripcion, disponibilidad, is_active, imagen_url, estado) FROM stdin;
\.


--
-- Data for Name: promocion_productos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.promocion_productos (promocion_id, producto_id, empresa_id) FROM stdin;
\.


--
-- Data for Name: promociones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.promociones (id, nombre, porcentaje_descuento, fecha_inicio, fecha_fin, activa, fecha_creacion, empresa_id) FROM stdin;
\.


--
-- Data for Name: proveedores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.proveedores (id, razon_social, nombre_contacto, correo, telefono, is_active, empresa_id) FROM stdin;
\.


--
-- Data for Name: recepciones_mercaderia; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.recepciones_mercaderia (id, proveedor_id, sucursal_id, usuario_id, fecha_hora, observacion) FROM stdin;
\.


--
-- Data for Name: reserva_detalles; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.reserva_detalles (id, producto_variante_id, cantidad, estado, reserva_id) FROM stdin;
\.


--
-- Data for Name: reservas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.reservas (id, codigo_reserva, cliente_id, sucursal_id, fecha_reserva, hora_inicio, estado_general, fecha_creacion, empresa_id, uuid_operacion_offline) FROM stdin;
\.


--
-- Data for Name: stock_sucursal; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.stock_sucursal (id, sucursal_id, producto_variante_id, cantidad, stock_reservado) FROM stdin;
\.


--
-- Data for Name: sucursales; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.sucursales (id, nombre, ciudad_id, direccion, telefono, is_active, empresa_id) FROM stdin;
\.


--
-- Data for Name: suscripciones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.suscripciones (id, empresa_id, plan_id, fecha_inicio, fecha_vencimiento, en_prueba, fecha_fin_prueba, activa, created_at, updated_at) FROM stdin;
1	1	1	2026-11-10 01:35:28.457396+00	2026-12-10 01:35:28.457396+00	t	\N	t	2026-11-10 01:35:28.457396+00	2026-11-10 01:35:28.457396+00
\.


--
-- Data for Name: tallas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.tallas (id, nombre, is_active, empresa_id) FROM stdin;
\.


--
-- Data for Name: temporadas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.temporadas (id, nombre, fecha_inicio, fecha_fin, is_active, empresa_id) FROM stdin;
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.usuarios (id, nombre, correo, password_hash, rol, is_active, created_at, sucursal_id, proveedor_id, telefono, empresa_id) FROM stdin;
1	Administrador	admin@fashionstore.com	$2b$12$xmvT9F/zKHL0DtSzTdGbgOCJAiS9dEBk/wsX6wtIsIUoC/EmeyJSO	ADMINISTRADOR	t	2026-11-10 01:35:28.419268+00	\N	\N	+573001234567	1
\.


--
-- Data for Name: venta_detalles; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.venta_detalles (id, venta_id, producto_variante_id, cantidad, precio_unitario, subtotal, carrito_item_id) FROM stdin;
\.


--
-- Data for Name: ventas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.ventas (id, codigo_venta, cliente_id, sucursal_id, tipo, estado, total, fecha_creacion, cajero_id, origen, reserva_id, empresa_id, uuid_operacion_offline) FROM stdin;
\.


--
-- Name: carrito_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.carrito_items_id_seq', 1, false);


--
-- Name: carritos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.carritos_id_seq', 1, false);


--
-- Name: categorias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.categorias_id_seq', 1, false);


--
-- Name: ciudades_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.ciudades_id_seq', 1, false);


--
-- Name: colecciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.colecciones_id_seq', 1, false);


--
-- Name: colores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.colores_id_seq', 1, false);


--
-- Name: detalles_recepcion_mercaderia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.detalles_recepcion_mercaderia_id_seq', 1, false);


--
-- Name: devoluciones_cambios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.devoluciones_cambios_id_seq', 1, false);


--
-- Name: empresas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.empresas_id_seq', 1, true);


--
-- Name: movimientos_inventario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.movimientos_inventario_id_seq', 1, false);


--
-- Name: operaciones_sincronizacion_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.operaciones_sincronizacion_log_id_seq', 1, false);


--
-- Name: pagos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.pagos_id_seq', 1, false);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 1, false);


--
-- Name: planes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.planes_id_seq', 1, true);


--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.producto_imagenes_id_seq', 1, false);


--
-- Name: producto_variantes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.producto_variantes_id_seq', 1, false);


--
-- Name: productos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.productos_id_seq', 1, false);


--
-- Name: productos_proveedor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.productos_proveedor_id_seq', 1, false);


--
-- Name: promociones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.promociones_id_seq', 1, false);


--
-- Name: proveedores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.proveedores_id_seq', 1, false);


--
-- Name: recepciones_mercaderia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.recepciones_mercaderia_id_seq', 1, false);


--
-- Name: reserva_detalles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.reserva_detalles_id_seq', 1, false);


--
-- Name: reservas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.reservas_id_seq', 1, false);


--
-- Name: stock_sucursal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.stock_sucursal_id_seq', 1, false);


--
-- Name: sucursales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.sucursales_id_seq', 1, false);


--
-- Name: suscripciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.suscripciones_id_seq', 1, true);


--
-- Name: tallas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.tallas_id_seq', 1, false);


--
-- Name: temporadas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.temporadas_id_seq', 1, false);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 1, true);


--
-- Name: venta_detalles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.venta_detalles_id_seq', 1, false);


--
-- Name: ventas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.ventas_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: carrito_items carrito_items_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carrito_items
    ADD CONSTRAINT carrito_items_pkey PRIMARY KEY (id);


--
-- Name: carritos carritos_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carritos
    ADD CONSTRAINT carritos_pkey PRIMARY KEY (id);


--
-- Name: categorias categorias_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_nombre_key UNIQUE (nombre);


--
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- Name: ciudades ciudades_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT ciudades_nombre_key UNIQUE (nombre);


--
-- Name: ciudades ciudades_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT ciudades_pkey PRIMARY KEY (id);


--
-- Name: colecciones colecciones_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT colecciones_pkey PRIMARY KEY (id);


--
-- Name: colores colores_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colores
    ADD CONSTRAINT colores_nombre_key UNIQUE (nombre);


--
-- Name: colores colores_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colores
    ADD CONSTRAINT colores_pkey PRIMARY KEY (id);


--
-- Name: detalles_recepcion_mercaderia detalles_recepcion_mercaderia_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.detalles_recepcion_mercaderia
    ADD CONSTRAINT detalles_recepcion_mercaderia_pkey PRIMARY KEY (id);


--
-- Name: devoluciones_cambios devoluciones_cambios_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_pkey PRIMARY KEY (id);


--
-- Name: empresas empresas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_pkey PRIMARY KEY (id);


--
-- Name: movimientos_inventario movimientos_inventario_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.movimientos_inventario
    ADD CONSTRAINT movimientos_inventario_pkey PRIMARY KEY (id);


--
-- Name: operaciones_sincronizacion_log operaciones_sincronizacion_log_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.operaciones_sincronizacion_log
    ADD CONSTRAINT operaciones_sincronizacion_log_pkey PRIMARY KEY (id);


--
-- Name: pagos pagos_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: planes planes_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.planes
    ADD CONSTRAINT planes_nombre_key UNIQUE (nombre);


--
-- Name: planes planes_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.planes
    ADD CONSTRAINT planes_pkey PRIMARY KEY (id);


--
-- Name: planes planes_slug_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.planes
    ADD CONSTRAINT planes_slug_key UNIQUE (slug);


--
-- Name: producto_colores producto_colores_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_pkey PRIMARY KEY (producto_id, color_id);


--
-- Name: producto_imagenes producto_imagenes_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_imagenes
    ADD CONSTRAINT producto_imagenes_pkey PRIMARY KEY (id);


--
-- Name: producto_tallas producto_tallas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_pkey PRIMARY KEY (producto_id, talla_id);


--
-- Name: producto_variantes producto_variantes_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_pkey PRIMARY KEY (id);


--
-- Name: producto_variantes producto_variantes_producto_id_talla_id_color_id_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_producto_id_talla_id_color_id_key UNIQUE (producto_id, talla_id, color_id);


--
-- Name: productos productos_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_pkey PRIMARY KEY (id);


--
-- Name: productos productos_producto_proveedor_id_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_producto_proveedor_id_key UNIQUE (producto_proveedor_id);


--
-- Name: productos_proveedor productos_proveedor_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos_proveedor
    ADD CONSTRAINT productos_proveedor_pkey PRIMARY KEY (id);


--
-- Name: promocion_productos promocion_productos_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT promocion_productos_pkey PRIMARY KEY (promocion_id, producto_id);


--
-- Name: promociones promociones_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promociones
    ADD CONSTRAINT promociones_pkey PRIMARY KEY (id);


--
-- Name: proveedores proveedores_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT proveedores_pkey PRIMARY KEY (id);


--
-- Name: proveedores proveedores_razon_social_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT proveedores_razon_social_key UNIQUE (razon_social);


--
-- Name: recepciones_mercaderia recepciones_mercaderia_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_pkey PRIMARY KEY (id);


--
-- Name: reserva_detalles reserva_detalles_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reserva_detalles
    ADD CONSTRAINT reserva_detalles_pkey PRIMARY KEY (id);


--
-- Name: reservas reservas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_pkey PRIMARY KEY (id);


--
-- Name: stock_sucursal stock_sucursal_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_pkey PRIMARY KEY (id);


--
-- Name: stock_sucursal stock_sucursal_sucursal_id_producto_variante_id_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_sucursal_id_producto_variante_id_key UNIQUE (sucursal_id, producto_variante_id);


--
-- Name: sucursales sucursales_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT sucursales_pkey PRIMARY KEY (id);


--
-- Name: suscripciones suscripciones_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.suscripciones
    ADD CONSTRAINT suscripciones_pkey PRIMARY KEY (id);


--
-- Name: tallas tallas_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT tallas_nombre_key UNIQUE (nombre);


--
-- Name: tallas tallas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT tallas_pkey PRIMARY KEY (id);


--
-- Name: temporadas temporadas_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.temporadas
    ADD CONSTRAINT temporadas_nombre_key UNIQUE (nombre);


--
-- Name: temporadas temporadas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.temporadas
    ADD CONSTRAINT temporadas_pkey PRIMARY KEY (id);


--
-- Name: carritos uq_carritos_cliente_id; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carritos
    ADD CONSTRAINT uq_carritos_cliente_id UNIQUE (cliente_id);


--
-- Name: empresas uq_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT uq_empresa_nombre UNIQUE (nombre);


--
-- Name: empresas uq_empresa_slug; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT uq_empresa_slug UNIQUE (slug);


--
-- Name: pagos uq_pagos_stripe_checkout_session_id; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT uq_pagos_stripe_checkout_session_id UNIQUE (stripe_checkout_session_id);


--
-- Name: reservas uq_reservas_codigo_reserva; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT uq_reservas_codigo_reserva UNIQUE (codigo_reserva);


--
-- Name: reservas uq_reservas_uuid_operacion_offline; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT uq_reservas_uuid_operacion_offline UNIQUE (uuid_operacion_offline);


--
-- Name: ventas uq_ventas_codigo_venta; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT uq_ventas_codigo_venta UNIQUE (codigo_venta);


--
-- Name: ventas uq_ventas_uuid_operacion_offline; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT uq_ventas_uuid_operacion_offline UNIQUE (uuid_operacion_offline);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_proveedor_id_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_proveedor_id_key UNIQUE (proveedor_id);


--
-- Name: venta_detalles venta_detalles_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT venta_detalles_pkey PRIMARY KEY (id);


--
-- Name: ventas ventas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_pkey PRIMARY KEY (id);


--
-- Name: idx_empresa_fecha; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_empresa_fecha ON public.operaciones_sincronizacion_log USING btree (empresa_id, fecha_intento);


--
-- Name: idx_empresa_tipo_estado; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_empresa_tipo_estado ON public.operaciones_sincronizacion_log USING btree (empresa_id, tipo_operacion, estado_resultado);


--
-- Name: idx_proveedores_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_proveedores_empresa_id ON public.proveedores USING btree (empresa_id);


--
-- Name: idx_sucursales_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_sucursales_empresa_id ON public.sucursales USING btree (empresa_id);


--
-- Name: idx_suscripciones_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_suscripciones_empresa_id ON public.suscripciones USING btree (empresa_id);


--
-- Name: idx_usuarios_correo; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_usuarios_correo ON public.usuarios USING btree (correo);


--
-- Name: idx_usuarios_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_usuarios_empresa_id ON public.usuarios USING btree (empresa_id);


--
-- Name: idx_uuid_empresa; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_uuid_empresa ON public.operaciones_sincronizacion_log USING btree (uuid_operacion_offline, empresa_id);


--
-- Name: ix_colecciones_una_destacada_inicio; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE UNIQUE INDEX ix_colecciones_una_destacada_inicio ON public.colecciones USING btree (es_destacada_inicio) WHERE es_destacada_inicio;


--
-- Name: ix_password_reset_tokens_token_hash; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE UNIQUE INDEX ix_password_reset_tokens_token_hash ON public.password_reset_tokens USING btree (token_hash);


--
-- Name: ix_password_reset_tokens_usuario_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX ix_password_reset_tokens_usuario_id ON public.password_reset_tokens USING btree (usuario_id);


--
-- Name: ix_reserva_detalles_reserva_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX ix_reserva_detalles_reserva_id ON public.reserva_detalles USING btree (reserva_id);


--
-- Name: ix_suscripciones_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX ix_suscripciones_empresa_id ON public.suscripciones USING btree (empresa_id);


--
-- Name: ix_suscripciones_plan_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX ix_suscripciones_plan_id ON public.suscripciones USING btree (plan_id);


--
-- Name: ix_usuarios_correo; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE UNIQUE INDEX ix_usuarios_correo ON public.usuarios USING btree (correo);


--
-- Name: carrito_items carrito_items_carrito_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carrito_items
    ADD CONSTRAINT carrito_items_carrito_id_fkey FOREIGN KEY (carrito_id) REFERENCES public.carritos(id) ON DELETE CASCADE;


--
-- Name: carrito_items carrito_items_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carrito_items
    ADD CONSTRAINT carrito_items_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: carritos carritos_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carritos
    ADD CONSTRAINT carritos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id);


--
-- Name: colecciones colecciones_temporada_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT colecciones_temporada_id_fkey FOREIGN KEY (temporada_id) REFERENCES public.temporadas(id);


--
-- Name: detalles_recepcion_mercaderia detalles_recepcion_mercaderia_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.detalles_recepcion_mercaderia
    ADD CONSTRAINT detalles_recepcion_mercaderia_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: detalles_recepcion_mercaderia detalles_recepcion_mercaderia_recepcion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.detalles_recepcion_mercaderia
    ADD CONSTRAINT detalles_recepcion_mercaderia_recepcion_id_fkey FOREIGN KEY (recepcion_id) REFERENCES public.recepciones_mercaderia(id) ON DELETE CASCADE;


--
-- Name: devoluciones_cambios devoluciones_cambios_cajero_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_cajero_id_fkey FOREIGN KEY (cajero_id) REFERENCES public.usuarios(id);


--
-- Name: devoluciones_cambios devoluciones_cambios_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: devoluciones_cambios devoluciones_cambios_variante_nueva_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_variante_nueva_id_fkey FOREIGN KEY (variante_nueva_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: devoluciones_cambios devoluciones_cambios_variante_original_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_variante_original_id_fkey FOREIGN KEY (variante_original_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: devoluciones_cambios devoluciones_cambios_venta_detalle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_venta_detalle_id_fkey FOREIGN KEY (venta_detalle_id) REFERENCES public.venta_detalles(id) ON DELETE CASCADE;


--
-- Name: devoluciones_cambios devoluciones_cambios_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.devoluciones_cambios
    ADD CONSTRAINT devoluciones_cambios_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas(id) ON DELETE CASCADE;


--
-- Name: categorias fk_categorias_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT fk_categorias_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: ciudades fk_ciudades_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT fk_ciudades_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: colecciones fk_colecciones_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT fk_colecciones_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: colores fk_colores_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colores
    ADD CONSTRAINT fk_colores_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: pagos fk_pagos_cajero_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT fk_pagos_cajero_id FOREIGN KEY (cajero_id) REFERENCES public.usuarios(id);


--
-- Name: productos fk_productos_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT fk_productos_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: promocion_productos fk_promocion_productos_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT fk_promocion_productos_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: promociones fk_promociones_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promociones
    ADD CONSTRAINT fk_promociones_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: proveedores fk_proveedores_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT fk_proveedores_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: reserva_detalles fk_reserva_detalles_reserva_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reserva_detalles
    ADD CONSTRAINT fk_reserva_detalles_reserva_id FOREIGN KEY (reserva_id) REFERENCES public.reservas(id) ON DELETE CASCADE;


--
-- Name: reservas fk_reservas_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT fk_reservas_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: sucursales fk_sucursales_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT fk_sucursales_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: tallas fk_tallas_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT fk_tallas_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: temporadas fk_temporadas_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.temporadas
    ADD CONSTRAINT fk_temporadas_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: usuarios fk_usuarios_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_usuarios_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: venta_detalles fk_venta_detalles_carrito_item_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT fk_venta_detalles_carrito_item_id FOREIGN KEY (carrito_item_id) REFERENCES public.carrito_items(id) ON DELETE SET NULL;


--
-- Name: ventas fk_ventas_cajero_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_cajero_id FOREIGN KEY (cajero_id) REFERENCES public.usuarios(id);


--
-- Name: ventas fk_ventas_empresa_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_empresa_id FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: ventas fk_ventas_reserva_id; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_reserva_id FOREIGN KEY (reserva_id) REFERENCES public.reservas(id) ON DELETE SET NULL;


--
-- Name: movimientos_inventario movimientos_inventario_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.movimientos_inventario
    ADD CONSTRAINT movimientos_inventario_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: movimientos_inventario movimientos_inventario_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.movimientos_inventario
    ADD CONSTRAINT movimientos_inventario_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: movimientos_inventario movimientos_inventario_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.movimientos_inventario
    ADD CONSTRAINT movimientos_inventario_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: pagos pagos_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas(id) ON DELETE CASCADE;


--
-- Name: password_reset_tokens password_reset_tokens_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: producto_colores producto_colores_color_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_color_id_fkey FOREIGN KEY (color_id) REFERENCES public.colores(id);


--
-- Name: producto_colores producto_colores_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: producto_imagenes producto_imagenes_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_imagenes
    ADD CONSTRAINT producto_imagenes_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: producto_tallas producto_tallas_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: producto_tallas producto_tallas_talla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_talla_id_fkey FOREIGN KEY (talla_id) REFERENCES public.tallas(id);


--
-- Name: producto_variantes producto_variantes_color_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_color_id_fkey FOREIGN KEY (color_id) REFERENCES public.colores(id);


--
-- Name: producto_variantes producto_variantes_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: producto_variantes producto_variantes_talla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_talla_id_fkey FOREIGN KEY (talla_id) REFERENCES public.tallas(id);


--
-- Name: productos productos_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id);


--
-- Name: productos productos_coleccion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_coleccion_id_fkey FOREIGN KEY (coleccion_id) REFERENCES public.colecciones(id);


--
-- Name: productos productos_producto_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_producto_proveedor_id_fkey FOREIGN KEY (producto_proveedor_id) REFERENCES public.productos_proveedor(id);


--
-- Name: productos productos_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedores(id);


--
-- Name: productos_proveedor productos_proveedor_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos_proveedor
    ADD CONSTRAINT productos_proveedor_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedores(id);


--
-- Name: productos productos_temporada_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_temporada_id_fkey FOREIGN KEY (temporada_id) REFERENCES public.temporadas(id);


--
-- Name: promocion_productos promocion_productos_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT promocion_productos_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- Name: promocion_productos promocion_productos_promocion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT promocion_productos_promocion_id_fkey FOREIGN KEY (promocion_id) REFERENCES public.promociones(id) ON DELETE CASCADE;


--
-- Name: recepciones_mercaderia recepciones_mercaderia_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedores(id);


--
-- Name: recepciones_mercaderia recepciones_mercaderia_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: recepciones_mercaderia recepciones_mercaderia_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: reserva_detalles reserva_detalles_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reserva_detalles
    ADD CONSTRAINT reserva_detalles_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: reservas reservas_cliente_id_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_cliente_id_fkey1 FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id);


--
-- Name: reservas reservas_sucursal_id_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_sucursal_id_fkey1 FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: stock_sucursal stock_sucursal_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: stock_sucursal stock_sucursal_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: sucursales sucursales_ciudad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT sucursales_ciudad_id_fkey FOREIGN KEY (ciudad_id) REFERENCES public.ciudades(id);


--
-- Name: suscripciones suscripciones_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.suscripciones
    ADD CONSTRAINT suscripciones_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: suscripciones suscripciones_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.suscripciones
    ADD CONSTRAINT suscripciones_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.planes(id);


--
-- Name: usuarios usuarios_proveedor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_proveedor_id_fkey FOREIGN KEY (proveedor_id) REFERENCES public.proveedores(id);


--
-- Name: usuarios usuarios_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: venta_detalles venta_detalles_producto_variante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT venta_detalles_producto_variante_id_fkey FOREIGN KEY (producto_variante_id) REFERENCES public.producto_variantes(id) ON DELETE CASCADE;


--
-- Name: venta_detalles venta_detalles_venta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT venta_detalles_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES public.ventas(id) ON DELETE CASCADE;


--
-- Name: ventas ventas_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id);


--
-- Name: ventas ventas_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: fashionstore
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict a0QuH1juzS8avZKxPLGExzAzk4IKgURil1opZJjfrO32B1Lf5F0TaRJbkUTdlxO

