export type TProductFilterRequest = {
  name?: string | undefined;
  price?: number | undefined;
  discount?: number | undefined;
  searchTerm?: string | undefined;
};

// export type TProductFilterRequest = {
//   name?: string;
//   price?: number;
//   discount?: number;
//   searchTerm?: string;
//   minPrice?: number;
//   maxPrice?: number;
//   minDiscount?: number;
//   maxDiscount?: number;
// };

export type TCategory = {
  name: string;
  description?: string;
};
