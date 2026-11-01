--
-- PostgreSQL database dump
--

\restrict hKdDthCywfhcg6bK6yxJoWQpev6GjP435sH8K5Stnsfz95hxU5tI6OHNjYv1w4x

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO fashionstore;

--
-- Name: carrito_items; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.carrito_items (
    id integer NOT NULL,
    carrito_id integer NOT NULL,
    producto_variante_id integer NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric(10,2),
    seleccionado boolean DEFAULT true,
    fecha_agregado timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT carrito_items_cantidad_check CHECK ((cantidad > 0))
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
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
    is_active boolean DEFAULT true NOT NULL
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
    empresa_id integer NOT NULL,
    temporada_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    is_active boolean DEFAULT true NOT NULL,
    es_destacada_inicio boolean DEFAULT false NOT NULL,
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
    nombre character varying(50) NOT NULL,
    codigo_hex character varying(7),
    is_active boolean DEFAULT true NOT NULL
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
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT detalles_recepcion_mercaderia_cantidad_recibida_check CHECK ((cantidad_recibida > 0))
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
    variante_original_id integer NOT NULL,
    variante_nueva_id integer,
    cajero_id integer NOT NULL,
    sucursal_id integer NOT NULL,
    tipo character varying(20) NOT NULL,
    motivo character varying(30) NOT NULL,
    cantidad integer NOT NULL,
    monto_reembolso numeric(10,2),
    metodo_reembolso character varying(20),
    estado_reembolso character varying(20) DEFAULT 'REGISTRADO'::character varying,
    observaciones text,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT devoluciones_cambios_cantidad_check CHECK ((cantidad > 0))
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
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
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
    tipo character varying(20) NOT NULL,
    cantidad integer NOT NULL,
    stock_anterior integer NOT NULL,
    stock_resultante integer NOT NULL,
    motivo text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT movimientos_inventario_cantidad_check CHECK ((cantidad > 0)),
    CONSTRAINT movimientos_inventario_stock_anterior_check CHECK ((stock_anterior >= 0)),
    CONSTRAINT movimientos_inventario_stock_resultante_check CHECK ((stock_resultante >= 0))
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
-- Name: pagos; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.pagos (
    id integer NOT NULL,
    venta_id integer NOT NULL,
    cajero_id integer,
    proveedor character varying(20) NOT NULL,
    estado character varying(20) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    tipo_tarjeta character varying(10),
    monto numeric(10,2) NOT NULL,
    stripe_checkout_session_id character varying(255),
    referencia_externa character varying(255),
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
    token_hash character varying(255) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
    precio numeric(10,2) DEFAULT 0 NOT NULL,
    duracion_dias integer DEFAULT 30 NOT NULL,
    limite_sucursales integer DEFAULT 1 NOT NULL,
    limite_usuarios integer DEFAULT 5 NOT NULL,
    permite_prueba_gratuita boolean DEFAULT false NOT NULL,
    duracion_prueba_dias integer,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    gestion_productos boolean DEFAULT true NOT NULL,
    gestion_ventas boolean DEFAULT true NOT NULL,
    reservas boolean DEFAULT true NOT NULL,
    operacion_offline boolean DEFAULT true NOT NULL,
    reportes_convencionales boolean DEFAULT true NOT NULL,
    reportes_generativos_ia boolean DEFAULT false NOT NULL
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
    empresa_id integer NOT NULL,
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
    orden smallint DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
    empresa_id integer NOT NULL,
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
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true NOT NULL
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
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
    razon_social character varying(150),
    sku_proveedor character varying(100),
    descripcion text,
    precio_sugerido numeric(10,2),
    estado character varying(20) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
    empresa_id integer NOT NULL,
    producto_id integer NOT NULL
);


ALTER TABLE public.promocion_productos OWNER TO fashionstore;

--
-- Name: promociones; Type: TABLE; Schema: public; Owner: fashionstore
--

CREATE TABLE public.promociones (
    id integer NOT NULL,
    empresa_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    porcentaje_descuento numeric(5,2) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    estado character varying(20),
    activa boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT promociones_check CHECK ((fecha_fin >= fecha_inicio)),
    CONSTRAINT promociones_porcentaje_descuento_check CHECK (((porcentaje_descuento > (0)::numeric) AND (porcentaje_descuento < (100)::numeric)))
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
    is_active boolean DEFAULT true NOT NULL
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
    numero_remision character varying(100) NOT NULL,
    fecha_recepcion date DEFAULT CURRENT_DATE NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
    estado character varying(20) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    precio_unitario numeric(10,2),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT reserva_detalles_cantidad_check CHECK ((cantidad > 0))
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
    cliente_id integer NOT NULL,
    codigo_reserva character varying(50) NOT NULL,
    sucursal_id integer NOT NULL,
    estado_general character varying(20) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    fecha_reserva date DEFAULT CURRENT_DATE NOT NULL,
    hora_inicio time without time zone,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stock_sucursal_cantidad_check CHECK ((cantidad >= 0)),
    CONSTRAINT stock_sucursal_stock_reservado_check CHECK ((stock_reservado >= 0))
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
    en_prueba boolean DEFAULT false NOT NULL,
    fecha_fin_prueba timestamp with time zone,
    activa boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
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
    nombre character varying(20) NOT NULL,
    is_active boolean DEFAULT true NOT NULL
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
    nombre character varying(100) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    is_active boolean DEFAULT true NOT NULL
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
    rol character varying(20) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
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
    carrito_item_id integer,
    cantidad integer NOT NULL,
    precio_unitario numeric(10,2) NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT venta_detalles_cantidad_check CHECK ((cantidad > 0))
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
    cliente_id integer,
    cajero_id integer,
    reserva_id integer,
    codigo_venta character varying(50) NOT NULL,
    sucursal_id integer NOT NULL,
    tipo character varying(20) DEFAULT 'PRESENCIAL'::character varying NOT NULL,
    estado character varying(20) DEFAULT 'PENDIENTE_PAGO'::character varying NOT NULL,
    origen character varying(20) DEFAULT 'DIRECTA'::character varying NOT NULL,
    monto_total numeric(10,2) NOT NULL,
    monto_pagado numeric(10,2) DEFAULT 0,
    descuento_total numeric(10,2) DEFAULT 0,
    observaciones text,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
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
b3ce5bc51b48
\.


--
-- Data for Name: carrito_items; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.carrito_items (id, carrito_id, producto_variante_id, cantidad, precio_unitario, seleccionado, fecha_agregado) FROM stdin;
\.


--
-- Data for Name: carritos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.carritos (id, cliente_id, fecha_creacion, fecha_actualizacion) FROM stdin;
\.


--
-- Data for Name: categorias; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.categorias (id, empresa_id, nombre, imagen_url, is_active) FROM stdin;
1	2	Camisetas	\N	t
2	2	Pantalones	\N	t
3	2	Chaquetas	\N	t
\.


--
-- Data for Name: ciudades; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.ciudades (id, nombre, is_active, departamento, empresa_id) FROM stdin;
1	Bogotá	t	Cundinamarca	\N
2	Medellín	t	Antioquia	\N
3	Cali	t	Valle del Cauca	\N
4	Barranquilla	t	Atlántico	\N
\.


--
-- Data for Name: colecciones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.colecciones (id, empresa_id, temporada_id, nombre, descripcion, is_active, es_destacada_inicio, imagen_destacada_url) FROM stdin;
1	2	1	Urban	........	t	f	\N
\.


--
-- Data for Name: colores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.colores (id, empresa_id, nombre, codigo_hex, is_active) FROM stdin;
1	2	Negro	#000000	t
2	2	Blanco	#FFFFFF	t
3	2	Azul	#0000FF	t
4	2	Rojo	#FF0000	t
\.


--
-- Data for Name: detalles_recepcion_mercaderia; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.detalles_recepcion_mercaderia (id, recepcion_id, producto_variante_id, cantidad_recibida, created_at) FROM stdin;
\.


--
-- Data for Name: devoluciones_cambios; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.devoluciones_cambios (id, venta_id, venta_detalle_id, variante_original_id, variante_nueva_id, cajero_id, sucursal_id, tipo, motivo, cantidad, monto_reembolso, metodo_reembolso, estado_reembolso, observaciones, fecha_creacion, updated_at) FROM stdin;
\.


--
-- Data for Name: empresas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.empresas (id, nombre, slug, razon_social, correo, telefono, is_active, created_at, updated_at) FROM stdin;
2	FashionStore	fashionstore	FashionStore SAS	info@fashionstore.com	+573001234567	t	2026-10-31 16:17:38.135034+00	2026-10-31 16:17:38.135034+00
3	TestCorp	testcorp	TestCorp SAS	info@testcorp.com	+573009876543	t	2026-10-31 16:34:25.118611+00	2026-10-31 16:34:25.118611+00
\.


--
-- Data for Name: movimientos_inventario; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.movimientos_inventario (id, sucursal_id, producto_variante_id, usuario_id, tipo, cantidad, stock_anterior, stock_resultante, motivo, created_at) FROM stdin;
\.


--
-- Data for Name: pagos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.pagos (id, venta_id, cajero_id, proveedor, estado, tipo_tarjeta, monto, stripe_checkout_session_id, referencia_externa, fecha_creacion, updated_at) FROM stdin;
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.password_reset_tokens (id, usuario_id, token_hash, expires_at, used_at, created_at) FROM stdin;
\.


--
-- Data for Name: planes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.planes (id, nombre, slug, descripcion, precio, duracion_dias, limite_sucursales, limite_usuarios, permite_prueba_gratuita, duracion_prueba_dias, is_active, created_at, updated_at, gestion_productos, gestion_ventas, reservas, operacion_offline, reportes_convencionales, reportes_generativos_ia) FROM stdin;
3	Plan Profesional	plan-profesional	Plan para medianas empresas	299.99	30	10	50	f	\N	t	2026-10-31 16:34:25.090726+00	2026-10-31 16:34:25.090726+00	t	t	t	t	t	t
1	Plan Gratuito	plan-gratuito	Plan de prueba con características limitadas	0.00	30	1	5	t	30	t	2026-10-31 16:34:25.090726+00	2026-10-31 16:34:25.090726+00	t	t	t	t	t	f
4	BASICO	basico	Ofrece...	500.00	30	2	20	f	\N	t	2026-10-31 18:04:59.716987+00	2026-10-31 21:51:18.610488+00	t	t	t	t	f	f
\.


--
-- Data for Name: producto_colores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_colores (producto_id, empresa_id, color_id) FROM stdin;
1	2	3
2	2	3
3	2	3
\.


--
-- Data for Name: producto_imagenes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_imagenes (id, producto_id, url, orden, created_at) FROM stdin;
\.


--
-- Data for Name: producto_tallas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_tallas (producto_id, empresa_id, talla_id) FROM stdin;
1	2	4
1	2	3
2	2	4
2	2	3
3	2	4
\.


--
-- Data for Name: producto_variantes; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.producto_variantes (id, producto_id, talla_id, color_id, created_at, is_active) FROM stdin;
1	1	3	3	2026-11-01 01:05:57.534589+00	t
2	1	4	3	2026-11-01 01:05:57.534589+00	t
3	2	3	3	2026-11-01 01:06:07.653023+00	t
4	2	4	3	2026-11-01 01:06:07.653023+00	t
5	3	4	3	2026-11-01 01:19:25.601719+00	t
\.


--
-- Data for Name: productos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.productos (id, empresa_id, nombre, descripcion, proveedor_id, producto_proveedor_id, categoria_id, temporada_id, coleccion_id, precio_venta, imagen_principal_url, is_active, created_at, updated_at) FROM stdin;
1	2	CHAQUETA CUERO	SDKJCWKSNLKAS	1	\N	3	1	1	500.00	\N	t	2026-11-01 01:05:57.534589+00	2026-11-01 01:05:57.534589+00
2	2	CHAQUETA CUERO	SDKJCWKSNLKAS	1	\N	3	1	1	500.00	\N	t	2026-11-01 01:06:07.653023+00	2026-11-01 01:06:07.653023+00
3	2	Test Producto POST	Test description	1	\N	1	1	1	100.00	\N	t	2026-11-01 01:19:25.601719+00	2026-11-01 01:19:25.601719+00
\.


--
-- Data for Name: productos_proveedor; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.productos_proveedor (id, proveedor_id, razon_social, sku_proveedor, descripcion, precio_sugerido, estado, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: promocion_productos; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.promocion_productos (promocion_id, empresa_id, producto_id) FROM stdin;
\.


--
-- Data for Name: promociones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.promociones (id, empresa_id, nombre, descripcion, porcentaje_descuento, fecha_inicio, fecha_fin, estado, activa, fecha_creacion, updated_at) FROM stdin;
\.


--
-- Data for Name: proveedores; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.proveedores (id, empresa_id, razon_social, nombre_contacto, correo, telefono, is_active) FROM stdin;
1	2	SHEIN	Lourdes Lima	cristelvicente981@gmail.com	12345678	t
\.


--
-- Data for Name: recepciones_mercaderia; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.recepciones_mercaderia (id, proveedor_id, sucursal_id, usuario_id, numero_remision, fecha_recepcion, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: reserva_detalles; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.reserva_detalles (id, reserva_id, producto_variante_id, cantidad, estado, precio_unitario, created_at) FROM stdin;
\.


--
-- Data for Name: reservas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.reservas (id, empresa_id, cliente_id, codigo_reserva, sucursal_id, estado_general, fecha_reserva, hora_inicio, fecha_creacion, updated_at) FROM stdin;
\.


--
-- Data for Name: stock_sucursal; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.stock_sucursal (id, sucursal_id, producto_variante_id, cantidad, stock_reservado, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sucursales; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.sucursales (id, nombre, ciudad_id, direccion, telefono, is_active, empresa_id) FROM stdin;
1	Sucursal Bogotá	1	Cra 7 #100-23, Bogotá	+573001111111	t	2
2	Sucursal Principal	2	Cra 50 #54-10, Medellín	+573009999999	t	3
\.


--
-- Data for Name: suscripciones; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.suscripciones (id, empresa_id, plan_id, fecha_inicio, fecha_vencimiento, en_prueba, fecha_fin_prueba, activa, created_at, updated_at) FROM stdin;
1	2	1	2026-10-31 16:34:25.100908+00	2026-11-30 16:34:25.100908+00	t	\N	t	2026-10-31 16:34:25.100908+00	2026-10-31 16:34:25.100908+00
\.


--
-- Data for Name: tallas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.tallas (id, empresa_id, nombre, is_active) FROM stdin;
1	2	XS	t
2	2	S	t
3	2	M	t
4	2	L	t
5	2	XL	t
\.


--
-- Data for Name: temporadas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.temporadas (id, empresa_id, nombre, fecha_inicio, fecha_fin, is_active) FROM stdin;
1	2	PRIMAVERA	2026-10-31	2026-11-06	t
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.usuarios (id, empresa_id, nombre, correo, password_hash, rol, is_active, created_at, sucursal_id, proveedor_id, telefono) FROM stdin;
1	2	Admin	admin@fashionstore.com	$2b$12$xmvT9F/zKHL0DtSzTdGbgOCJAiS9dEBk/wsX6wtIsIUoC/EmeyJSO	ADMINISTRADOR	t	2026-10-31 16:18:29.432606+00	\N	\N	+573001234567
2	\N	Administrador Global FashionStore	superadmin@fashionstore.com	$2b$12$iaGnldreu.Xj0PONs1FBqeieQt04u22CUUE9N.vW8GNdEMacmM0em	SUPERADMIN	t	2026-10-31 16:41:53.530343+00	\N	\N	\N
\.


--
-- Data for Name: venta_detalles; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.venta_detalles (id, venta_id, producto_variante_id, carrito_item_id, cantidad, precio_unitario, subtotal, created_at) FROM stdin;
\.


--
-- Data for Name: ventas; Type: TABLE DATA; Schema: public; Owner: fashionstore
--

COPY public.ventas (id, empresa_id, cliente_id, cajero_id, reserva_id, codigo_venta, sucursal_id, tipo, estado, origen, monto_total, monto_pagado, descuento_total, observaciones, fecha_creacion, updated_at) FROM stdin;
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

SELECT pg_catalog.setval('public.categorias_id_seq', 3, true);


--
-- Name: ciudades_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.ciudades_id_seq', 4, true);


--
-- Name: colecciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.colecciones_id_seq', 1, true);


--
-- Name: colores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.colores_id_seq', 4, true);


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

SELECT pg_catalog.setval('public.empresas_id_seq', 3, true);


--
-- Name: movimientos_inventario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.movimientos_inventario_id_seq', 1, false);


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

SELECT pg_catalog.setval('public.planes_id_seq', 5, true);


--
-- Name: producto_imagenes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.producto_imagenes_id_seq', 1, false);


--
-- Name: producto_variantes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.producto_variantes_id_seq', 5, true);


--
-- Name: productos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.productos_id_seq', 3, true);


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

SELECT pg_catalog.setval('public.proveedores_id_seq', 1, true);


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

SELECT pg_catalog.setval('public.sucursales_id_seq', 2, true);


--
-- Name: suscripciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.suscripciones_id_seq', 1, true);


--
-- Name: tallas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.tallas_id_seq', 5, true);


--
-- Name: temporadas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.temporadas_id_seq', 1, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fashionstore
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 2, true);


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
-- Name: carritos carritos_cliente_id_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carritos
    ADD CONSTRAINT carritos_cliente_id_key UNIQUE (cliente_id);


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
-- Name: password_reset_tokens password_reset_tokens_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_hash_key UNIQUE (token_hash);


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
    ADD CONSTRAINT producto_colores_pkey PRIMARY KEY (producto_id, empresa_id, color_id);


--
-- Name: producto_imagenes producto_imagenes_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_imagenes
    ADD CONSTRAINT producto_imagenes_pkey PRIMARY KEY (id);


--
-- Name: producto_tallas producto_tallas_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_pkey PRIMARY KEY (producto_id, empresa_id, talla_id);


--
-- Name: producto_variantes producto_variantes_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_pkey PRIMARY KEY (id);


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
    ADD CONSTRAINT promocion_productos_pkey PRIMARY KEY (promocion_id, empresa_id, producto_id);


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
-- Name: recepciones_mercaderia recepciones_mercaderia_numero_remision_key; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.recepciones_mercaderia
    ADD CONSTRAINT recepciones_mercaderia_numero_remision_key UNIQUE (numero_remision);


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
-- Name: stock_sucursal stock_sucursal_pkey; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT stock_sucursal_pkey PRIMARY KEY (id);


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
-- Name: carrito_items uq_carrito_item; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.carrito_items
    ADD CONSTRAINT uq_carrito_item UNIQUE (carrito_id, producto_variante_id);


--
-- Name: categorias uq_categoria_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT uq_categoria_empresa_nombre UNIQUE (empresa_id, nombre);


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
-- Name: producto_variantes uq_producto_variante_unique; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT uq_producto_variante_unique UNIQUE (producto_id, talla_id, color_id);


--
-- Name: promociones uq_promocion_empresa_nombre; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promociones
    ADD CONSTRAINT uq_promocion_empresa_nombre UNIQUE (empresa_id, nombre);


--
-- Name: proveedores uq_proveedor_empresa_razon_social; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT uq_proveedor_empresa_razon_social UNIQUE (empresa_id, razon_social);


--
-- Name: stock_sucursal uq_stock_sucursal; Type: CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.stock_sucursal
    ADD CONSTRAINT uq_stock_sucursal UNIQUE (sucursal_id, producto_variante_id);


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
-- Name: idx_categorias_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_categorias_empresa_id ON public.categorias USING btree (empresa_id);


--
-- Name: idx_colecciones_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_colecciones_empresa_id ON public.colecciones USING btree (empresa_id);


--
-- Name: idx_colores_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_colores_empresa_id ON public.colores USING btree (empresa_id);


--
-- Name: idx_devoluciones_venta_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_devoluciones_venta_id ON public.devoluciones_cambios USING btree (venta_id);


--
-- Name: idx_pagos_venta_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_pagos_venta_id ON public.pagos USING btree (venta_id);


--
-- Name: idx_password_reset_tokens_hash; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_password_reset_tokens_hash ON public.password_reset_tokens USING btree (token_hash);


--
-- Name: idx_password_reset_tokens_usuario_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_password_reset_tokens_usuario_id ON public.password_reset_tokens USING btree (usuario_id);


--
-- Name: idx_productos_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_productos_empresa_id ON public.productos USING btree (empresa_id);


--
-- Name: idx_reservas_cliente_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_reservas_cliente_id ON public.reservas USING btree (cliente_id);


--
-- Name: idx_reservas_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_reservas_empresa_id ON public.reservas USING btree (empresa_id);


--
-- Name: idx_stock_sucursal_sucursal; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_stock_sucursal_sucursal ON public.stock_sucursal USING btree (sucursal_id);


--
-- Name: idx_tallas_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_tallas_empresa_id ON public.tallas USING btree (empresa_id);


--
-- Name: idx_temporadas_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_temporadas_empresa_id ON public.temporadas USING btree (empresa_id);


--
-- Name: idx_usuarios_correo; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_usuarios_correo ON public.usuarios USING btree (correo);


--
-- Name: idx_usuarios_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_usuarios_empresa_id ON public.usuarios USING btree (empresa_id);


--
-- Name: idx_venta_detalles_venta_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_venta_detalles_venta_id ON public.venta_detalles USING btree (venta_id);


--
-- Name: idx_ventas_cliente_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_ventas_cliente_id ON public.ventas USING btree (cliente_id);


--
-- Name: idx_ventas_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX idx_ventas_empresa_id ON public.ventas USING btree (empresa_id);


--
-- Name: ix_suscripciones_empresa_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX ix_suscripciones_empresa_id ON public.suscripciones USING btree (empresa_id);


--
-- Name: ix_suscripciones_plan_id; Type: INDEX; Schema: public; Owner: fashionstore
--

CREATE INDEX ix_suscripciones_plan_id ON public.suscripciones USING btree (plan_id);


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
-- Name: categorias categorias_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


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
-- Name: ciudades fk_ciudades_empresa; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.ciudades
    ADD CONSTRAINT fk_ciudades_empresa FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: sucursales fk_sucursales_empresa; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT fk_sucursales_empresa FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


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
    ADD CONSTRAINT password_reset_tokens_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: producto_colores producto_colores_color_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_color_id_fkey FOREIGN KEY (color_id) REFERENCES public.colores(id) ON DELETE CASCADE;


--
-- Name: producto_colores producto_colores_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: producto_colores producto_colores_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_colores
    ADD CONSTRAINT producto_colores_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- Name: producto_imagenes producto_imagenes_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_imagenes
    ADD CONSTRAINT producto_imagenes_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- Name: producto_tallas producto_tallas_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: producto_tallas producto_tallas_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- Name: producto_tallas producto_tallas_talla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_tallas
    ADD CONSTRAINT producto_tallas_talla_id_fkey FOREIGN KEY (talla_id) REFERENCES public.tallas(id) ON DELETE CASCADE;


--
-- Name: producto_variantes producto_variantes_color_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_color_id_fkey FOREIGN KEY (color_id) REFERENCES public.colores(id);


--
-- Name: producto_variantes producto_variantes_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.producto_variantes
    ADD CONSTRAINT producto_variantes_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


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
-- Name: promocion_productos promocion_productos_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT promocion_productos_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: promocion_productos promocion_productos_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fashionstore
--

ALTER TABLE ONLY public.promocion_productos
    ADD CONSTRAINT promocion_productos_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


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

\unrestrict hKdDthCywfhcg6bK6yxJoWQpev6GjP435sH8K5Stnsfz95hxU5tI6OHNjYv1w4x

