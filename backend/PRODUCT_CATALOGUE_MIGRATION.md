# ShopSense student product catalogue

This update replaces the 20 generic sample products with 20 named, branded products useful for college, coursework, coding, online classes and hostel life.

## What changed

- `product_catalog.json`: readable source catalogue with full descriptions, model-specific specifications, product images, primary purchase pages and additional marketplace links.
- `seed_products.sql`: re-runnable PostgreSQL seed/update script. It updates existing product IDs **2–21** in place, so existing foreign-key references continue to point to valid product rows.
- `migrations/001_add_product_catalogue_fields.sql`: adds catalogue metadata columns, including `marketplace_links`.
- `app/routes/product.py` and `app/models.py`: the existing API/model already supported most catalogue fields; no redesign was needed.
- `frontend/src/pages/Home.jsx`: shows actual catalogue image URLs, brand labels and student-focused category filters.
- `frontend/src/pages/ProductDetails.jsx`: shows detailed specifications and all marketplace links. The old fabricated Amazon/Flipkart/Myntra price comparison was removed.
- `recommendation_model/recommender.py`: content keywords were updated to describe the new catalogue, and brand/specifications are now included in TF-IDF features.

## Apply to your local project

1. Back up your PostgreSQL database.
2. Copy the updated project source into your working ShopSense folder.
3. From pgAdmin Query Tool, run `backend/migrations/001_add_product_catalogue_fields.sql`.
4. Then run `backend/seed_products.sql`.
5. Restart Flask and the recommendation API.
6. Open the frontend and confirm that 20 products appear. Open several product detail pages and test their external purchase links.

The seed script updates product IDs 2–21 instead of inserting duplicate rows. It does not delete users, reviews, interactions, cart rows or wishlist rows.

## Important recommendation-data note

The existing interaction records and `svd_model.pkl` were created against the old sample catalogue. Because the same product IDs now represent new products, old demo interactions may no longer describe what users actually liked. For a clean demonstration, clear only test/demo cart, wishlist, review and interaction rows after backing up, then collect fresh interactions and retrain SVD from the new interaction data. Do not clear real user activity.

The content-based recommender keyword map has been updated. The SVD algorithm itself has not been changed.

## Prices, product pages and images

- Prices in the seed data are indicative snapshots/references researched on **12 November 2026**; they are not live prices. A few hard-to-source SKUs use a catalogue reference value rather than a confirmed live offer. Marketplace prices, seller, delivery and availability can change. The `stock=50` value is only an internal ShopSense cart limit, not marketplace inventory.
- Each product has a primary model/product page in `product_url`. Additional sources are in `marketplace_links`. Some are manufacturer pages; others are exact retailer product listings. Search pages are explicitly labelled as searches.
- The product identity/model and purchase-page destination were checked against manufacturer or retailer pages during catalogue preparation. A checked URL does not guarantee that a seller still has stock, ships to every PIN code, or is an authorised seller.
- Images use product imagery from manufacturer or retailer product pages/CDNs. Remote image URLs can change; if one stops loading, replace it with a current image URL from the same product's official or retailer listing.
- Verify the exact SKU, RAM/storage configuration, warranty, seller and return policy before purchasing.

## Security

Do not put your real `.env` file in a ZIP, Git repository or shared project folder. Use `.env.example` as a template and keep your local `.env` private. Rotate the JWT signing secret that was present in the uploaded archive before deployment or sharing.
