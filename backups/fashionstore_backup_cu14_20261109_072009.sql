--
-- PostgreSQL database dump
--

\restrict iSgIEp3FBFCxSbZjxofBpTvmLEIpo3T1ywJ77DMIjCgKHKl9rtaKgt0mjUZkIHd

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
    'PREPARADA',
    'EN_ATENCION',
    'LISTA_PARA_CAJA',
    'CANCELADA',
    'ATENDIDA',
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
    'CLIENTE',
    'PROVEEDOR'
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
-- Name: carrito_items; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.carrito_items (
    id integer NOT NULL,
    carrito_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    seleccionado boolean DEFAULT true NOT NULL,
    fecha_agregado timestamp with time zone DEFAULT now() NOT NULL
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
    empresa_id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    imagen_url character varying(500),
    is_active boolean NOT NULL
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
    empresa_id integer,
    nombre character varying(120) NOT NULL,
    departamento character varying(120) NOT NULL,
    is_active boolean NOT NULL
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
    empresa_id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    temporada_id integer NOT NULL,
    descripcion character varying(255),
    is_active boolean NOT NULL,
    es_destacada_inicio boolean NOT NULL,
    imagen_destacada_url character varying(500)
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
    empresa_id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    is_active boolean NOT NULL
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
    limite_sucursales integer NOT NULL,
    limite_usuarios integer NOT NULL,
    gestion_productos boolean NOT NULL,
    gestion_ventas boolean NOT NULL,
    reservas boolean NOT NULL,
    operacion_offline boolean NOT NULL,
    reportes_convencionales boolean NOT NULL,
    reportes_generativos_ia boolean NOT NULL,
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
    empresa_id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    descripcion character varying(500),
    proveedor_id integer NOT NULL,
    producto_proveedor_id integer,
    categoria_id integer NOT NULL,
    temporada_id integer NOT NULL,
    coleccion_id integer NOT NULL,
    precio_venta numeric(10,2) NOT NULL,
    imagen_principal_url character varying(500),
    is_active boolean NOT NULL
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
    imagen_url character varying(500),
    disponibilidad boolean NOT NULL,
    is_active boolean NOT NULL,
    estado public.estado_producto_proveedor NOT NULL
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
    producto_id integer NOT NULL
);


ALTER TABLE public.promocion_productos OWNER TO fashionstore;

--
-- Name: promociones; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.promociones (
    id integer NOT NULL,
    empresa_id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    porcentaje_descuento numeric(5,2) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    activa boolean NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
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
    empresa_id integer NOT NULL,
    razon_social character varying(150) NOT NULL,
    nombre_contacto character varying(120) NOT NULL,
    correo character varying(255) NOT NULL,
    telefono character varying(30) NOT NULL,
    is_active boolean NOT NULL
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
    reserva_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    cantidad integer NOT NULL,
    estado public.estado_reserva NOT NULL,
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
    empresa_id integer NOT NULL,
    codigo_reserva character varying(20) NOT NULL,
    cliente_id integer NOT NULL,
    sucursal_id integer NOT NULL,
    fecha_reserva date NOT NULL,
    hora_inicio time without time zone NOT NULL,
    estado_general public.estado_reserva NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
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
    cantidad integer NOT NULL,
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
    empresa_id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    ciudad_id integer NOT NULL,
    direccion character varying(255) NOT NULL,
    telefono character varying(30) NOT NULL,
    is_active boolean NOT NULL
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
    empresa_id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    is_active boolean NOT NULL
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
    empresa_id integer NOT NULL,
    nombre character varying(120) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    is_active boolean NOT NULL
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
    empresa_id integer,
    nombre character varying(120) NOT NULL,
    correo character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    rol public.rol_usuario NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    sucursal_id integer,
    proveedor_id integer,
    telefono character varying(30)
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
    empresa_id integer NOT NULL,
    codigo_venta character varying(20) NOT NULL,
    cliente_id integer,
    sucursal_id integer NOT NULL,
    tipo public.tipo_venta NOT NULL,
    estado public.estado_venta NOT NULL,
    monto_total numeric(10,2) NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    cajero_id integer,
    origen public.origen_venta,
    reserva_id integer,
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
-- Data for Name: carrito_items; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.carrito_items (id, carrito_id, producto_variante_id, seleccionado, fecha_agregado) FROM stdin;
2	1	1	f	2026-11-08 05:14:06.498908+00
3	1	1	f	2026-11-08 05:48:15.002283+00
5	1	1	t	2026-11-08 06:11:54.768714+00
\.


--
-- Data for Name: carritos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.carritos (id, cliente_id, fecha_creacion, fecha_actualizacion) FROM stdin;
1	4	2026-11-08 03:08:15.479017+00	2026-11-08 06:11:55.18488+00
\.


--
-- Data for Name: categorias; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.categorias (id, empresa_id, nombre, imagen_url, is_active) FROM stdin;
1	1	CHAQUETAS	\N	t
\.


--
-- Data for Name: ciudades; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.ciudades (id, empresa_id, nombre, departamento, is_active) FROM stdin;
1	\N	Santa Cruz	Santa Cruz	t
2	\N	Cochabamba	Cochabamba	t
3	\N	La Paz	La Paz	t
\.


--
-- Data for Name: colecciones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.colecciones (id, empresa_id, nombre, temporada_id, descripcion, is_active, es_destacada_inicio, imagen_destacada_url) FROM stdin;
1	1	URBAN	1	AAAAAAAAAAAAA	t	t	/api/v1/media/colecciones/0f84878ec9cb4e1ba9c3254798251277.jpg
\.


--
-- Data for Name: colores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.colores (id, empresa_id, nombre, is_active) FROM stdin;
1	1	AZUL	t
\.


--
-- Data for Name: detalles_recepcion_mercaderia; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.detalles_recepcion_mercaderia (id, recepcion_id, producto_variante_id, cantidad_recibida) FROM stdin;
1	1	1	20
2	2	2	20
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
1	FashionStore	fashionstore	Boutique	cristelvicente981@gmail.com	+59175553135	t	2026-11-07 16:54:30.503431+00	2026-11-07 16:54:30.503431+00
2	SHEIN	shein	Boutique	jael@gmail.com	+59175553133	t	2026-11-07 16:55:58.249737+00	2026-11-07 16:55:58.249737+00
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
1	2	STRIPE	cs_test_a1sixFfzXoaEUczHEi2jGwIGWaniwpLkOfGLpemKj8BihT19DeJMkDn6bi	\N	200.40	PENDIENTE	2026-11-08 05:29:15.637081+00	\N	\N	\N	\N	\N	\N
2	3	STRIPE	cs_test_a1IwQhtQzCVQoZ9yfFVAkGrvmToHsrwdGtssIR9KWxzxHh953ZyuwEYHjn	\N	200.40	PENDIENTE	2026-11-08 05:43:03.295741+00	\N	\N	\N	\N	\N	\N
3	4	STRIPE	cs_test_a1WvGo9ZBaTWlFCGTGumnEIUUtIYXGpCUSW6eoHTGDajMeTYEe7xglT3uT	pi_3UZOybJO82YVluNl0hH9dEqw	200.40	PAGADO	2026-11-08 05:48:50.284169+00	2026-11-08 05:49:25.957148+00	\N	\N	\N	\N	\N
4	11	EFECTIVO	\N	\N	200.40	PAGADO	2026-11-09 03:14:08.304717+00	2026-11-09 03:14:08.732474+00	2	200.40	0.00	\N	\N
5	12	EFECTIVO	\N	\N	200.40	PAGADO	2026-11-09 03:16:57.992197+00	2026-11-09 03:16:58.227178+00	2	200.40	0.00	\N	\N
6	13	EFECTIVO	\N	\N	200.40	PAGADO	2026-11-09 03:18:41.441944+00	2026-11-09 03:18:41.775163+00	2	200.40	0.00	\N	\N
7	14	EFECTIVO	\N	\N	200.40	PAGADO	2026-11-09 03:24:56.169522+00	2026-11-09 03:24:56.743767+00	8	251.00	50.60	\N	\N
8	15	EFECTIVO	\N	\N	200.40	PAGADO	2026-11-09 05:08:33.430996+00	2026-11-09 05:08:33.630542+00	8	250.50	50.10	\N	\N
9	16	EFECTIVO	\N	\N	200.00	PAGADO	2026-11-09 05:13:25.643383+00	2026-11-09 05:13:25.85776+00	8	200.00	0.00	\N	\N
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.password_reset_tokens (id, usuario_id, token_hash, expires_at, used_at, created_at) FROM stdin;
\.


--
-- Data for Name: planes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.planes (id, nombre, slug, descripcion, precio, limite_sucursales, limite_usuarios, gestion_productos, gestion_ventas, reservas, operacion_offline, reportes_convencionales, reportes_generativos_ia, is_active, created_at, updated_at) FROM stdin;
1	BASICO	basico	-------------------	20.00	2	20	t	t	t	t	t	f	t	2026-11-07 16:48:14.11027+00	2026-11-07 16:48:14.11027+00
2	PREMIUM	premium	AAAAAAAAAAAAAAAAAAAA	500.00	5	50	t	t	t	t	t	t	t	2026-11-07 16:48:46.082937+00	2026-11-07 16:48:46.082937+00
\.


--
-- Data for Name: producto_colores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_colores (producto_id, color_id) FROM stdin;
9	1
10	1
\.


--
-- Data for Name: producto_imagenes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_imagenes (id, producto_id, url, orden) FROM stdin;
1	10	/api/v1/media/productos/48f708ee1722463db4ce7654aec4d810.png	0
\.


--
-- Data for Name: producto_tallas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_tallas (producto_id, talla_id) FROM stdin;
9	1
10	1
\.


--
-- Data for Name: producto_variantes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_variantes (id, producto_id, talla_id, color_id, is_active) FROM stdin;
1	9	1	1	t
2	10	1	1	t
\.


--
-- Data for Name: productos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.productos (id, empresa_id, nombre, descripcion, proveedor_id, producto_proveedor_id, categoria_id, temporada_id, coleccion_id, precio_venta, imagen_principal_url, is_active) FROM stdin;
9	1	Chaqueta Urban Premium	Chaqueta premium azul	1	\N	1	1	1	250.50	/api/v1/media/productos/020819a76d854c989dfff9f076516f78.jpg	t
10	1	Polera	aaaaaaaaaaaaaaaa	1	\N	1	1	1	200.00	/api/v1/media/productos/90dc7e921106471d91a89aa2d917f098.jpg	t
\.


--
-- Data for Name: productos_proveedor; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.productos_proveedor (id, proveedor_id, nombre, descripcion, imagen_url, disponibilidad, is_active, estado) FROM stdin;
\.


--
-- Data for Name: promocion_productos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.promocion_productos (promocion_id, producto_id) FROM stdin;
3	9
\.


--
-- Data for Name: promociones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.promociones (id, empresa_id, nombre, porcentaje_descuento, fecha_inicio, fecha_fin, activa, fecha_creacion) FROM stdin;
3	1	Descuento Urban	20.00	2026-11-07	2026-12-07	t	2026-11-07 17:57:35.970529+00
\.


--
-- Data for Name: proveedores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.proveedores (id, empresa_id, razon_social, nombre_contacto, correo, telefono, is_active) FROM stdin;
1	1	Shen	Noe	noe@gmail.com	12345678	t
\.


--
-- Data for Name: recepciones_mercaderia; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.recepciones_mercaderia (id, proveedor_id, sucursal_id, usuario_id, fecha_hora, observacion) FROM stdin;
1	1	2	6	2026-11-08 04:54:36.582231+00	\N
2	1	2	7	2026-11-08 19:53:18.066485+00	\N
\.


--
-- Data for Name: reserva_detalles; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.reserva_detalles (id, reserva_id, producto_variante_id, cantidad, estado) FROM stdin;
1	1	1	1	CANCELADA
2	2	1	1	CANCELADA
5	5	1	1	CANCELADA
4	4	1	1	CANCELADA
3	3	1	1	CANCELADA
7	7	1	1	CANCELADA
6	6	1	2	CANCELADA
8	8	1	1	CANCELADA
9	9	1	1	PENDIENTE
11	11	2	1	CANCELADA
10	10	1	1	CANCELADA
12	12	2	1	PENDIENTE
\.


--
-- Data for Name: reservas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.reservas (id, empresa_id, codigo_reserva, cliente_id, sucursal_id, fecha_reserva, hora_inicio, estado_general, fecha_creacion, uuid_operacion_offline) FROM stdin;
1	1	RS-00001	4	2	2026-11-09	10:00:00	CANCELADA	2026-11-08 04:58:54.140952+00	\N
2	1	RS-00002	4	2	2026-11-09	10:00:00	CANCELADA	2026-11-08 06:12:03.639383+00	\N
5	1	RS-00005	4	2	2026-11-11	12:00:00	CANCELADA	2026-11-08 16:57:55.282552+00	\N
4	1	RS-00004	4	2	2026-11-10	10:00:00	CANCELADA	2026-11-08 06:43:47.379902+00	\N
3	1	RS-00003	4	2	2026-11-09	10:00:00	CANCELADA	2026-11-08 06:30:42.512527+00	\N
7	1	RS-00007	4	2	2026-11-12	13:00:00	CANCELADA	2026-11-08 17:20:33.142562+00	\N
6	1	RS-00006	4	2	2026-11-09	19:00:00	CANCELADA	2026-11-08 17:17:32.437299+00	\N
8	1	RS-00008	4	2	2026-11-09	12:00:00	CANCELADA	2026-11-08 18:51:14.647917+00	\N
9	1	RS-00009	2	2	2026-11-09	10:00:00	PENDIENTE	2026-11-09 03:19:44.427749+00	uuid-reserva-admin
11	1	RS-00011	4	2	2026-11-09	12:00:00	CANCELADA	2026-11-09 05:57:06.613388+00	75cdc996-e125-467b-a3e5-f0c814b52ea0
10	1	RS-00010	4	2	2026-11-09	10:00:00	CANCELADA	2026-11-09 05:28:13.862221+00	5bfaa30f-f7a4-4b24-b6c5-50f979d43a59
12	1	RS-00012	4	2	2026-11-09	10:00:00	PENDIENTE	2026-11-09 06:08:41.680207+00	dd00f6c3-877c-4c25-b27e-c01a2e32f225
\.


--
-- Data for Name: stock_sucursal; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.stock_sucursal (id, sucursal_id, producto_variante_id, cantidad, stock_reservado) FROM stdin;
1	2	1	14	1
2	2	2	19	1
\.


--
-- Data for Name: sucursales; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.sucursales (id, empresa_id, nombre, ciudad_id, direccion, telefono, is_active) FROM stdin;
2	1	Mall ventura	1	Mall ventura	75553135	t
\.


--
-- Data for Name: suscripciones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.suscripciones (id, empresa_id, plan_id, fecha_inicio, fecha_vencimiento, en_prueba, fecha_fin_prueba, activa, created_at, updated_at) FROM stdin;
1	1	2	2026-11-07 16:54:31.627096+00	2027-11-07 16:54:31.627096+00	f	\N	t	2026-11-07 16:54:31.585512+00	2026-11-07 16:54:31.585512+00
2	2	1	2026-11-07 16:55:58.678347+00	2027-11-07 16:55:58.678347+00	f	\N	t	2026-11-07 16:55:58.669418+00	2026-11-07 16:55:58.669418+00
\.


--
-- Data for Name: tallas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.tallas (id, empresa_id, nombre, is_active) FROM stdin;
1	1	L	t
\.


--
-- Data for Name: temporadas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.temporadas (id, empresa_id, nombre, fecha_inicio, fecha_fin, is_active) FROM stdin;
1	1	URBAN	2026-11-01	2026-11-20	t
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.usuarios (id, empresa_id, nombre, correo, password_hash, rol, is_active, created_at, sucursal_id, proveedor_id, telefono) FROM stdin;
1	\N	SuperAdmin FashionStore	superadmin@fashionstore.com	$2b$12$AM92DyN/gy5VQvWu2I36..fKAYgMwgYhe64.VhjABqHDQnJwksLom	SUPERADMIN	t	2026-11-07 16:38:25.432933+00	\N	\N	\N
3	2	Juan Sandoval	admin@shein.com	$2b$12$YtrwsvS1mdHpC7QnuZAakuEfcTSiTm65iaaZ/X/SHD46jT/K043Xu	ADMINISTRADOR	t	2026-11-07 16:55:58.273527+00	\N	\N	\N
4	1	Cristel Vicente	cristelvicente981@gmail.com	$2b$12$naeH7/Emm3VKK20DCDdSO.BF7kQuHg2Wk9aXylB.4UJx5Pk6Tm8qO	CLIENTE	t	2026-11-07 18:00:28.673526+00	\N	\N	+59175553135
5	2	Daniel Lima	dani@gmail.com	$2b$12$Fm9vdswzov8dNYy9hcKMfevIThvLRWqKg0wrLO9joPEBq7Ulj2/sm	CLIENTE	t	2026-11-07 18:01:22.689919+00	\N	\N	+59175553135
6	1	Eliana	elianalv@fashionstore.com	$2b$12$LgbMU9/iUJyMdvkbce4vqe2/ZGRqQUoWnFBiTVO1hksTfCf1DVEgW	ENCARGADO_SUCURSAL	f	2026-11-08 04:54:03.487668+00	2	\N	\N
7	1	Noelia	nao707@gmail.com	$2b$12$55fmq0p8KiKSvoEptqrjxOzu/rU6AQhkGYm7EQxE8jyt.h0LJ8Ybm	ENCARGADO_SUCURSAL	t	2026-11-08 19:52:55.860269+00	2	\N	\N
8	1	Abigail	abi@gmail.com	$2b$12$q/iNSBrsfHqFf57i5qP2a.XFxRr94a8XM8XTvXv6M8CXbFM/C0Sqq	CAJERO	t	2026-11-08 20:35:43.915918+00	2	\N	\N
9	1	Cajero Test	cajero@test.com	hashed_password_test	CAJERO	t	2026-11-09 03:05:44.781191+00	2	\N	\N
2	1	Jael Sandoval	admin@fashionstore.com	$2b$12$pD3CKsbqoF4JjA0oBr2G5ulzPLzM..ndiWXTeMAKJ6cdXbrYfHWaa	ADMINISTRADOR	t	2026-11-07 16:54:30.937239+00	2	\N	\N
\.


--
-- Data for Name: venta_detalles; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.venta_detalles (id, venta_id, producto_variante_id, cantidad, precio_unitario, subtotal, carrito_item_id) FROM stdin;
1	1	1	1	200.40	200.40	2
2	2	1	1	200.40	200.40	2
3	3	1	1	200.40	200.40	2
4	4	1	1	200.40	200.40	\N
5	5	1	1	200.40	200.40	\N
6	6	1	1	200.40	200.40	\N
7	7	1	1	200.40	200.40	\N
8	8	1	1	200.40	200.40	\N
9	9	1	1	200.40	200.40	\N
10	10	1	1	200.40	200.40	\N
11	11	1	1	200.40	200.40	\N
12	12	1	1	200.40	200.40	\N
13	13	1	1	200.40	200.40	\N
14	14	1	1	200.40	200.40	\N
15	15	1	1	200.40	200.40	\N
16	16	2	1	200.00	200.00	\N
\.


--
-- Data for Name: ventas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.ventas (id, empresa_id, codigo_venta, cliente_id, sucursal_id, tipo, estado, monto_total, fecha_creacion, cajero_id, origen, reserva_id, uuid_operacion_offline) FROM stdin;
1	1	VT-00001	4	2	DIGITAL	PENDIENTE_PAGO	200.40	2026-11-08 05:14:36.963308+00	\N	\N	\N	\N
2	1	VT-00002	4	2	DIGITAL	PENDIENTE_PAGO	200.40	2026-11-08 05:29:14.928542+00	\N	\N	\N	\N
3	1	VT-00003	4	2	DIGITAL	PENDIENTE_PAGO	200.40	2026-11-08 05:43:02.875753+00	\N	\N	\N	\N
4	1	VT-00004	4	2	DIGITAL	PAGADA	200.40	2026-11-08 05:48:49.901528+00	\N	\N	\N	\N
5	1	VT-00005	\N	2	PRESENCIAL	PENDIENTE_PAGO	200.40	2026-11-09 02:54:44.420721+00	8	DIRECTA	\N	\N
6	1	VT-00006	\N	2	PRESENCIAL	PENDIENTE_PAGO	200.40	2026-11-09 02:55:52.219075+00	8	DIRECTA	\N	\N
7	1	VT-00007	\N	2	PRESENCIAL	PENDIENTE_PAGO	200.40	2026-11-09 03:06:19.667991+00	2	DIRECTA	\N	\N
8	1	VT-00008	\N	2	PRESENCIAL	PENDIENTE_PAGO	200.40	2026-11-09 03:06:36.00411+00	2	DIRECTA	\N	\N
9	1	VT-00009	\N	2	PRESENCIAL	PENDIENTE_PAGO	200.40	2026-11-09 03:10:58.544009+00	2	DIRECTA	\N	\N
10	1	VT-00010	\N	2	PRESENCIAL	PENDIENTE_PAGO	200.40	2026-11-09 03:11:27.674485+00	2	DIRECTA	\N	\N
11	1	VT-00011	\N	2	PRESENCIAL	PAGADA	200.40	2026-11-09 03:14:07.58986+00	2	DIRECTA	\N	\N
12	1	VT-00012	\N	2	PRESENCIAL	PAGADA	200.40	2026-11-09 03:16:57.575263+00	2	DIRECTA	\N	uuid-venta-con-guardado
13	1	VT-00013	\N	2	PRESENCIAL	PAGADA	200.40	2026-11-09 03:18:41.023691+00	2	DIRECTA	\N	uuid-venta-segundo-intento
14	1	VT-00014	\N	2	PRESENCIAL	PAGADA	200.40	2026-11-09 03:24:55.675179+00	8	DIRECTA	\N	7b61289b-1a1a-43ab-88db-b54e5d928146
15	1	VT-00015	\N	2	PRESENCIAL	PAGADA	200.40	2026-11-09 05:08:32.507387+00	8	DIRECTA	\N	a33a2b7a-0ac1-4151-acdb-f5df8782d08b
16	1	VT-00016	\N	2	PRESENCIAL	PAGADA	200.00	2026-11-09 05:13:25.269212+00	8	DIRECTA	\N	213a6800-d930-48b1-8906-5e18af418dc7
\.


--
-- Name: carrito_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.carrito_items_id_seq', 5, true);


--
-- Name: carritos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.carritos_id_seq', 1, true);


--
-- Name: categorias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.categorias_id_seq', 2, true);


--
-- Name: ciudades_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.ciudades_id_seq', 3, true);


--
-- Name: colecciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.colecciones_id_seq', 2, true);


--
-- Name: colores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.colores_id_seq', 2, true);


--
-- Name: detalles_recepcion_mercaderia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.detalles_recepcion_mercaderia_id_seq', 2, true);


--
-- Name: devoluciones_cambios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.devoluciones_cambios_id_seq', 1, false);


--
-- Name: empresas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.empresas_id_seq', 3, true);


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

SELECT pg_catalog.setval('public.pagos_id_seq', 9, true);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 1, false);


--
-- Name: planes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.planes_id_seq', 2, true);


--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.producto_imagenes_id_seq', 1, true);


--
-- Name: producto_variantes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.producto_variantes_id_seq', 2, true);


--
-- Name: productos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.productos_id_seq', 10, true);


--
-- Name: productos_proveedor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.productos_proveedor_id_seq', 1, false);


--
-- Name: promociones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.promociones_id_seq', 3, true);


--
-- Name: proveedores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.proveedores_id_seq', 2, true);


--
-- Name: recepciones_mercaderia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.recepciones_mercaderia_id_seq', 2, true);


--
-- Name: reserva_detalles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.reserva_detalles_id_seq', 12, true);


--
-- Name: reservas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.reservas_id_seq', 12, true);


--
-- Name: stock_sucursal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.stock_sucursal_id_seq', 2, true);


--
-- Name: sucursales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.sucursales_id_seq', 2, true);


--
-- Name: suscripciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.suscripciones_id_seq', 2, true);


--
-- Name: tallas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.tallas_id_seq', 2, true);


--
-- Name: temporadas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.temporadas_id_seq', 2, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 9, true);


--
-- Name: venta_detalles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.venta_detalles_id_seq', 16, true);


--
-- Name: ventas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.ventas_id_seq', 16, true);


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
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


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
-- Name: empresas empresas_nombre_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_nombre_key UNIQUE (nombre);


--
-- Name: empresas empresas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_pkey PRIMARY KEY (id);


--
-- Name: empresas empresas_slug_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_slug_key UNIQUE (slug);


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
-- Name: pagos pagos_stripe_checkout_session_id_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_stripe_checkout_session_id_key UNIQUE (stripe_checkout_session_id);


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
-- Name: reservas reservas_codigo_reserva_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_codigo_reserva_key UNIQUE (codigo_reserva);


--
-- Name: reservas reservas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_pkey PRIMARY KEY (id);


--
-- Name: reservas reservas_uuid_operacion_offline_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_uuid_operacion_offline_key UNIQUE (uuid_operacion_offline);


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
-- Name: tallas tallas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT tallas_pkey PRIMARY KEY (id);


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
-- Name: categorias uq_categoria_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT uq_categoria_empresa_nombre UNIQUE (empresa_id, nombre);


--
-- Name: ciudades uq_ciudad_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT uq_ciudad_empresa_nombre UNIQUE (empresa_id, nombre);


--
-- Name: colecciones uq_coleccion_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT uq_coleccion_empresa_nombre UNIQUE (empresa_id, nombre);


--
-- Name: colores uq_color_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colores
    ADD CONSTRAINT uq_color_empresa_nombre UNIQUE (empresa_id, nombre);


--
-- Name: proveedores uq_proveedor_empresa_razon_social; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT uq_proveedor_empresa_razon_social UNIQUE (empresa_id, razon_social);


--
-- Name: sucursales uq_sucursal_empresa_id; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT uq_sucursal_empresa_id UNIQUE (empresa_id, id);


--
-- Name: tallas uq_talla_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT uq_talla_empresa_nombre UNIQUE (empresa_id, nombre);


--
-- Name: temporadas uq_temporada_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.temporadas
    ADD CONSTRAINT uq_temporada_empresa_nombre UNIQUE (empresa_id, nombre);


--
-- Name: usuarios uq_usuario_empresa_correo; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT uq_usuario_empresa_correo UNIQUE (empresa_id, correo);


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
-- Name: ventas ventas_codigo_venta_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_codigo_venta_key UNIQUE (codigo_venta);


--
-- Name: ventas ventas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_pkey PRIMARY KEY (id);


--
-- Name: ventas ventas_uuid_operacion_offline_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_uuid_operacion_offline_key UNIQUE (uuid_operacion_offline);


--
-- Name: idx_empresa_fecha; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_empresa_fecha ON public.operaciones_sincronizacion_log USING btree (empresa_id, fecha_intento);


--
-- Name: idx_empresa_tipo_estado; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_empresa_tipo_estado ON public.operaciones_sincronizacion_log USING btree (empresa_id, tipo_operacion, estado_resultado);


--
-- Name: idx_uuid_empresa; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_uuid_empresa ON public.operaciones_sincronizacion_log USING btree (uuid_operacion_offline, empresa_id);


--
-- Name: ix_password_reset_tokens_token_hash; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE UNIQUE INDEX ix_password_reset_tokens_token_hash ON public.password_reset_tokens USING btree (token_hash);


--
-- Name: ix_password_reset_tokens_usuario_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX ix_password_reset_tokens_usuario_id ON public.password_reset_tokens USING btree (usuario_id);


--
-- Name: ix_usuarios_correo; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX ix_usuarios_correo ON public.usuarios USING btree (correo);


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
-- Name: categorias categorias_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: ciudades ciudades_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT ciudades_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: colecciones colecciones_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT colecciones_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: colecciones colecciones_temporada_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colecciones
    ADD CONSTRAINT colecciones_temporada_id_fkey FOREIGN KEY (temporada_id) REFERENCES public.temporadas(id);


--
-- Name: colores colores_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.colores
    ADD CONSTRAINT colores_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


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
-- Name: pagos pagos_cajero_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_cajero_id_fkey FOREIGN KEY (cajero_id) REFERENCES public.usuarios(id);


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
-- Name: productos productos_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


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
-- Name: promociones promociones_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promociones
    ADD CONSTRAINT promociones_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: proveedores proveedores_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT proveedores_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


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
-- Name: reserva_detalles reserva_detalles_reserva_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reserva_detalles
    ADD CONSTRAINT reserva_detalles_reserva_id_fkey FOREIGN KEY (reserva_id) REFERENCES public.reservas(id) ON DELETE CASCADE;


--
-- Name: reservas reservas_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id);


--
-- Name: reservas reservas_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: reservas reservas_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


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
-- Name: sucursales sucursales_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT sucursales_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


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
-- Name: tallas tallas_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.tallas
    ADD CONSTRAINT tallas_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: temporadas temporadas_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.temporadas
    ADD CONSTRAINT temporadas_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: usuarios usuarios_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


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
-- Name: venta_detalles venta_detalles_carrito_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.venta_detalles
    ADD CONSTRAINT venta_detalles_carrito_item_id_fkey FOREIGN KEY (carrito_item_id) REFERENCES public.carrito_items(id) ON DELETE SET NULL;


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
-- Name: ventas ventas_cajero_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_cajero_id_fkey FOREIGN KEY (cajero_id) REFERENCES public.usuarios(id);


--
-- Name: ventas ventas_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id);


--
-- Name: ventas ventas_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: ventas ventas_reserva_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_reserva_id_fkey FOREIGN KEY (reserva_id) REFERENCES public.reservas(id) ON DELETE SET NULL;


--
-- Name: ventas ventas_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id);


--
-- PostgreSQL database dump complete
--

\unrestrict iSgIEp3FBFCxSbZjxofBpTvmLEIpo3T1ywJ77DMIjCgKHKl9rtaKgt0mjUZkIHd

