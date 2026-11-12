-- ShopSense: extend products with verified catalogue metadata.
-- Run once against the existing PostgreSQL database before restarting the backend.
-- IF NOT EXISTS makes this safe to rerun.

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS brand VARCHAR(120),
    ADD COLUMN IF NOT EXISTS original_price NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS marketplace VARCHAR(80),
    ADD COLUMN IF NOT EXISTS product_url TEXT,
    ADD COLUMN IF NOT EXISTS specifications JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS marketplace_links JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Optional data-quality guard for future writes.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'products_original_price_nonnegative'
    ) THEN
        ALTER TABLE products
            ADD CONSTRAINT products_original_price_nonnegative
            CHECK (original_price IS NULL OR original_price >= 0);
    END IF;
END $$;
