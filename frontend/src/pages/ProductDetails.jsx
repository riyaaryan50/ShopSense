
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Heart,
  ShoppingCart,
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  Truck,
  Star,
  ThumbsUp,
  ThumbsDown,
  TrendingDown,
  MessageSquare,
  Package,
} from "lucide-react";

import { useCart } from "../context/CartContext";
import { logInteraction } from "../services/interactionService";
import { getProducts } from "../services/productService";



function ProductDetails() {
  const { id } = useParams();
  const { addToCart, wishlist, toggleWishlist } = useCart();

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [recommendedProducts, setRecommendedProducts] = useState([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);

  // Fetch all products
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getProducts();

        if (!Array.isArray(data)) {
          throw new Error("Invalid product data received from server.");
        }

        const formattedProducts = data.map((item) => ({
          ...item,
          image: item.image_url || "",
        }));

        setProducts(formattedProducts);
      } catch (err) {
        console.error("Product loading error:", err);
        setError(
          "Unable to load product details. Please check whether the backend is running."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  // Fetch AI recommendations
  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setRecommendationsLoading(true);
        setRecommendedProducts([]);

        const response = await fetch(
          `http://127.0.0.1:5001/api/recommendations/${id}`
        );

        if (!response.ok) {
          throw new Error("Unable to fetch recommendations");
        }

        const data = await response.json();

        const formattedRecommendations = (
          data.recommendations || []
        ).map((item) => ({
          ...item,
          image: item.image_url || "",
        }));

        setRecommendedProducts(formattedRecommendations);
      } catch (err) {
        console.error("Recommendation error:", err);
        setRecommendedProducts([]);
      } finally {
        setRecommendationsLoading(false);
      }
    };

    if (id) {
      fetchRecommendations();
    }
  }, [id]);

  const product = products.find(
    (item) => String(item.id) === String(id)
  );

  const isWishlisted = product
    ? wishlist.some((item) => item.id === product.id)
    : false;

  // Log product view
  useEffect(() => {
    if (product) {
      logInteraction(product.id, "view");
    }
  }, [product]);

  const handleAddToCart = () => {
    if (!product) return;

    addToCart(product);
    logInteraction(product.id, "add_to_cart");
  };

  const handleWishlist = () => {
    if (!product) return;

    toggleWishlist(product);

    logInteraction(
      product.id,
      isWishlisted ? "remove_from_wishlist" : "add_to_wishlist"
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#f8f8fc]">
        <div className="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin" />
        <p className="mt-5 text-gray-600 font-medium">
          Loading product details...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#f8f8fc] px-5">
        <Package size={55} className="text-purple-400" />
        <h2 className="text-2xl font-bold mt-5">
          Unable to Load Product
        </h2>
        <p className="text-gray-500 text-center mt-3">{error}</p>
        <Link
          to="/"
          className="mt-6 bg-purple-600 text-white px-6 py-3 rounded-xl font-semibold"
        >
          Back to Home
        </Link>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#f8f8fc]">
        <Package size={55} className="text-purple-400" />
        <h2 className="text-3xl font-bold mt-5">
          Product Not Found
        </h2>
        <p className="text-gray-500 mt-3">
          This product is not available in the catalogue.
        </p>
        <Link to="/" className="mt-5 text-purple-600 font-semibold">
          Back to Home
        </Link>
      </div>
    );
  }

  const reviewAnalysis = {
    positive: 85,
    negative: 10,
    neutral: 5,
    likes: [
      "Good product quality and performance.",
      "Comfortable for everyday usage.",
      "Value for money according to customers.",
    ],
    complaints: [
      "Some customers reported minor issues.",
      "Product availability and delivery experience may vary.",
    ],
  };

  const productPrice = Number(product.price) || 0;

  return (
    <div className="min-h-screen bg-[#f8f8fc] text-gray-900">
      <main className="max-w-7xl mx-auto px-5 md:px-8 py-10">

        {/* Back Button */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-gray-500 hover:text-purple-600 mb-8"
        >
          <ArrowLeft size={18} />
          Back to Products
        </Link>

        {/* Product Information */}
        <section className="grid lg:grid-cols-2 gap-12 bg-white rounded-3xl p-6 md:p-10 shadow-sm">

          {/* Product Image */}
          <div className="bg-gray-50 rounded-2xl overflow-hidden flex items-center justify-center min-h-[350px]">
            {product.image ? (
              <img
                src={product.image}
                alt={product.name}
                onError={(e) => {
                  e.currentTarget.onerror = null;
                  e.currentTarget.style.display = "none";
                }}
                className="w-full h-[350px] md:h-[480px] object-contain p-4"
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-purple-400">
                <Package size={100} strokeWidth={1.2} />
                <p className="mt-4 text-sm text-gray-400">
                  Product image not available
                </p>
              </div>
            )}
          </div>

          {/* Product Details */}
          <div className="flex flex-col justify-center">

            <span className="bg-purple-100 text-purple-700 px-4 py-2 rounded-full text-sm font-semibold w-fit">
              {product.category || "Uncategorized"}
            </span>

            <h1 className="text-3xl md:text-4xl font-bold mt-5">
              {product.name}
            </h1>

            {product.brand && (
              <p className="text-gray-500 mt-2">
                Brand: <strong>{product.brand}</strong>
              </p>
            )}

            <div className="flex items-center gap-2 mt-4">
              <Star className="text-gray-300" size={19} />
              <span className="text-gray-400 text-sm">
                Rating not available
              </span>
            </div>

            <p className="text-gray-500 leading-8 mt-6">
              {product.description || "No product description available."}
            </p>


            {product.specifications &&
              Object.keys(product.specifications).length > 0 && (
                <div className="mt-7">
                  <h3 className="text-xl font-bold mb-4">
                    Product Specifications
                  </h3>

                  <div className="border rounded-xl divide-y">
                    {Object.entries(product.specifications).map(
                      ([key, value]) => (
                        <div
                          key={key}
                          className="flex justify-between gap-4 p-4 text-sm"
                        >
                          <span className="text-gray-500 capitalize">
                            {key.replace(/_/g, " ")}
                          </span>
                          <span className="font-semibold text-right">
                            {String(value)}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}


            <div className="flex items-center gap-3 mt-7">
              <h2 className="text-3xl font-bold">
                ₹{productPrice.toLocaleString("en-IN")}
              </h2>

              {product.original_price &&
                Number(product.original_price) > productPrice && (
                  <span className="text-gray-400 line-through">
                    ₹{Number(product.original_price).toLocaleString("en-IN")}
                  </span>
                )}
              </div>

            <p className="text-sm text-gray-500 mt-2">
              Seller availability is confirmed on the marketplace listing.
            </p>

            <p className="text-xs text-gray-500 mt-2">
              Listed price is indicative. Final price, seller, delivery and availability are confirmed by the marketplace at checkout.
            </p>

            <div className="flex flex-wrap gap-4 mt-8">
              <button
                onClick={handleAddToCart}
                disabled={Number(product.stock) <= 0}
                className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white py-4 rounded-xl font-semibold flex justify-center items-center gap-2"
              >
                <ShoppingCart size={20} />
                Add to Cart
              </button>

              <button
                onClick={handleWishlist}
                className="border border-gray-200 hover:border-purple-400 p-4 rounded-xl"
                aria-label="Toggle wishlist"
              >
                <Heart
                  size={22}
                  className={
                    isWishlisted
                      ? "fill-red-500 text-red-500"
                      : "text-gray-600"
                  }
                />
              </button>
            </div>

            {product.product_url && (
              <a
                href={product.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 w-full bg-green-600 hover:bg-green-700 text-white py-4 rounded-xl font-semibold flex justify-center items-center gap-2"
              >
                Buy Now on {product.marketplace || "Marketplace"}
                <span>↗</span>
              </a>
            )}


{product.marketplace_links &&
  Object.entries(product.marketplace_links).length > 0 && (() => {
    const allLinks = Object.entries(product.marketplace_links)
      .filter(([store, url]) =>
        typeof url === "string" &&
        /^https?:\/\//i.test(url)
      );

    // Remove duplicate URLs
    const uniqueLinks = allLinks.filter(
      ([store, url], index, arr) =>
        arr.findIndex(
          ([, existingUrl]) => existingUrl === url
        ) === index
    );

    const officialLinks = uniqueLinks.filter(([store]) =>
      /official/i.test(store)
    );

    const searchLinks = uniqueLinks.filter(([store]) =>
      /search/i.test(store)
    );

    const verifiedLinks = uniqueLinks.filter(([store]) =>
      /exact listing/i.test(store)
    );

    const otherLinks = uniqueLinks.filter(([store]) =>
      !/official|search|exact listing/i.test(store)
    );

    const renderLinks = (title, links, description) => {
      if (!links.length) return null;

      return (
        <div className="mb-5">
          <h4 className="font-bold text-gray-800 mb-3">
            {title}
          </h4>

          <div className="grid sm:grid-cols-2 gap-3">
            {links.map(([store, url]) => (
              <a
                key={store}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between gap-2 rounded-xl border border-gray-200 p-3 hover:border-purple-400 hover:bg-purple-50 transition"
              >
                <span className="font-semibold text-sm text-gray-700">
                  {store.replace(/(official|exact listing|search)/ig, "").trim()}
                </span>
                <span className="text-purple-600 text-sm">
                  Visit ↗
                </span>
              </a>
            ))}
          </div>

          <p className="text-xs text-gray-400 mt-2">
            {description}
          </p>
        </div>
      );
    };

    return (
      <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-5">
        <h3 className="text-xl font-bold text-gray-900 mb-5">
          Compare Purchasing Options
        </h3>

        {renderLinks(
          "Official Brand Stores",
          officialLinks,
          "Manufacturer websites and official brand stores."
        )}

        {renderLinks(
          "Exact Product Listings",
          verifiedLinks,
          "Listings labelled as exact matches. Confirm model and configuration before purchasing."
        )}

        {renderLinks(
          "Other Retailer Links",
          otherLinks,
          "Check the seller, exact model and product availability."
        )}

        {renderLinks(
          "Explore More Marketplaces",
          searchLinks,
          "These links open marketplace searches, not confirmed product listings."
        )}

        <div className="border-t pt-4 text-xs text-gray-500">
          Prices, stock, delivery and seller terms may change.
          Always verify the exact product configuration before payment.
        </div>
      </div>
    );
  })()}


            <div className="grid grid-cols-2 gap-4 mt-8">
              <div className="flex gap-3 items-center">
                <Truck className="text-purple-600" />
                <span className="text-sm text-gray-600">
                  Delivery information
                </span>
              </div>

              <div className="flex gap-3 items-center">
                <ShieldCheck className="text-purple-600" />
                <span className="text-sm text-gray-600">
                  Shopping protection
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* AI Recommended Products */}
        <section className="mt-14 bg-white rounded-3xl p-6 md:p-10 shadow-sm">

          <div className="flex items-center gap-3 mb-8">
            <div className="bg-purple-100 text-purple-600 p-3 rounded-xl">
              <Sparkles size={25} />
            </div>

            <div>
              <h2 className="text-2xl font-bold">
                Recommended Products for You
              </h2>
              <p className="text-gray-500 text-sm">
                AI-powered recommendations based on product similarity.
              </p>
            </div>
          </div>

          {recommendationsLoading ? (
            <div className="text-center py-10 text-gray-500">
              Loading recommendations...
            </div>
          ) : recommendedProducts.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">

              {recommendedProducts.map((item) => (
                <Link
                  to={`/product/${item.id}`}
                  key={item.id}
                  className="group border border-gray-100 rounded-2xl overflow-hidden hover:shadow-lg transition duration-300"
                >
                  <div className="bg-gray-50 h-44 flex items-center justify-center p-4">
                    {item.image ? (
                      <img
                        src={item.image}
                        alt={item.name}
                        onError={(e) => {
                          e.currentTarget.onerror = null;
                          e.currentTarget.style.display = "none";
                        }}
                        className="w-full h-full object-contain group-hover:scale-105 transition duration-300"
                      />
                    ) : (
                      <Package
                        size={55}
                        className="text-purple-300"
                      />
                    )}
                  </div>

                  <div className="p-4">
                    <span className="text-xs text-purple-600 font-semibold">
                      {item.category}
                    </span>

                    <h3 className="font-bold mt-2 text-gray-800 line-clamp-2">
                      {item.name}
                    </h3>

                    <p className="text-lg font-bold text-purple-700 mt-3">
                      ₹{Number(item.price).toLocaleString("en-IN")}
                    </p>

                    <p className="text-xs text-gray-400 mt-2">
                      AI Recommended
                    </p>
                  </div>
                </Link>
              ))}

            </div>
          ) : (
            <div className="text-center py-10 text-gray-500">
              No recommendations available right now.
            </div>
          )}

        </section>

        {/* AI Review Analysis */}
        <section className="mt-14 bg-white rounded-3xl p-6 md:p-10 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <div className="bg-purple-100 text-purple-600 p-3 rounded-xl">
              <Sparkles size={25} />
            </div>

            <div>
              <h2 className="text-2xl font-bold">
                AI Review Analysis
              </h2>
              <p className="text-gray-500 text-sm">
                Understand customer opinions quickly.
              </p>
            </div>

            <span className="ml-auto text-xs bg-yellow-100 text-yellow-800 px-3 py-2 rounded-full">
              Sample Analysis
            </span>
          </div>

          <div className="grid md:grid-cols-2 gap-10 mt-9">
            <div>
              <h3 className="font-bold text-lg mb-5">
                Customer Sentiment
              </h3>

              <div className="text-center mb-6">
                <h2 className="text-5xl font-bold text-green-600">
                  {reviewAnalysis.positive}%
                </h2>
                <p className="text-gray-500 mt-2">
                  Positive sentiment (illustrative)
                </p>
              </div>

              <div className="flex h-4 rounded-full overflow-hidden">
                <div
                  className="bg-green-500"
                  style={{ width: `${reviewAnalysis.positive}%` }}
                />
                <div
                  className="bg-red-400"
                  style={{ width: `${reviewAnalysis.negative}%` }}
                />
                <div
                  className="bg-yellow-400"
                  style={{ width: `${reviewAnalysis.neutral}%` }}
                />
              </div>

              <div className="space-y-4 mt-6">
                {[
                  { name: "Positive", value: reviewAnalysis.positive, color: "bg-green-500" },
                  { name: "Negative", value: reviewAnalysis.negative, color: "bg-red-400" },
                  { name: "Neutral", value: reviewAnalysis.neutral, color: "bg-yellow-400" },
                ].map((item) => (
                  <div key={item.name} className="flex justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${item.color}`} />
                      {item.name}
                    </span>
                    <strong>{item.value}%</strong>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-bold text-lg mb-5">
                Review Insights
              </h3>

              <div className="bg-green-50 rounded-2xl p-5 mb-5">
                <h4 className="font-semibold text-green-700 flex items-center gap-2">
                  <ThumbsUp size={18} />
                  What Customers Like
                </h4>

                <ul className="mt-4 space-y-3 text-sm text-gray-600">
                  {reviewAnalysis.likes.map((item, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="text-green-600">✓</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-red-50 rounded-2xl p-5">
                <h4 className="font-semibold text-red-700 flex items-center gap-2">
                  <ThumbsDown size={18} />
                  Common Complaints
                </h4>

                <ul className="mt-4 space-y-3 text-sm text-gray-600">
                  {reviewAnalysis.complaints.map((item, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="text-red-500">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="mt-8 bg-purple-50 rounded-2xl p-5">
            <div className="flex items-center gap-2 text-purple-700 font-bold">
              <MessageSquare size={19} />
              AI Verdict
            </div>

            <p className="text-gray-600 mt-3 leading-7">
              This section will summarize real customer reviews
              and highlight important product advantages and
              complaints after NLP integration.
            </p>
          </div>
        </section>

        {/* Bottom Section */}
        <section className="mt-14 bg-gradient-to-r from-purple-700 to-indigo-600 rounded-3xl p-8 md:p-10 text-white">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div>
              <div className="flex items-center gap-2 text-purple-200 mb-3">
                <Sparkles size={19} />
                ShopSense AI
              </div>

              <h2 className="text-2xl md:text-3xl font-bold">
                Shop smarter with AI.
              </h2>

              <p className="text-purple-100 mt-2">
                Discover products and make informed shopping decisions.
              </p>
            </div>

            <Link
              to="/"
              className="bg-white text-purple-700 px-6 py-3 rounded-xl font-semibold flex items-center gap-2"
            >
              Explore More
              <ArrowLeft size={18} className="rotate-180" />
            </Link>
          </div>
        </section>

      </main>
    </div>
  );
}

export default ProductDetails;
