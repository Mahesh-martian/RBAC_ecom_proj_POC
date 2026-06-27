
export type TAdminFilterRequest = {
  name?: string | undefined;
  email?: string | undefined;
  searchTerm?: string | undefined;
};

export type TCategory = {
  name: string;
  description?: string
}