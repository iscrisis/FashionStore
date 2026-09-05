// Modelo temporal SOLO para maquetar la sección visual "Destacados para ti".
// No proviene de ningún endpoint: se reemplazará por el modelo real cuando
// se implemente el caso de uso de gestión de productos.
export interface MockProduct {
  id: number;
  name: string;
  price: number;
  imageUrl: string | null;
}
