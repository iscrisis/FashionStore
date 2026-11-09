import { Injectable } from '@angular/core';

function hash(str: string): number {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    h = (h << 5) - h + char;
    h = h & h; // Convert to 32bit integer
  }
  return Math.abs(h);
}

export interface OfflinePreparacion {
  sucursal: {
    id: number;
    nombre: string;
    id_ciudad: number | null;
    ciudad: string | null;
    es_activa: boolean;
  };
  ciudades: Array<{
    id: number;
    nombre: string;
  }>;
  productos: Array<{
    id: number;
    nombre: string;
    categoria_id: number;
    coleccion_id: number;
    es_activo: boolean;
    precio_base: number;
    precio_final: number;
    en_promocion: boolean;
    porcentaje_descuento: number | null;
    imagen_principal_url: string | null;
    variantes: Array<{
      id: number;
      producto_id: number;
      talla_id: number;
      talla_nombre: string;
      color_id: number;
      color_nombre: string;
      precio: number;
      stock_disponible: number;
    }>;
  }>;
  tallas: Array<{
    id: number;
    nombre: string;
  }>;
  colores: Array<{
    id: number;
    nombre: string;
  }>;
  categorias: Array<{
    id: number;
    nombre: string;
  }>;
  colecciones: Array<{
    id: number;
    nombre: string;
    descripcion: string | null;
    imagen_destacada_url: string | null;
    es_destacada_inicio: boolean;
    temporada: { id: number; nombre: string };
  }>;
  clientes_minimos: Array<{
    id: number;
    nombre: string;
    correo: string;
  }>;
  metadata: {
    fecha_preparacion: string;
    version: number;
    estado: string;
    empresa_id: number;
    sucursal_id: number;
  };
}

@Injectable({
  providedIn: 'root',
})
export class OfflineStorageService {
  private dbName = 'fashionstore_offline';
  private db: IDBDatabase | null = null;
  private readonly dbReady: Promise<void>;

  constructor() {
    this.dbReady = this.initializeDB();
  }

  private initializeDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 8);

      request.onerror = () => {
        const error = new Error('Error al abrir IndexedDB');
        console.error(error);
        reject(error);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Crear object stores si no existen
        if (!db.objectStoreNames.contains('offline_preparacion')) {
          const preparacionStore = db.createObjectStore('offline_preparacion', { keyPath: 'id' });
          preparacionStore.createIndex('empresa_sucursal', ['empresa_id', 'sucursal_id'], {
            unique: true,
          });
          console.log('Object Store offline_preparacion creado');
        }

        if (!db.objectStoreNames.contains('offline_ciudades')) {
          const ciudadesStore = db.createObjectStore('offline_ciudades', { keyPath: 'id' });
          ciudadesStore.createIndex('empresa_id', 'empresa_id');
          console.log('Object Store offline_ciudades creado');
        }

        if (!db.objectStoreNames.contains('offline_reservas')) {
          const reservasStore = db.createObjectStore('offline_reservas', { keyPath: 'uuid' });
          reservasStore.createIndex('empresa_id', 'empresa_id');
          reservasStore.createIndex('estado_sync', 'estado_sync');
          console.log('Object Store offline_reservas creado');
        }

        if (!db.objectStoreNames.contains('offline_reserva_detalles')) {
          const detallesStore = db.createObjectStore('offline_reserva_detalles', { keyPath: 'uuid' });
          detallesStore.createIndex('reserva_uuid', 'reserva_uuid');
          console.log('Object Store offline_reserva_detalles creado');
        }

        // CU9 — Venta presencial offline
        if (!db.objectStoreNames.contains('offline_ventas')) {
          const ventasStore = db.createObjectStore('offline_ventas', { keyPath: 'uuid' });
          ventasStore.createIndex('empresa_id', 'empresa_id');
          ventasStore.createIndex('estado_sync', 'estado_sync');
          console.log('Object Store offline_ventas creado');
        }

        if (!db.objectStoreNames.contains('offline_venta_detalles')) {
          const detallesVentaStore = db.createObjectStore('offline_venta_detalles', { keyPath: 'uuid' });
          detallesVentaStore.createIndex('venta_uuid', 'venta_uuid');
          console.log('Object Store offline_venta_detalles creado');
        }

        if (!db.objectStoreNames.contains('offline_pago_efectivo')) {
          const pagoStore = db.createObjectStore('offline_pago_efectivo', { keyPath: 'venta_uuid' });
          pagoStore.createIndex('empresa_id', 'empresa_id');
          console.log('Object Store offline_pago_efectivo creado');
        }

        // CU27 — Historial de compras confirmadas descargadas (Cliente y Cajero)
        if (!db.objectStoreNames.contains('historial_ventas_confirmadas')) {
          const historialStore = db.createObjectStore('historial_ventas_confirmadas', { keyPath: 'venta_id' });
          historialStore.createIndex('cliente_id', 'cliente_id');
          historialStore.createIndex('empresa_id', 'empresa_id');
          historialStore.createIndex('empresa_cliente', ['empresa_id', 'cliente_id'], { unique: false });
          historialStore.createIndex('empresa_sucursal', ['empresa_id', 'sucursal_id'], { unique: false });
          console.log('Object Store historial_ventas_confirmadas creado');
        } else if ((event as any).oldVersion < 7) {
          // V7: Agregar índice empresa_sucursal para búsquedas del CAJERO sin recrear tabla
          try {
            const store = (event.target as IDBOpenDBRequest).transaction?.objectStore('historial_ventas_confirmadas');
            if (store && !Array.from(store.indexNames).includes('empresa_sucursal')) {
              store.createIndex('empresa_sucursal', ['empresa_id', 'sucursal_id'], { unique: false });
              console.log('Índice empresa_sucursal agregado a historial_ventas_confirmadas');
            }
          } catch (e) {
            console.log('Índice empresa_sucursal ya existe o error al crear');
          }
        }

        // V8: CU18 — Historial de reservas confirmadas descargadas (Cliente)
        if (!db.objectStoreNames.contains('historial_reservas_confirmadas')) {
          const historialReservasStore = db.createObjectStore('historial_reservas_confirmadas', { keyPath: 'reserva_id' });
          historialReservasStore.createIndex('cliente_id', 'cliente_id');
          historialReservasStore.createIndex('empresa_id', 'empresa_id');
          historialReservasStore.createIndex('empresa_cliente', ['empresa_id', 'cliente_id'], { unique: false });
          console.log('Object Store historial_reservas_confirmadas creado');
        }
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('IndexedDB inicializado correctamente');
        resolve();
      };
    });
  }

  async savePreparacion(preparacion: OfflinePreparacion, empresaId: number): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['offline_preparacion'], 'readwrite');
    const store = transaction.objectStore('offline_preparacion');

    const dataToStore = {
      id: `${empresaId}_${preparacion.metadata.sucursal_id}`,
      empresa_id: empresaId,
      sucursal_id: preparacion.metadata.sucursal_id,
      data: preparacion,
      timestamp: new Date().toISOString(),
    };

    return new Promise((resolve, reject) => {
      const request = store.put(dataToStore);

      request.onsuccess = () => {
        console.log(`Preparación guardada: empresa=${empresaId}, sucursal=${preparacion.metadata.sucursal_id}`);
      };

      request.onerror = () => {
        const error = new Error(`Error al guardar preparación en IndexedDB: ${request.error?.message}`);
        console.error(error);
        reject(error);
      };

      transaction.oncomplete = () => {
        resolve();
      };

      transaction.onerror = () => {
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };
    });
  }

  async getPreparacion(empresaId: number, sucursalId: number): Promise<OfflinePreparacion | null> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['offline_preparacion'], 'readonly');
    const store = transaction.objectStore('offline_preparacion');

    return new Promise((resolve, reject) => {
      let result: OfflinePreparacion | null = null;
      const request = store.get(`${empresaId}_${sucursalId}`);

      request.onsuccess = () => {
        result = request.result ? this.normalizarPreparacion(request.result.data) : null;
      };

      request.onerror = () => {
        const error = new Error(`Error al obtener preparación de IndexedDB: ${request.error?.message}`);
        console.error(error);
        reject(error);
      };

      transaction.oncomplete = () => {
        resolve(result);
      };

      transaction.onerror = () => {
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };
    });
  }

  async getAllPreparaciones(empresaId: number): Promise<OfflinePreparacion[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['offline_preparacion'], 'readonly');
    const store = transaction.objectStore('offline_preparacion');
    const index = store.index('empresa_sucursal');

    return new Promise((resolve, reject) => {
      let results: OfflinePreparacion[] = [];
      const request = index.getAll(IDBKeyRange.bound([empresaId, 0], [empresaId, Infinity]));

      request.onsuccess = () => {
        const rawResults = request.result || [];
        console.log(`Obtenidas ${rawResults.length} preparaciones para empresa ${empresaId}`);
        results = rawResults.map((r) => this.normalizarPreparacion(r.data));
      };

      request.onerror = () => {
        const error = new Error(`Error al obtener preparaciones de IndexedDB: ${request.error?.message}`);
        console.error(error);
        reject(error);
      };

      transaction.oncomplete = () => {
        resolve(results);
      };

      transaction.onerror = () => {
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };
    });
  }

  async deletePreparacion(empresaId: number, sucursalId: number): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['offline_preparacion'], 'readwrite');
    const store = transaction.objectStore('offline_preparacion');

    return new Promise((resolve, reject) => {
      const request = store.delete(`${empresaId}_${sucursalId}`);

      request.onsuccess = () => {
        console.log(`Preparación eliminada: empresa=${empresaId}, sucursal=${sucursalId}`);
      };

      request.onerror = () => {
        const error = new Error(`Error al eliminar preparación de IndexedDB: ${request.error?.message}`);
        console.error(error);
        reject(error);
      };

      transaction.oncomplete = () => {
        resolve();
      };

      transaction.onerror = () => {
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };
    });
  }

  async clearAllPreparaciones(): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['offline_preparacion'], 'readwrite');
    const store = transaction.objectStore('offline_preparacion');

    return new Promise((resolve, reject) => {
      const request = store.clear();

      request.onsuccess = () => {
        console.log('IndexedDB limpiado completamente');
      };

      request.onerror = () => {
        const error = new Error(`Error al limpiar IndexedDB: ${request.error?.message}`);
        console.error(error);
        reject(error);
      };

      transaction.oncomplete = () => {
        resolve();
      };

      transaction.onerror = () => {
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };
    });
  }

  private normalizarPreparacion(prep: OfflinePreparacion): OfflinePreparacion {
    // Normalización defensiva para datos legacy y validación de precios.
    return {
      ...prep,
      productos: prep.productos.map((prod) => {
        const precioBase = this.normalizarPrecio(prod.precio_base);
        const precioFinal = this.normalizarPrecio(prod.precio_final);
        const porcentajeDesc = prod.porcentaje_descuento
          ? this.normalizarPrecio(prod.porcentaje_descuento)
          : null;

        return {
          ...prod,
          precio_base: precioBase,
          precio_final: precioFinal,
          porcentaje_descuento: porcentajeDesc,
          variantes: prod.variantes.map((v) => ({
            ...v,
            precio: this.normalizarPrecio(v.precio),
          })),
        };
      }),
    };
  }

  private normalizarPrecio(valor: any): number {
    const num = typeof valor === 'string' ? parseFloat(valor) : Number(valor);
    if (!isFinite(num)) {
      console.warn(`Precio inválido recibido: ${valor}, usando 0`);
      return 0;
    }
    return num;
  }

  async getDisponibilidadProductoOffline(
    empresaId: number,
    productoId: number,
  ): Promise<Array<{
    sucursal_id: number;
    sucursal: string;
    ciudad_id: number;
    ciudad: string;
    variantes: Array<{
      producto_variante_id: number;
      talla_id: number;
      talla: string;
      color_id: number;
      color: string;
      cantidad: number;
    }>;
  }>> {
    try {
      const preparaciones = await this.getAllPreparaciones(empresaId);

      console.log(`[CU07 BRANCH FILTER] Total preparaciones: ${preparaciones.length}`);
      for (let i = 0; i < preparaciones.length; i++) {
        const prep = preparaciones[i];
        console.log(`[CU07 BRANCH] prep[${i}] sucursal: ${prep.sucursal.nombre} | id: ${prep.sucursal.id} | id_ciudad: ${prep.sucursal.id_ciudad} | ciudad: ${prep.sucursal.ciudad}`);
      }

      // Deduplicar por sucursal_id usando Map
      const disponibilidadMap = new Map<number, {
        sucursal_id: number;
        sucursal: string;
        ciudad_id: number;
        ciudad: string;
        variantes: Array<{
          producto_variante_id: number;
          talla_id: number;
          talla: string;
          color_id: number;
          color: string;
          cantidad: number;
        }>;
      }>();

      for (const prep of preparaciones) {
        const producto = prep.productos.find((p) => p.id === productoId);
        if (!producto) {
          continue;
        }

        // Usar id_ciudad del paquete offline (ahora incluido en el schema)
        const ciudadId = prep.sucursal.id_ciudad || hash(prep.sucursal.ciudad || 'sin-ciudad');
        console.log(`[CU07 BRANCH PROCESS] sucursal: ${prep.sucursal.nombre} | ciudad_id usado: ${ciudadId} | de: id_ciudad=${prep.sucursal.id_ciudad}`);

        // Si ya existe esta sucursal, combinar variantes
        if (disponibilidadMap.has(prep.sucursal.id)) {
          const existing = disponibilidadMap.get(prep.sucursal.id)!;
          const nuevasVariantes = producto.variantes.map((v) => ({
            producto_variante_id: v.id,
            talla_id: v.talla_id,
            talla: v.talla_nombre,
            color_id: v.color_id,
            color: v.color_nombre,
            cantidad: v.stock_disponible,
          }));

          // Deduplicar variantes por producto_variante_id
          const variantesMap = new Map();
          existing.variantes.forEach((v) => variantesMap.set(v.producto_variante_id, v));
          nuevasVariantes.forEach((v) => variantesMap.set(v.producto_variante_id, v));
          existing.variantes = Array.from(variantesMap.values());
        } else {
          // Primera vez que vemos esta sucursal
          disponibilidadMap.set(prep.sucursal.id, {
            sucursal_id: prep.sucursal.id,
            sucursal: prep.sucursal.nombre,
            ciudad_id: ciudadId,
            ciudad: prep.sucursal.ciudad || 'Sin ciudad',
            variantes: producto.variantes.map((v) => ({
              producto_variante_id: v.id,
              talla_id: v.talla_id,
              talla: v.talla_nombre,
              color_id: v.color_id,
              color: v.color_nombre,
              cantidad: v.stock_disponible,
            })),
          });
        }
      }

      return Array.from(disponibilidadMap.values());
    } catch (error) {
      console.error('Error al obtener disponibilidad offline:', error);
      return [];
    }
  }

  async getCiudadesOffline(empresaId: number): Promise<Array<{ id: number; nombre: string }>> {
    try {
      // Leer ciudades desde la primera preparación
      const preparaciones = await this.getAllPreparaciones(empresaId);
      if (preparaciones.length === 0) {
        return [];
      }

      const ciudades = preparaciones[0].ciudades || [];
      console.log(`[CU07 CITIES OFFLINE] total: ${ciudades.length}`);
      for (const c of ciudades) {
        console.log(`  - ${c.nombre}`);
      }
      return ciudades;
    } catch (error) {
      console.error('Error al obtener ciudades offline:', error);
      return [];
    }
  }

  async getCategoriasOffline(empresaId: number): Promise<Array<{ id: number; nombre: string }>> {
    try {
      const preparaciones = await this.getAllPreparaciones(empresaId);
      const categoriasMap = new Map<number, string>();

      for (const prep of preparaciones) {
        // Defensivo: categorias puede no existir en datos antiguos
        if (prep.categorias && Array.isArray(prep.categorias)) {
          for (const cat of prep.categorias) {
            if (!categoriasMap.has(cat.id)) {
              categoriasMap.set(cat.id, cat.nombre);
            }
          }
        }
      }

      return Array.from(categoriasMap, ([id, nombre]) => ({ id, nombre }));
    } catch (error) {
      console.error('Error al obtener categorías offline:', error);
      return [];
    }
  }

  async getColeccionesOffline(empresaId: number): Promise<
    Array<{
      id: number;
      nombre: string;
      descripcion: string | null;
      imagen_destacada_url: string | null;
      es_destacada_inicio: boolean;
      temporada: { id: number; nombre: string };
    }>
  > {
    try {
      const preparaciones = await this.getAllPreparaciones(empresaId);
      const coleccionesMap = new Map<
        number,
        {
          id: number;
          nombre: string;
          descripcion: string | null;
          imagen_destacada_url: string | null;
          es_destacada_inicio: boolean;
          temporada: { id: number; nombre: string };
        }
      >();

      for (const prep of preparaciones) {
        // Defensivo: colecciones puede no existir en datos antiguos
        if (prep.colecciones && Array.isArray(prep.colecciones)) {
          for (const col of prep.colecciones) {
            if (!coleccionesMap.has(col.id)) {
              coleccionesMap.set(col.id, {
                id: col.id,
                nombre: col.nombre,
                descripcion: col.descripcion,
                imagen_destacada_url: col.imagen_destacada_url,
                es_destacada_inicio: col.es_destacada_inicio,
                temporada: col.temporada,
              });
            }
          }
        }
      }

      return Array.from(coleccionesMap.values());
    } catch (error) {
      console.error('Error al obtener colecciones offline:', error);
      return [];
    }
  }

  async saveCiudades(ciudades: Array<{ id: number; nombre: string }>, empresaId: number): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['offline_ciudades'], 'readwrite');
    const store = transaction.objectStore('offline_ciudades');

    return new Promise((resolve, reject) => {
      // Guardar nuevas ciudades
      for (const ciudad of ciudades) {
        const dataToStore = {
          id: ciudad.id,
          empresa_id: empresaId,
          nombre: ciudad.nombre,
          timestamp: new Date().toISOString(),
        };
        store.put(dataToStore);
      }

      transaction.oncomplete = () => {
        console.log(`[CU07 CITIES SAVE] Guardadas: ${ciudades.length}`);
        console.log(`[CU07 CITIES SAVE] ${ciudades.map((c) => c.nombre).join(', ')}`);
        resolve();
      };

      transaction.onerror = () => {
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };
    });
  }

  async getCiudadesGuardadas(empresaId: number): Promise<Array<{ id: number; nombre: string }>> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['offline_ciudades'], 'readonly');
    const store = transaction.objectStore('offline_ciudades');
    const index = store.index('empresa_id');

    return new Promise((resolve, reject) => {
      const request = index.getAll(IDBKeyRange.only(empresaId));

      request.onsuccess = () => {
        const ciudades = (request.result || []).map((item) => ({
          id: item.id,
          nombre: item.nombre,
        }));
        console.log(`[CU07 CITIES OFFLINE] total: ${ciudades.length}`);
        for (const c of ciudades) {
          console.log(`  - ${c.nombre}`);
        }
        resolve(ciudades);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener ciudades: ${request.error?.message}`));
      };

      transaction.onerror = () => {
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };
    });
  }

  // CU8 — Registrar reserva offline
  async saveReservaOffline(reserva: {
    uuid: string;
    empresa_id: number;
    cliente_id: number;
    sucursal_id: number;
    fecha_reserva: string;
    hora_inicio: string;
    estado_general: string;
    estado_sync: string;
    fecha_creacion_local: string;
    detalles: Array<{
      uuid: string;
      producto_variante_id: number;
      cantidad: number;
      estado: string;
      estado_sync: string;
    }>;
  }, empresaId: number): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['offline_reservas', 'offline_reserva_detalles'], 'readwrite');
    const reservasStore = transaction.objectStore('offline_reservas');
    const detallesStore = transaction.objectStore('offline_reserva_detalles');

    const reservaData = {
      uuid: reserva.uuid,
      empresa_id: reserva.empresa_id,
      cliente_id: reserva.cliente_id,
      sucursal_id: reserva.sucursal_id,
      fecha_reserva: reserva.fecha_reserva,
      hora_inicio: reserva.hora_inicio,
      estado_general: reserva.estado_general,
      estado_sync: reserva.estado_sync,
      fecha_creacion_local: reserva.fecha_creacion_local,
    };

    return new Promise((resolve, reject) => {
      console.log(`[CU08 OFFLINE] Abriendo transacción para guardar reserva: ${reserva.uuid}`);

      // Patrón atómico: lanzar TODOS los puts directamente sin callbacks anidados
      // La transacción permanece abierta hasta que completa
      try {
        // Put cabecera de reserva
        const putReserva = reservasStore.put(reservaData);
        console.log(`[CU08 OFFLINE] put() reserva enviado: ${reserva.uuid}`);

        // Rastrear errores del put individual
        putReserva.onsuccess = () => {
          console.log(`[CU08 OFFLINE] put reserva exitoso`);
        };
        putReserva.onerror = () => {
          console.error(`[CU08 OFFLINE] put reserva ERROR: ${putReserva.error?.message}`);
        };

        // Put todos los detalles DENTRO de la misma transacción
        for (const detalle of reserva.detalles) {
          const putDetalle = detallesStore.put({
            uuid: detalle.uuid,
            reserva_uuid: reserva.uuid,
            producto_variante_id: detalle.producto_variante_id,
            cantidad: detalle.cantidad,
            estado: detalle.estado,
            estado_sync: detalle.estado_sync,
          });
          console.log(`[CU08 OFFLINE] put() detalle enviado: ${detalle.uuid}`);

          putDetalle.onerror = () => {
            console.error(`[CU08 OFFLINE] put detalle ERROR: ${putDetalle.error?.message}`);
          };
        }
        console.log(`[CU08 OFFLINE] todos los puts() encolados: ${reserva.detalles.length} detalles`);
      } catch (error) {
        console.error(`[CU08 OFFLINE] EXCEPCIÓN al lanzar puts: ${(error as Error).message}`);
        reject(new Error(`Error lanzando operaciones: ${(error as Error).message}`));
        return;
      }

      // La única confirmación definitiva es transaction.oncomplete
      // Esto se ejecuta cuando TODOS los puts han completado exitosamente
      transaction.oncomplete = () => {
        console.log(`[CU08 OFFLINE] ✅ TRANSACCIÓN COMPLETADA: ${reserva.uuid}`);
        resolve();
      };

      transaction.onerror = () => {
        console.error(`[CU08 OFFLINE] ❌ TRANSACTION ERROR: ${transaction.error?.message}`);
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };

      transaction.onabort = () => {
        console.error(`[CU08 OFFLINE] ❌ TRANSACTION ABORT: ${transaction.error?.message || 'unknown cause'}`);
        reject(new Error(`Transaction aborted: ${transaction.error?.message || 'unknown cause'}`));
      };
    });
  }

  async getReservasOfflinePendientes(empresaId: number): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_reservas'], 'readonly');
      const store = transaction.objectStore('offline_reservas');
      const index = store.index('empresa_id');

      const request = index.getAll(empresaId);

      request.onsuccess = () => {
        const reservas = request.result.filter((r: any) => r.estado_sync === 'PENDIENTE_SYNC');
        console.log(`[CU08 RESERVAS PENDIENTES] total: ${reservas.length}`);
        resolve(reservas);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener reservas: ${request.error?.message}`));
      };
    });
  }

  // CU18 — Mis reservas offline: obtener reservas con información visual completa
  async getReservasOfflineCompletas(empresaId: number, clienteId: number): Promise<any[]> {
    const reservas = await this.getReservasOfflinePendientes(empresaId);
    const result: any[] = [];

    for (const reserva of reservas) {
      if (reserva.cliente_id !== clienteId) continue;

      const preparacion = await this.getPreparacionActual(empresaId, reserva.sucursal_id);
      if (!preparacion) continue;

      try {
        const detalles = await this.getDetallesReserva(reserva.uuid);
        const detallesConInfo = detalles.map((detalle: any) => {
          const variante = preparacion.productos?.flatMap((p: any) => p.variantes).find((v: any) => v.id === detalle.producto_variante_id);
          const producto = variante ? preparacion.productos?.find((p: any) => p.variantes?.some((v: any) => v.id === detalle.producto_variante_id)) : null;

          return {
            id: parseInt(detalle.uuid.slice(0, 8), 16) % 1000000,
            producto: producto ? { id: producto.id, nombre: producto.nombre, imagen_principal_url: producto.imagen_principal_url } : null,
            variante: variante ? { id: variante.id, talla: { id: variante.talla_id, nombre: variante.talla_nombre }, color: { id: variante.color_id, nombre: variante.color_nombre } } : null,
            cantidad: detalle.cantidad,
            estado: detalle.estado || 'PENDIENTE',
          };
        });

        result.push({
          id: parseInt(reserva.uuid.slice(0, 8), 16) % 1000000,
          codigo_reserva: `LOC-${reserva.uuid.slice(0, 8).toUpperCase()}`,
          sucursal: { id: preparacion.sucursal?.id, nombre: preparacion.sucursal?.nombre, ciudad: { id: preparacion.sucursal?.id_ciudad, nombre: preparacion.sucursal?.ciudad } },
          estado_general: reserva.estado_general,
          fecha_reserva: reserva.fecha_reserva,
          hora_inicio: reserva.hora_inicio,
          hora_fin: reserva.hora_fin || '01:00',
          fecha_creacion: reserva.fecha_creacion_local,
          detalles: detallesConInfo,
          _origen: 'LOCAL',
          _estado_sync: reserva.estado_sync,
        });
      } catch (error) {
        console.error(`[CU18 OFFLINE] Error procesando reserva ${reserva.uuid}:`, error);
        continue;
      }
    }

    return result;
  }

  // CU18 — Obtener detalles de una reserva offline
  // CU10 — Público para CU10 (consulta de detalles)
  async getDetallesReserva(reservaUuid: string): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_reserva_detalles'], 'readonly');
      const store = transaction.objectStore('offline_reserva_detalles');
      const index = store.index('reserva_uuid');

      const request = index.getAll(reservaUuid);

      request.onsuccess = () => {
        resolve(request.result || []);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener detalles: ${request.error?.message}`));
      };
    });
  }

  // CU8 — Validaciones locales: obtener datos de CU6 para validar reserva
  async getPreparacionActual(empresaId: number, sucursalId: number): Promise<OfflinePreparacion | null> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_preparacion'], 'readonly');
      const store = transaction.objectStore('offline_preparacion');

      const request = store.getAll();

      request.onsuccess = () => {
        const registros = request.result || [];
        const registro = registros.find(
          (p: any) => p?.empresa_id === empresaId && p?.sucursal_id === sucursalId
        );
        resolve(registro?.data || null);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener preparación: ${request.error?.message}`));
      };
    });
  }

  // CU8 — Buscar variante específica en datos locales
  getVariantePorId(preparacion: OfflinePreparacion, varianteId: number): any | null {
    for (const producto of preparacion.productos) {
      const variante = producto.variantes.find((v) => v.id === varianteId);
      if (variante) {
        return {
          ...variante,
          producto_id: producto.id,
          producto_nombre: producto.nombre,
        };
      }
    }
    return null;
  }

  // CU8 — Validar sucursal pertenece a empresa actual
  validarSucursalPertenece(preparacion: OfflinePreparacion, sucursalId: number, empresaId: number): boolean {
    return preparacion.metadata.empresa_id === empresaId && preparacion.sucursal.id === sucursalId;
  }

  // CU9 — Guardar venta presencial offline (TRANSACCIÓN ATÓMICA)
  async guardarVentaOffline(venta: {
    uuid: string;
    empresa_id: number;
    cajero_id: number;
    sucursal_id: number;
    fecha_creacion: string;
    total: number;
    estado: string;
    estado_sync: string;
    tipo: string;
    origen: string;
    detalles: Array<{
      uuid: string;
      producto_variante_id: number;
      cantidad: number;
      precio_unitario: number;
      subtotal: number;
    }>;
    pago: {
      monto_total: number;
      monto_recibido: number;
      cambio: number;
      fecha_cobro: string;
    };
  }): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(
        ['offline_ventas', 'offline_venta_detalles', 'offline_pago_efectivo'],
        'readwrite'
      );
      const ventasStore = transaction.objectStore('offline_ventas');
      const detallesStore = transaction.objectStore('offline_venta_detalles');
      const pagoStore = transaction.objectStore('offline_pago_efectivo');

      try {
        console.log(`[CU9 OFFLINE] Abriendo transacción para guardar venta: ${venta.uuid}`);

        // Guardar cabecera
        const ventaData = {
          uuid: venta.uuid,
          empresa_id: venta.empresa_id,
          cajero_id: venta.cajero_id,
          sucursal_id: venta.sucursal_id,
          fecha_creacion: venta.fecha_creacion,
          total: venta.total,
          estado: venta.estado,
          estado_sync: venta.estado_sync,
          tipo: venta.tipo,
          origen: venta.origen,
        };
        ventasStore.put(ventaData);
        console.log(`[CU9 OFFLINE] put() venta enviado: ${venta.uuid}`);

        // Guardar detalles
        for (const detalle of venta.detalles) {
          const detalleData = {
            uuid: detalle.uuid,
            venta_uuid: venta.uuid,
            producto_variante_id: detalle.producto_variante_id,
            cantidad: detalle.cantidad,
            precio_unitario: detalle.precio_unitario,
            subtotal: detalle.subtotal,
          };
          detallesStore.put(detalleData);
        }
        console.log(`[CU9 OFFLINE] put() detalles enviados: ${venta.detalles.length}`);

        // Guardar pago
        const pagoData = {
          venta_uuid: venta.uuid,
          monto_total: venta.pago.monto_total,
          monto_recibido: venta.pago.monto_recibido,
          cambio: venta.pago.cambio,
          fecha_cobro: venta.pago.fecha_cobro,
        };
        pagoStore.put(pagoData);
        console.log(`[CU9 OFFLINE] put() pago enviado: ${venta.uuid}`);
      } catch (error) {
        console.error(`[CU9 OFFLINE] EXCEPCIÓN al lanzar puts: ${(error as Error).message}`);
        reject(new Error(`Error lanzando operaciones: ${(error as Error).message}`));
        return;
      }

      transaction.oncomplete = () => {
        console.log(`[CU9 OFFLINE] ✅ TRANSACCIÓN COMPLETADA: ${venta.uuid}`);
        resolve();
      };

      transaction.onerror = () => {
        console.error(`[CU9 OFFLINE] ❌ TRANSACTION ERROR: ${transaction.error?.message}`);
        reject(new Error(`Transaction error: ${transaction.error?.message}`));
      };

      transaction.onabort = () => {
        console.error(`[CU9 OFFLINE] ❌ TRANSACTION ABORT: ${transaction.error?.message || 'unknown cause'}`);
        reject(new Error(`Transaction aborted: ${transaction.error?.message || 'unknown cause'}`));
      };
    });
  }

  // CU9 — Obtener ventas presenciales offline pendientes
  async obtenerVentasOfflinePendientes(empresaId: number): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_ventas'], 'readonly');
      const store = transaction.objectStore('offline_ventas');
      const index = store.index('empresa_id');

      const request = index.getAll(empresaId);

      request.onsuccess = () => {
        const ventas = request.result.filter((v: any) => v.estado_sync === 'PENDIENTE_SYNC');
        console.log(`[CU9 VENTAS PENDIENTES] total: ${ventas.length}`);
        resolve(ventas);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener ventas: ${request.error?.message}`));
      };
    });
  }

  // CU13 REINTENTOS — Obtener ventas rechazadas o con conflicto
  async obtenerVentasOfflineRechazadas(empresaId: number): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_ventas'], 'readonly');
      const store = transaction.objectStore('offline_ventas');
      const index = store.index('empresa_id');

      const request = index.getAll(empresaId);

      request.onsuccess = () => {
        const ventas = request.result.filter(
          (v: any) => v.estado_sync === 'RECHAZADA' || v.estado_sync === 'CONFLICTO'
        );
        console.log(`[CU13 VENTAS RECHAZADAS] total: ${ventas.length}`);
        resolve(ventas);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener ventas rechazadas: ${request.error?.message}`));
      };
    });
  }

  // CU13 REINTENTOS — Obtener reservas rechazadas o con conflicto
  async getReservasOfflineRechazadas(empresaId: number): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_reservas'], 'readonly');
      const store = transaction.objectStore('offline_reservas');
      const index = store.index('empresa_id');

      const request = index.getAll(empresaId);

      request.onsuccess = () => {
        const reservas = request.result.filter(
          (r: any) => r.estado_sync === 'RECHAZADA' || r.estado_sync === 'CONFLICTO'
        );
        console.log(`[CU13 RESERVAS RECHAZADAS] total: ${reservas.length}`);
        resolve(reservas);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener reservas rechazadas: ${request.error?.message}`));
      };
    });
  }

  // CU9 STOCK CONTROL — Calcular stock disponible considerando ventas offline locales
  async obtenerStockDisponibleLocal(
    empresaId: number,
    sucursalId: number,
    productoVarianteId: number,
  ): Promise<number> {
    try {
      // 1. Obtener preparaciones para esta empresa/sucursal
      const preparaciones = await this.getAllPreparaciones(empresaId);
      const preparacion = preparaciones.find((p: any) => p.metadata?.sucursal_id === sucursalId);

      if (!preparacion) {
        console.warn(
          `[CU9 STOCK] No hay preparación para empresa=${empresaId}, sucursal=${sucursalId}`
        );
        return 0;
      }

      // 2. Encontrar stock base de la variante en la preparación
      let stockBase = 0;
      for (const producto of preparacion.productos || []) {
        for (const variante of producto.variantes || []) {
          if (variante.id === productoVarianteId) {
            stockBase = variante.stock_disponible || 0;
            break;
          }
        }
        if (stockBase > 0) break;
      }

      if (stockBase === 0) {
        console.warn(`[CU9 STOCK] Variante ${productoVarianteId} no encontrada o sin stock`);
        return 0;
      }

      // 3. Obtener ventas offline pendientes
      const ventasOffline = await this.obtenerVentasOfflinePendientes(empresaId);
      let cantidadComprometidaVentas = 0;

      for (const venta of ventasOffline) {
        // Solo contar si es la misma sucursal
        if (venta.sucursal_id !== sucursalId) continue;

        // Obtener detalles de esta venta
        const detalles = await this.obtenerDetallesVenta(venta.uuid);
        for (const detalle of detalles) {
          if (detalle.producto_variante_id === productoVarianteId) {
            cantidadComprometidaVentas += detalle.cantidad || 0;
          }
        }
      }

      // 4. Obtener reservas offline pendientes (CU8)
      let cantidadComprometidaReservas = 0;
      const reservasOffline = await this.getReservasOfflinePendientes(empresaId);

      for (const reserva of reservasOffline) {
        // Solo contar si es la misma sucursal
        if (reserva.sucursal_id !== sucursalId) continue;

        // Obtener detalles de esta reserva
        const detalles = await this.getDetallesReserva(reserva.uuid);
        for (const detalle of detalles) {
          if (detalle.producto_variante_id === productoVarianteId) {
            cantidadComprometidaReservas += detalle.cantidad || 0;
          }
        }
      }

      // 5. Calcular disponibilidad local
      const disponible = Math.max(
        0,
        stockBase - cantidadComprometidaVentas - cantidadComprometidaReservas
      );

      console.log(
        `[CU9 STOCK CALC] variante=${productoVarianteId}, stock_base=${stockBase}, ` +
        `ventas_comprometidas=${cantidadComprometidaVentas}, reservas=${cantidadComprometidaReservas}, ` +
        `disponible=${disponible}`
      );

      return disponible;
    } catch (error) {
      console.error('[CU9 STOCK] Error al calcular disponibilidad:', error);
      return 0;
    }
  }

  // CU9/CU10 — Obtener detalles de una venta (public para que CU10 pueda consultarla)
  async obtenerDetallesVenta(ventaUuid: string): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_venta_detalles'], 'readonly');
      const store = transaction.objectStore('offline_venta_detalles');
      const index = store.index('venta_uuid');

      const request = index.getAll(ventaUuid);

      request.onsuccess = () => {
        resolve(request.result || []);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener detalles venta: ${request.error?.message}`));
      };
    });
  }

  // CU9 — Obtener pago de una venta
  async obtenerPagoVenta(ventaUuid: string): Promise<any | null> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_pago_efectivo'], 'readonly');
      const store = transaction.objectStore('offline_pago_efectivo');

      const request = store.get(ventaUuid);

      request.onsuccess = () => {
        resolve(request.result || null);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener pago: ${request.error?.message}`));
      };
    });
  }

  // CU11 — Actualizar estado de sincronización de venta
  async actualizarEstadoVentaOffline(
    ventaUuid: string,
    nuevoEstado: 'SINCRONIZADA' | 'RECHAZADA' | 'CONFLICTO',
    motivo?: string | null,
    resultadoServer?: { venta_id?: number | null; codigo_venta?: string | null; fecha_sincronizacion?: string }
  ): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_ventas'], 'readwrite');
      const store = transaction.objectStore('offline_ventas');

      const getRequest = store.get(ventaUuid);

      getRequest.onsuccess = () => {
        const venta = getRequest.result;
        if (!venta) {
          reject(new Error(`Venta no encontrada: ${ventaUuid}`));
          return;
        }

        // Actualizar estado y metadatos de sincronización
        venta.estado_sync = nuevoEstado;
        venta.motivo_rechazo = motivo || null;
        venta.fecha_sincronizacion = new Date().toISOString();
        venta.venta_id_servidor = resultadoServer?.venta_id || null;
        venta.codigo_venta_servidor = resultadoServer?.codigo_venta || null;

        const putRequest = store.put(venta);

        putRequest.onsuccess = () => {
          console.log(`[CU11] Estado venta actualizado: ${ventaUuid} -> ${nuevoEstado}`);
          resolve();
        };

        putRequest.onerror = () => {
          reject(new Error(`Error al actualizar venta: ${putRequest.error?.message}`));
        };
      };

      getRequest.onerror = () => {
        reject(new Error(`Error al obtener venta: ${getRequest.error?.message}`));
      };
    });
  }

  // CU11 — Actualizar estado de sincronización de reserva
  async actualizarEstadoReservaOffline(
    reservaUuid: string,
    nuevoEstado: 'SINCRONIZADA' | 'RECHAZADA' | 'CONFLICTO',
    motivo?: string | null,
    resultadoServer?: { reserva_id?: number | null; codigo_reserva?: string | null; fecha_sincronizacion?: string }
  ): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['offline_reservas'], 'readwrite');
      const store = transaction.objectStore('offline_reservas');

      const getRequest = store.get(reservaUuid);

      getRequest.onsuccess = () => {
        const reserva = getRequest.result;
        if (!reserva) {
          reject(new Error(`Reserva no encontrada: ${reservaUuid}`));
          return;
        }

        // Actualizar estado y metadatos de sincronización
        reserva.estado_sync = nuevoEstado;
        reserva.motivo_rechazo = motivo || null;
        reserva.fecha_sincronizacion = new Date().toISOString();
        reserva.reserva_id_servidor = resultadoServer?.reserva_id || null;
        reserva.codigo_reserva_servidor = resultadoServer?.codigo_reserva || null;

        const putRequest = store.put(reserva);

        putRequest.onsuccess = () => {
          console.log(`[CU11] Estado reserva actualizado: ${reservaUuid} -> ${nuevoEstado}`);
          resolve();
        };

        putRequest.onerror = () => {
          reject(new Error(`Error al actualizar reserva: ${putRequest.error?.message}`));
        };
      };

      getRequest.onerror = () => {
        reject(new Error(`Error al obtener reserva: ${getRequest.error?.message}`));
      };
    });
  }

  // CU27 — Guardar historial de compras confirmadas desde backend (CLIENTE y CAJERO)
  async guardarHistorialConfirmado(
    ventasConfirmadas: any[],
    empresaId: number,
    clienteId?: number,
    sucursalId?: number
  ): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['historial_ventas_confirmadas'], 'readwrite');
    const store = transaction.objectStore('historial_ventas_confirmadas');

    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => {
        console.log(`[CU27 HISTORIAL] ${ventasConfirmadas.length} compras confirmadas guardadas`, {
          empresa: empresaId,
          cliente: clienteId || 'N/A',
          sucursal: sucursalId || 'N/A',
        });
        resolve();
      };

      transaction.onerror = () => {
        reject(new Error(`Error en transacción de historial: ${transaction.error?.message}`));
      };

      ventasConfirmadas.forEach((venta: any) => {
        const ventaConfirmada = {
          venta_id: venta.venta_id,
          codigo_venta: venta.codigo_venta,
          cliente_id: clienteId !== undefined ? clienteId : null,
          empresa_id: empresaId,
          sucursal_id: sucursalId !== undefined ? sucursalId : (venta.sucursal?.id || venta.sucursal_id || 0),
          fecha: venta.fecha,
          tipo: venta.tipo,
          metodo_pago: venta.metodo_pago,
          total: venta.total,
          tiene_postventa: venta.tiene_postventa,
          leyenda_postventa: venta.leyenda_postventa,
          estado_sync: 'CONFIRMADA',
          fecha_descarga: new Date().toISOString(),
        };
        store.put(ventaConfirmada);
      });
    });
  }

  // CU27 — Obtener historial de compras confirmadas del cliente
  async obtenerHistorialConfirmado(empresaId: number, clienteId: number): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['historial_ventas_confirmadas'], 'readonly');
      const store = transaction.objectStore('historial_ventas_confirmadas');
      const index = store.index('empresa_cliente');
      const range = IDBKeyRange.only([empresaId, clienteId]);
      const request = index.getAll(range);

      request.onsuccess = () => {
        resolve(request.result || []);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener historial confirmado: ${request.error?.message}`));
      };
    });
  }

  // CU27 — Obtener historial de compras confirmadas de una sucursal (para Cajero)
  async obtenerHistorialConfirmadoPorSucursal(empresaId: number, sucursalId: number): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['historial_ventas_confirmadas'], 'readonly');
      const store = transaction.objectStore('historial_ventas_confirmadas');

      try {
        const index = store.index('empresa_sucursal');
        const range = IDBKeyRange.only([empresaId, sucursalId]);
        const request = index.getAll(range);

        request.onsuccess = () => {
          resolve(request.result || []);
        };

        request.onerror = () => {
          reject(new Error(`Error al obtener historial por sucursal: ${request.error?.message}`));
        };
      } catch (e) {
        // Si índice no existe aún (fallback a búsqueda manual)
        console.log('[CU27] Índice empresa_sucursal no disponible, búsqueda manual');
        const request = store.getAll();
        request.onsuccess = () => {
          const resultados = (request.result || []).filter(
            (v: any) => v.empresa_id === empresaId && v.sucursal_id === sucursalId
          );
          resolve(resultados);
        };
        request.onerror = () => reject(e);
      }
    });
  }

  // CU18 — Guardar historial de reservas confirmadas descargadas
  async guardarHistorialReservasConfirmado(
    reservasConfirmadas: any[],
    empresaId: number,
    clienteId?: number
  ): Promise<void> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    const transaction = db.transaction(['historial_reservas_confirmadas'], 'readwrite');
    const store = transaction.objectStore('historial_reservas_confirmadas');

    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => {
        console.log(`[CU18 HISTORIAL] ${reservasConfirmadas.length} reservas confirmadas guardadas`, {
          empresa: empresaId,
          cliente: clienteId || 'N/A',
        });
        resolve();
      };

      transaction.onerror = () => {
        reject(new Error(`Error en transacción de historial de reservas: ${transaction.error?.message}`));
      };

      reservasConfirmadas.forEach((reserva: any) => {
        const reservaConfirmada = {
          // Identificadores para IndexedDB
          reserva_id: reserva.id,
          cliente_id: clienteId !== undefined ? clienteId : null,
          empresa_id: empresaId,
          // Datos de la cabecera (necesarios para renderizar tarjeta)
          codigo_reserva: reserva.codigo_reserva,
          sucursal: {
            id: reserva.sucursal?.id || 0,
            nombre: reserva.sucursal?.nombre || 'Sucursal desconocida',
            ciudad: {
              id: reserva.sucursal?.ciudad?.id || 0,
              nombre: reserva.sucursal?.ciudad?.nombre || 'Ciudad desconocida'
            }
          },
          estado_general: reserva.estado_general,
          fecha_reserva: reserva.fecha_reserva,
          hora_inicio: reserva.hora_inicio,
          hora_fin: reserva.hora_fin,
          fecha_creacion: reserva.fecha_creacion,
          // Detalles (necesarios para renderizar prendas)
          detalles: (reserva.detalles || []).map((d: any) => ({
            id: d.id,
            producto: {
              id: d.producto?.id || 0,
              nombre: d.producto?.nombre || 'Producto desconocido',
              imagen_principal_url: d.producto?.imagen_principal_url || null
            },
            variante: {
              id: d.variante?.id || 0,
              talla: {
                id: d.variante?.talla?.id || 0,
                nombre: d.variante?.talla?.nombre || 'S/T'
              },
              color: {
                id: d.variante?.color?.id || 0,
                nombre: d.variante?.color?.nombre || 'Sin color'
              }
            },
            cantidad: d.cantidad || 1,
            estado: d.estado || 'PENDIENTE',
          })),
          // Metadata
          estado_sync: 'CONFIRMADA',
          fecha_descarga: new Date().toISOString(),
          _origen: 'CONFIRMADA',
        };
        store.put(reservaConfirmada);
      });
    });
  }

  // CU18 — Obtener historial de reservas confirmadas del cliente
  async obtenerHistorialReservasConfirmado(empresaId: number, clienteId: number): Promise<any[]> {
    await this.dbReady;
    const db = this.db;

    if (!db) {
      throw new Error('IndexedDB no está disponible');
    }

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['historial_reservas_confirmadas'], 'readonly');
      const store = transaction.objectStore('historial_reservas_confirmadas');
      const index = store.index('empresa_cliente');
      const range = IDBKeyRange.only([empresaId, clienteId]);

      const request = index.getAll(range);

      request.onsuccess = () => {
        resolve(request.result || []);
      };

      request.onerror = () => {
        reject(new Error(`Error al obtener historial de reservas: ${request.error?.message}`));
      };
    });
  }

}
