export interface ColorItem {
  id: number;
  nombre: string;
  is_active: boolean;
}

export interface ColorPayload {
  nombre: string;
  is_active?: boolean;
}
