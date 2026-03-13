-- Migration: add legacy traceability support to clients, products, orders and order_items
-- Safe for existing PostgreSQL data sets.

BEGIN;

ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS legacy_code VARCHAR;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clients_legacy_code
    ON clients (legacy_code)
    WHERE legacy_code IS NOT NULL;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS legacy_code VARCHAR;

CREATE UNIQUE INDEX IF NOT EXISTS ix_products_legacy_code
    ON products (legacy_code)
    WHERE legacy_code IS NOT NULL;

ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS series VARCHAR,
    ADD COLUMN IF NOT EXISTS order_number VARCHAR,
    ADD COLUMN IF NOT EXISTS legacy_client_code VARCHAR,
    ADD COLUMN IF NOT EXISTS client_name_snapshot VARCHAR,
    ADD COLUMN IF NOT EXISTS notes VARCHAR,
    ADD COLUMN IF NOT EXISTS source VARCHAR DEFAULT 'erp',
    ADD COLUMN IF NOT EXISTS subtotal DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS tax_amount DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS total_amount DOUBLE PRECISION;

UPDATE orders
SET source = 'erp'
WHERE source IS NULL;

ALTER TABLE orders
    ALTER COLUMN source SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_orders_series
    ON orders (series);

CREATE INDEX IF NOT EXISTS ix_orders_order_number
    ON orders (order_number);

CREATE INDEX IF NOT EXISTS ix_orders_legacy_client_code
    ON orders (legacy_client_code);

CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_source_series_number
    ON orders (source, series, order_number);

ALTER TABLE order_items
    ALTER COLUMN product_id DROP NOT NULL;

ALTER TABLE order_items
    ADD COLUMN IF NOT EXISTS line_number INTEGER,
    ADD COLUMN IF NOT EXISTS line_type VARCHAR DEFAULT 'product',
    ADD COLUMN IF NOT EXISTS legacy_article_code VARCHAR,
    ADD COLUMN IF NOT EXISTS description VARCHAR,
    ADD COLUMN IF NOT EXISTS line_amount DOUBLE PRECISION;

UPDATE order_items
SET line_type = 'product'
WHERE line_type IS NULL;

ALTER TABLE order_items
    ALTER COLUMN line_type SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_order_items_legacy_article_code
    ON order_items (legacy_article_code);

CREATE UNIQUE INDEX IF NOT EXISTS uq_order_items_order_line_number
    ON order_items (order_id, line_number)
    WHERE line_number IS NOT NULL;

COMMIT;
