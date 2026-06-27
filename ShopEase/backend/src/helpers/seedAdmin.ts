import config from "../config";
import prisma from "../shared/prisma";
import bcrypt from "bcrypt";

export async function seedAdminAccount() {
  const adminEmail = config.ADMIN_EMAIL as string;
  const adminPassword = config.ADMIN_PASSWORD as string ;

  // Check if the admin account already exists
  const existingAdmin = await prisma.user.findUnique({
    where: { email: adminEmail },
  });

  if (!existingAdmin) {
    console.log("Admin account does not exist. Creating one...");

    // Hash the admin password
    const hashedPassword = await bcrypt.hash(adminPassword, 10);

    // Create admin account
    await prisma.user.create({
      data: {
        email: adminEmail,
        password: hashedPassword,
        role: "ADMIN",
        name: "Super Admin",
        
      },
    });

    console.log(`Admin account created with email: ${adminEmail}`);
  } else {
    console.log("Admin account already exists. Skipping creation.");
  }
}