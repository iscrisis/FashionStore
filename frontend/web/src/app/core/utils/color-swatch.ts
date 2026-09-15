// El backend NO guarda código hex para Color (ver
// backend/modules/P1_SucursalesYCatalogos/Models/color.py -- "Solo nombre,
// sin código hex"). Esta tabla es puramente de presentación en el círculo
// selector de color: traduce nombres comunes a un tono aproximado para que
// el usuario los reconozca visualmente, sin inventar ni persistir ningún
// dato nuevo -- el nombre real sigue siendo el único dato que viaja desde
// FastAPI. Un nombre que no aparece aquí cae a un swatch neutro.
const TONOS_CONOCIDOS: Record<string, string> = {
  rojo: '#a90012',
  negro: '#1a1a1a',
  blanco: '#ffffff',
  beige: '#e3d5c0',
  gris: '#9a9a9a',
  plomo: '#9a9a9a',
  azul: '#2a4d8f',
  celeste: '#7fb3e0',
  verde: '#2e7d4f',
  amarillo: '#e8c547',
  naranja: '#d9782d',
  rosado: '#e0a0b0',
  rosa: '#e0a0b0',
  morado: '#6b4e8e',
  violeta: '#6b4e8e',
  cafe: '#6b4423',
  café: '#6b4423',
  marron: '#6b4423',
  marrón: '#6b4423',
  dorado: '#c9a24b',
  plateado: '#c0c0c0',
  vino: '#5e0f18',
  crema: '#f0e6d2',
};

export function resolveColorSwatch(nombre: string): string | null {
  const clave = nombre.trim().toLowerCase();
  return TONOS_CONOCIDOS[clave] ?? null;
}
