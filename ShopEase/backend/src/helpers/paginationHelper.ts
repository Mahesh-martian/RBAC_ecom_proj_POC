import { TPaginationOptions, TPaginationResult } from "../app/types/pagination";


const calculatePagination = (options: TPaginationOptions) : TPaginationResult => {
  const page: number = Number(options.page) || 1;
  const limit: number = Number(options.limit) || 10;
  const skip: number = (Number(page) -1) * limit;

  const sortBy: string = options.sortBy || "createdAt"
  const sortOrder: string = options.sortOrder || "desc"

  return {
    page, limit, skip, sortBy, sortOrder
  }
}


export const paginationHelper = { calculatePagination }