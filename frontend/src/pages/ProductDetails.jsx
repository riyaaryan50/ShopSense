
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

  // Fetch products from the Flask backend
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getProducts();

        if (!Array.isArray(data)) {
          throw new Error("Invalid product data received from server.");
        }

        setProducts(data);
      } catch (err) {
        console.error("Product loading error:", err);
        setError("Unable to load product details. Please check whether the backend is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  // Find the selected product using its backend ID
  const product = products.find(
    (item) => String(item.id) === String(id)
  );

  const isWishlisted = product
    ? wishlist.some((item) => item.id === product.id)
    : false;

  // Record product view
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

  // Loading screen
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

  // Backend error screen
  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#f8f8fc] px-5">
        <Package size={55} className="text-purple-400" />

        <h2 className="text-2xl font-bold mt-5">
          Unable to Load Product
        </h2>

        <p className="text-gray-500 text-center mt-3">
          {error}
        </p>

        <Link
          to="/"
          className="mt-6 bg-purple-600 text-white px-6 py-3 rounded-xl font-semibold"
        >
          Back to Home
        </Link>
      </div>
    );
  }

  // Product not found
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

        <Link
          to="/"
          className="mt-5 text-purple-600 font-semibold"
        >
          Back to Home
        </Link>
      </div>
    );
  }

  // Demo review data until NLP integration
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

  // Demo prices only — not actual seller prices
  const productPrice = Number(product.price) || 0;

  const priceComparisons = [
    { store: "Amazon", price: productPrice },
    { store: "Flipkart", price: Math.round(productPrice * 1.08) },
    { store: "Myntra", price: Math.round(productPrice * 1.12) },
  ];

  const lowestPrice = Math.min(
    ...priceComparisons.map((item) => item.price)
  );

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

            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-[350px] md:h-[480px] object-cover"
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

            <div className="flex items-center gap-2 mt-4">
              <Star
                className="text-gray-300"
                size={19}
              />

              <span className="text-gray-400 text-sm">
                Rating not available
              </span>
            </div>

            <p className="text-gray-500 leading-8 mt-6">
              {product.description || "No product description available."}
            </p>

            <h2 className="text-3xl font-bold mt-7">
              ₹{productPrice.toLocaleString("en-IN")}
            </h2>

            <p className="text-sm text-green-600 mt-2">
              {Number(product.stock) > 0
                ? `${product.stock} units available`
                : "Stock information unavailable"}
            </p>

            {/* Action Buttons */}
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

            {/* Additional Information */}
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

            {/* Customer Sentiment */}
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

                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-green-500" />
                    Positive
                  </span>
                  <strong>{reviewAnalysis.positive}%</strong>
                </div>

                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-red-400" />
                    Negative
                  </span>
                  <strong>{reviewAnalysis.negative}%</strong>
                </div>

                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-yellow-400" />
                    Neutral
                  </span>
                  <strong>{reviewAnalysis.neutral}%</strong>
                </div>

              </div>
            </div>

            {/* Review Insights */}
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

        {/* Price Comparison */}
        <section className="mt-14 bg-white rounded-3xl p-6 md:p-10 shadow-sm">

          <div className="flex flex-wrap items-center gap-3">

            <div className="bg-indigo-100 text-indigo-600 p-3 rounded-xl">
              <TrendingDown size={25} />
            </div>

            <div>
              <h2 className="text-2xl font-bold">
                Compare Prices
              </h2>

              <p className="text-gray-500 text-sm">
                Compare this product across shopping platforms.
              </p>
            </div>

          </div>

          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-xl p-4 mt-7 text-sm">
            Demo comparison only. Prices are illustrative and
            are not live or verified seller offers.
          </div>

          <div className="overflow-x-auto mt-7">
            <table className="w-full text-left min-w-[500px]">

              <thead>
                <tr className="border-b text-gray-500 text-sm">
                  <th className="py-4">Shopping Website</th>
                  <th className="py-4">Price</th>
                  <th className="py-4">Status</th>
                </tr>
              </thead>

              <tbody>
                {priceComparisons.map((item) => (
                  <tr
                    key={item.store}
                    className="border-b border-gray-100"
                  >
                    <td className="py-5 font-semibold">
                      {item.store}
                    </td>

                    <td className="py-5 font-bold text-lg">
                      ₹{item.price.toLocaleString("en-IN")}
                    </td>

                    <td className="py-5">
                      {item.price === lowestPrice ? (
                        <span className="bg-green-100 text-green-700 px-3 py-2 rounded-full text-xs font-semibold">
                          Lowest demo price
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">
                          Demo price
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>

            </table>
          </div>

          <p className="text-xs text-gray-400 mt-5">
            Real product matching, seller links and live prices
            will be integrated using verified listings or permitted APIs.
          </p>

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
