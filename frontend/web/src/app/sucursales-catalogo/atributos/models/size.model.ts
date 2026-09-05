export interface Size {
  id: number;
  code: string;
  name: string;
  description: string | null;
  displayOrder: number;
  isActive: boolean;
}

export type SizePayload = Omit<Size, 'id'>;
