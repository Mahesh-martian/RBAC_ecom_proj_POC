import fs from "fs";
import path from "path";
import bcrypt from "bcrypt";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

/**
 * Seed the database from the Flipkart Fashion Products dataset.
 *
 * Download the dataset file and place it at:
 *   ShopEase/backend/prisma/data/flipkart_fashion_products_dataset.json
 *
 * Dataset: https://www.kaggle.com/datasets/aaditshukla/flipkart-fasion-products-dataset
 *
 * The Flipkart JSON has no User/Vendor/Shop/Category tables, so this script
 * synthesizes those records (which your Prisma schema requires as foreign keys)
 * from each product's `seller_name` and `breadcrumbs`/`brand`.
 *
 * Usage:
 *   npm run seed                 # seeds up to SEED_LIMIT products
 *   SEED_LIMIT=200 npm run seed  # cap how many products are inserted
 */

const DATA_FILE = path.join(__dirname, "data", "flipkart_fashion_products_dataset.json");
const SEED_LIMIT = Number(process.env.SEED_LIMIT ?? 500);
const DEFAULT_VENDOR_PASSWORD = process.env.SEED_VENDOR_PASSWORD ?? "Vendor@123";

type FlipkartProduct = {
  pid?: string;
  _id?: string;
  // Real dataset uses `title`; the smaller sample variant uses `name`.
  title?: string;
  name?: string;
  description?: string;
  selling_price?: string | number;
  // Real dataset uses `actual_price`; sample variant uses `original_price`.
  actual_price?: string | number;
  original_price?: string | number;
  brand?: string;
  // Real dataset uses `seller`; sample variant uses `seller_name`.
  seller?: string;
  seller_name?: string;
  images?: string[] | string;
  // Real dataset uses flat `category`/`sub_category`; sample uses `breadcrumbs`.
  category?: string;
  sub_category?: string;
  breadcrumbs?: string[] | string;
  out_of_stock?: boolean;
};

/** Product display name, handling both dataset variants. */
function pickName(p: FlipkartProduct): string {
  return (p.title ?? p.name ?? "").trim();
}

/** Original/list price, handling both dataset variants. */
function pickOriginalPrice(p: FlipkartProduct): number {
  return parsePrice(p.actual_price ?? p.original_price);
}

function slug(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60) || "item";
}

/** Parse a price that may be a number, "₹1,999", "Rs. 459", etc. Returns 0 if unparseable. */
function parsePrice(value: string | number | undefined): number {
  if (value === undefined || value === null) return 0;
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  const cleaned = value.replace(/[^0-9.]/g, "");
  const num = parseFloat(cleaned);
  return Number.isFinite(num) ? num : 0;
}

function toImageArray(images: string[] | string | undefined): string[] {
  if (Array.isArray(images)) return images.filter((i) => typeof i === "string" && i.length > 0);
  if (typeof images === "string" && images.length > 0) return [images];
  return [];
}

/** Pick a reasonable category name: prefer sub_category, then category, then breadcrumbs/brand. */
function pickCategory(p: FlipkartProduct): string {
  if (p.sub_category && p.sub_category.trim()) return p.sub_category.trim();
  if (p.category && p.category.trim()) return p.category.trim();
  const crumbs = Array.isArray(p.breadcrumbs)
    ? p.breadcrumbs
    : typeof p.breadcrumbs === "string"
      ? p.breadcrumbs.split(/[>/]/)
      : [];
  const cleaned = crumbs
    .map((c) => (typeof c === "string" ? c.trim() : ""))
    .filter((c) => c && c.toLowerCase() !== "home");
  if (cleaned.length >= 1) return cleaned[0];
  if (p.brand && p.brand.trim()) return p.brand.trim();
  return "General";
}

function pickSeller(p: FlipkartProduct): string {
  if (p.seller && p.seller.trim()) return p.seller.trim();
  if (p.seller_name && p.seller_name.trim()) return p.seller_name.trim();
  if (p.brand && p.brand.trim()) return p.brand.trim();
  return "ShopEase Marketplace";
}

async function main() {
  if (!fs.existsSync(DATA_FILE)) {
    console.error(`\nDataset not found at:\n  ${DATA_FILE}\n`);
    console.error(
      "Download `flipkart_fashion_products_dataset.json` from\n" +
        "  https://www.kaggle.com/datasets/aaditshukla/flipkart-fasion-products-dataset\n" +
        "and place it at the path above (create the `prisma/data/` folder).\n"
    );
    process.exit(1);
  }

  console.log("Reading dataset...");
  const raw = fs.readFileSync(DATA_FILE, "utf-8");
  const parsed = JSON.parse(raw) as FlipkartProduct[] | { products?: FlipkartProduct[] };
  const all: FlipkartProduct[] = Array.isArray(parsed) ? parsed : parsed.products ?? [];

  // Keep only usable rows (must have a name and a parseable price).
  const products = all
    .filter((p) => pickName(p) && parsePrice(p.selling_price ?? p.actual_price ?? p.original_price) > 0)
    .slice(0, SEED_LIMIT);

  console.log(`Loaded ${all.length} rows; seeding ${products.length} products (SEED_LIMIT=${SEED_LIMIT}).`);

  const hashedPassword = await bcrypt.hash(DEFAULT_VENDOR_PASSWORD, 10);

  // 1) Upsert categories.
  const categoryNames = Array.from(new Set(products.map(pickCategory)));
  const categoryIdByName = new Map<string, string>();
  for (const name of categoryNames) {
    const category = await prisma.category.upsert({
      where: { name },
      update: {},
      create: { name, description: `${name} products` },
    });
    categoryIdByName.set(name, category.id);
  }
  console.log(`Categories ready: ${categoryIdByName.size}`);

  // 2) Upsert vendors (User -> Vendor -> Shop) per unique seller.
  const sellerNames = Array.from(new Set(products.map(pickSeller)));
  const vendorByName = new Map<string, { vendorId: string; shopId: string }>();
  for (const sellerName of sellerNames) {
    const email = `${slug(sellerName)}@seed.shopease.local`;

    await prisma.user.upsert({
      where: { email },
      update: {},
      create: { email, password: hashedPassword, role: "VENDOR", name: sellerName },
    });

    const vendor = await prisma.vendor.upsert({
      where: { email },
      update: {},
      create: { name: sellerName, email },
    });

    const shop = await prisma.shop.upsert({
      where: { vendorId: vendor.id },
      update: {},
      create: { name: `${sellerName} Store`, description: `Official store of ${sellerName}`, vendorId: vendor.id },
    });

    vendorByName.set(sellerName, { vendorId: vendor.id, shopId: shop.id });
  }
  console.log(`Vendors/shops ready: ${vendorByName.size}`);

  // 3) Upsert products. Use Flipkart pid/_id as the stable primary key for idempotency.
  let created = 0;
  for (const p of products) {
    const productName = pickName(p);
    const id = (p.pid || p._id || slug(productName)).toString();
    const sellingPrice = parsePrice(p.selling_price ?? p.actual_price ?? p.original_price);
    const originalPrice = pickOriginalPrice(p);
    const discount =
      originalPrice > sellingPrice && originalPrice > 0
        ? Math.round(((originalPrice - sellingPrice) / originalPrice) * 100)
        : 0;
    const images = toImageArray(p.images);
    const categoryId = categoryIdByName.get(pickCategory(p))!;
    const { vendorId, shopId } = vendorByName.get(pickSeller(p))!;

    await prisma.product.upsert({
      where: { id },
      update: {
        price: sellingPrice,
        discount,
        inventory: p.out_of_stock ? 0 : 100,
        image: images,
      },
      create: {
        id,
        name: (productName || "Unnamed product").slice(0, 255),
        description: (p.description ?? productName ?? "No description available.").slice(0, 2000),
        price: sellingPrice,
        discount,
        categoryId,
        inventory: p.out_of_stock ? 0 : 100,
        image: images,
        vendorId,
        shopId,
      },
    });
    created++;
    if (created % 100 === 0) console.log(`  ...${created} products`);
  }

  console.log(`\nDone. Seeded ${created} products across ${vendorByName.size} vendors and ${categoryIdByName.size} categories.`);
}

async function run() {
  try {
    await main();
  } catch (e) {
    console.error("Seed failed:", e);
    process.exitCode = 1;
  } finally {
    await prisma.$disconnect();
  }
}

run();
