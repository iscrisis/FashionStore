export type CatalogStatusFilter = 'all' | 'active' | 'inactive';

export interface CatalogListQuery {
  search?: string;
  status?: CatalogStatusFilter;
}
