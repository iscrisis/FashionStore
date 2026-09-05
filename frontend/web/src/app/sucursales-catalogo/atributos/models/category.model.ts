export interface Category {
  id: number;
  name: string;
  description: string | null;
  imageUrl: string | null;
  displayOrder: number;
  isActive: boolean;
}

export type CategoryPayload = Omit<Category, 'id'>;
