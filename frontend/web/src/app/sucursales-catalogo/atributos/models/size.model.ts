export interface Size {
  id: number;
  nombre: string;
  is_active: boolean;
}

export interface SizePayload {
  nombre: string;
  is_active?: boolean;
}
