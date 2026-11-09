import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { SincronizarOperacionesPendientesService } from './sincronizar-operaciones-pendientes.service';
import { OfflineStorageService } from '../../../../core/services/offline-storage.service';
import { AuthService } from '../../../../core/services/auth.service';
import { environment } from '../../../../../environments/environment';

describe('SincronizarOperacionesPendientesService', () => {
  let service: SincronizarOperacionesPendientesService;
  let httpMock: HttpTestingController;
  let offlineStorageMock: jasmine.SpyObj<OfflineStorageService>;
  let authServiceMock: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    const offlineStorageSpy = jasmine.createSpyObj('OfflineStorageService', [
      'obtenerVentasOfflinePendientes',
      'obtenerDetallesVenta',
      'obtenerPagoVenta',
      'getReservasOfflinePendientes',
    ]);

    const authServiceSpy = jasmine.createSpyObj('AuthService', ['usuario']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        SincronizarOperacionesPendientesService,
        { provide: OfflineStorageService, useValue: offlineStorageSpy },
        { provide: AuthService, useValue: authServiceSpy },
      ],
    });

    service = TestBed.inject(SincronizarOperacionesPendientesService);
    httpMock = TestBed.inject(HttpTestingController);
    offlineStorageMock = TestBed.inject(OfflineStorageService) as jasmine.SpyObj<OfflineStorageService>;
    authServiceMock = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('obtenerVentasPendientes', () => {
    it('debe retornar lista de ventas pendientes', async () => {
      const ventasMock = [
        {
          uuid: 'uuid-001',
          empresa_id: 100,
          sucursal_id: 10,
          total: 200,
          estado_sync: 'PENDIENTE_SYNC',
        },
      ];

      offlineStorageMock.obtenerVentasOfflinePendientes.and.returnValue(
        Promise.resolve(ventasMock),
      );

      const ventas = await service.obtenerVentasPendientes(100);

      expect(ventas.length).toBe(1);
      expect(ventas[0].uuid).toBe('uuid-001');
    });

    it('debe retornar array vacío si hay error', async () => {
      offlineStorageMock.obtenerVentasOfflinePendientes.and.returnValue(
        Promise.reject(new Error('IndexedDB error')),
      );

      const ventas = await service.obtenerVentasPendientes(100);

      expect(ventas.length).toBe(0);
    });
  });

  describe('sincronizarVentaOffline', () => {
    it('debe sincronizar venta y retornar CONFIRMADA', async () => {
      const ventaMock = {
        uuid: 'uuid-venta-001',
        empresa_id: 100,
        sucursal_id: 10,
        fecha_creacion: '2026-11-08T12:00:00Z',
        total: 200,
      };

      const detallesMock = [
        {
          producto_variante_id: 50,
          cantidad: 2,
          precio_unitario: 100,
          subtotal: 200,
        },
      ];

      const pagoMock = {
        monto_recibido: 250,
      };

      offlineStorageMock.obtenerVentasOfflinePendientes.and.returnValue(
        Promise.resolve([ventaMock]),
      );
      offlineStorageMock.obtenerDetallesVenta.and.returnValue(
        Promise.resolve(detallesMock),
      );
      offlineStorageMock.obtenerPagoVenta.and.returnValue(Promise.resolve(pagoMock));

      const resultPromise = service.sincronizarVentaOffline('uuid-venta-001', 100);

      const req = httpMock.expectOne(`${environment.apiUrl}/sincronizar/ventas`);
      expect(req.request.method).toBe('POST');

      const payload = req.request.body;
      expect(payload.uuid).toBe('uuid-venta-001');
      expect(payload.empresa_id).toBe(100);
      expect(payload.detalles.length).toBe(1);

      req.flush({
        uuid_local: 'uuid-venta-001',
        venta_id: 1001,
        codigo_venta: 'V-001',
        estado: 'CONFIRMADA',
        total: 200,
      });

      const resultado = await resultPromise;

      expect(resultado.estado).toBe('CONFIRMADA');
      expect(resultado.venta_id).toBe(1001);
    });

    it('debe manejar CONFLICTO por stock insuficiente', async () => {
      const ventaMock = {
        uuid: 'uuid-venta-002',
        empresa_id: 100,
        sucursal_id: 10,
        fecha_creacion: '2026-11-08T12:00:00Z',
        total: 500,
      };

      offlineStorageMock.obtenerVentasOfflinePendientes.and.returnValue(
        Promise.resolve([ventaMock]),
      );
      offlineStorageMock.obtenerDetallesVenta.and.returnValue(
        Promise.resolve([
          {
            producto_variante_id: 50,
            cantidad: 100,
            precio_unitario: 5,
            subtotal: 500,
          },
        ]),
      );
      offlineStorageMock.obtenerPagoVenta.and.returnValue(Promise.resolve(null));

      const resultPromise = service.sincronizarVentaOffline('uuid-venta-002', 100);

      const req = httpMock.expectOne(`${environment.apiUrl}/sincronizar/ventas`);
      req.flush(
        { motivo: 'Stock insuficiente' },
        { status: 422, statusText: 'Unprocessable Entity' },
      );

      const resultado = await resultPromise;

      expect(resultado.estado).toBe('RECHAZADA');
    });

    it('debe retornar RECHAZADA si venta no encontrada', async () => {
      offlineStorageMock.obtenerVentasOfflinePendientes.and.returnValue(Promise.resolve([]));

      const resultado = await service.sincronizarVentaOffline('uuid-inexistente', 100);

      expect(resultado.estado).toBe('RECHAZADA');
      expect(resultado.motivo).toBe('Venta no encontrada');
    });

    it('debe validar aislamiento de empresa', async () => {
      const ventaOtraEmpresa = {
        uuid: 'uuid-otra-empresa',
        empresa_id: 999,
        sucursal_id: 10,
        total: 200,
      };

      offlineStorageMock.obtenerVentasOfflinePendientes.and.returnValue(
        Promise.resolve([ventaOtraEmpresa]),
      );

      const resultado = await service.sincronizarVentaOffline('uuid-otra-empresa', 100);

      expect(resultado.estado).toBe('RECHAZADA');
      expect(resultado.motivo).toContain('Empresa no autorizada');
    });
  });

  describe('sincronizarTodasLasOperaciones', () => {
    it('debe sincronizar todas las operaciones pendientes', async () => {
      const usuarioMock = { empresa_id: 100 };
      authServiceMock.usuario.and.returnValue(usuarioMock);

      const ventasMock = [
        {
          uuid: 'uuid-001',
          empresa_id: 100,
          sucursal_id: 10,
          fecha_creacion: '2026-11-08T12:00:00Z',
          total: 100,
        },
        {
          uuid: 'uuid-002',
          empresa_id: 100,
          sucursal_id: 10,
          fecha_creacion: '2026-11-08T13:00:00Z',
          total: 200,
        },
      ];

      offlineStorageMock.obtenerVentasOfflinePendientes.and.returnValue(
        Promise.resolve(ventasMock),
      );
      offlineStorageMock.obtenerDetallesVenta.and.returnValue(Promise.resolve([]));
      offlineStorageMock.obtenerPagoVenta.and.returnValue(Promise.resolve(null));

      const resultPromise = service.sincronizarTodasLasOperaciones();

      // Dos requests HTTP para dos ventas
      const reqs = httpMock.match(`${environment.apiUrl}/sincronizar/ventas`);
      expect(reqs.length).toBe(2);

      reqs[0].flush({
        uuid_local: 'uuid-001',
        venta_id: 1001,
        estado: 'CONFIRMADA',
      });

      reqs[1].flush({
        uuid_local: 'uuid-002',
        venta_id: 1002,
        estado: 'CONFIRMADA',
      });

      const resultados = await resultPromise;

      expect(resultados.length).toBe(2);
    });

    it('debe retornar array vacío si usuario no autenticado', async () => {
      authServiceMock.usuario.and.returnValue(null);

      const resultados = await service.sincronizarTodasLasOperaciones();

      expect(resultados.length).toBe(0);
    });
  });
});
