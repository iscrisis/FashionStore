export interface ColorItem {
  id: number;
  name: string;
  hexCode: string;
  displayOrder: number;
  isActive: boolean;
}

export type ColorPayload = Omit<ColorItem, 'id'>;
