-- Created on first Postgres init. The default POSTGRES_DB creates `shopease`;
-- this adds the second logical database used by the RAG service (ecom).
SELECT 'CREATE DATABASE ecommerce'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ecommerce')\gexec
