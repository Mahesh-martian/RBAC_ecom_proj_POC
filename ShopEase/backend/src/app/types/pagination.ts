export type TPaginationOptions = {
  page?: number, 
  limit?: number, 
  sortBy?: string | undefined, 
  sortOrder?: string | undefined, 
}

export type TPaginationResult = {
  page: number,
  limit: number,
  skip: number,
  sortBy: string,
  sortOrder: string,
}