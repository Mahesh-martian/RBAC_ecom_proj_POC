import { PrismaClient } from "@prisma/client";


const prisma = new PrismaClient()
// console.log(prisma);

prisma.$connect()
  .then(() => console.log('Connected to database'))
  .catch((err) => console.error('Failed to connect:', err));

  
export default prisma;