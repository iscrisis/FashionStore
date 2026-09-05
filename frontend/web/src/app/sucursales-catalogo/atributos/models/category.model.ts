export interface Category {
  id: number;
  nombre: string;
  imagen_url: string | null;
  is_active: boolean;
}

export interface CategoryPayload {
  nombre: string;
  is_active?: boolean;
}
