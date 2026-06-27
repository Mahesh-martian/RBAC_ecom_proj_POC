-- Copy seeded catalog from shopease_prisma -> shopease (same Postgres server).
-- Idempotent: re-running inserts only missing rows.
-- Order respects FKs: users -> categories -> vendors -> shops -> products.
-- categoryId is remapped by category NAME so it survives name collisions with
-- categories that already exist in the target DB.

CREATE EXTENSION IF NOT EXISTS dblink;

SELECT dblink_connect('pz', 'host=localhost port=5432 dbname=shopease_prisma user=postgres password=postgres');

-- 1) users (role is enum in source, varchar in target -> cast to text)
INSERT INTO users (id, email, password, role, name, "createdAt", "updatedAt", "deletedAt")
SELECT * FROM dblink('pz',
  'SELECT id, email, password, role::text, name, "createdAt", "updatedAt", "deletedAt" FROM users')
  AS t(id varchar, email varchar, password varchar, role varchar, name varchar,
       "createdAt" timestamptz, "updatedAt" timestamptz, "deletedAt" timestamptz)
ON CONFLICT (email) DO NOTHING;

-- 2) categories (unique by name; keep existing target row on collision)
INSERT INTO categories (id, name, description, "createdAt", "updatedAt", "deletedAt")
SELECT * FROM dblink('pz',
  'SELECT id, name, description, "createdAt", "updatedAt", "deletedAt" FROM categories')
  AS t(id varchar, name varchar, description varchar,
       "createdAt" timestamptz, "updatedAt" timestamptz, "deletedAt" timestamptz)
ON CONFLICT (name) DO NOTHING;

-- 3) vendors (email unique, FK -> users.email)
INSERT INTO vendors (id, name, email, "profilePhoto", "isDeleted", "isSuspended", "createdAt", "updatedAt")
SELECT * FROM dblink('pz',
  'SELECT id, name, email, "profilePhoto", "isDeleted", "isSuspended", "createdAt", "updatedAt" FROM vendors')
  AS t(id varchar, name varchar, email varchar, "profilePhoto" varchar,
       "isDeleted" boolean, "isSuspended" boolean, "createdAt" timestamptz, "updatedAt" timestamptz)
ON CONFLICT (email) DO NOTHING;

-- 4) shops (vendorId unique, FK -> vendors.id)
INSERT INTO shops (id, name, description, logo, "vendorId", "createdAt", "updatedAt", "deletedAt", "isBlackListed")
SELECT * FROM dblink('pz',
  'SELECT id, name, description, logo, "vendorId", "createdAt", "updatedAt", "deletedAt", "isBlackListed" FROM shops')
  AS t(id varchar, name varchar, description varchar, logo varchar, "vendorId" varchar,
       "createdAt" timestamptz, "updatedAt" timestamptz, "deletedAt" timestamptz, "isBlackListed" boolean)
ON CONFLICT ("vendorId") DO NOTHING;

-- 5) products (remap categoryId by name; vendorId/shopId keep source ids)
INSERT INTO products (id, name, description, price, discount, "categoryId", inventory, image, "vendorId", "shopId", "createdAt", "updatedAt", "deletedAt")
SELECT src.id, src.name, src.description, src.price, src.discount,
       c.id AS "categoryId", src.inventory, src.image, src."vendorId", src."shopId",
       src."createdAt", src."updatedAt", src."deletedAt"
FROM dblink('pz',
  'SELECT p.id, p.name, p.description, p.price, p.discount, cat.name AS catname, p.inventory,
          p.image, p."vendorId", p."shopId", p."createdAt", p."updatedAt", p."deletedAt"
   FROM products p JOIN categories cat ON cat.id = p."categoryId"')
  AS src(id varchar, name varchar, description varchar, price double precision, discount double precision,
         catname varchar, inventory integer, image varchar[], "vendorId" varchar, "shopId" varchar,
         "createdAt" timestamptz, "updatedAt" timestamptz, "deletedAt" timestamptz)
JOIN categories c ON c.name = src.catname
ON CONFLICT (id) DO NOTHING;

SELECT dblink_disconnect('pz');
