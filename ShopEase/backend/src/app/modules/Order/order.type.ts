
export type TProductFilterRequest = {
  name?: string | undefined;
  price?: number | undefined;
  discount?: number | undefined;
  searchTerm?: string | undefined;
};


export type TCategory = {
  name: string;
  description?: string
}