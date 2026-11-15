
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
  MessageSquare,
  Package,
} from "lucide-react";

import { useCart } from "../context/CartContext";
import { logInteraction } from "../services/interactionService";
import { getProducts } from "../services/productService";
import {
  getReviewSummary,
  getSimilarProducts,
  submitReview,
} from "../services/aiService";
import SentimentSummary from "../components/SentimentSummary";

const SENTIMENT_BADGE = {
  positive: "bg-green-100 text-green-700",
  negative: "bg-red-100 text-red-700",
  neutral: "bg-yellow-100 text-yellow-800",
};



function ProductDetails() {
  const { id } = useParams();
  const { addToCart, wishlist, toggleWishlist } = useCart();

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [recommendedProducts, setRecommendedProducts] = useState([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [similarSource, setSimilarSource] = useState("");

  const [reviewSummary, setReviewSummary] = useState(null);
  const [reviewLoading, setReviewLoading] = useState(true);
  const [reviewError, setReviewError] = useState("");
  const [reviewForm, setReviewForm] = useState({ rating: 5, comment: "" });
  const [reviewMessage, setReviewMessage] = useState("");

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

  // Review sentiment summary (Member 4 NLP service via backend proxy)
  const loadReviewSummary = async () => {
    try {
      setReviewLoading(true);
      setReviewError("");
      setReviewSummary(await getReviewSummary(id));
    } catch (err) {
      setReviewSummary(null);
      setReviewError(err.message);
    } finally {
      setReviewLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    getReviewSummary(id)
      .then((data) => {
        if (!cancelled) {
          setReviewSummary(data);
          setReviewError("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setReviewSummary(null);
          setReviewError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) setReviewLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleSubmitReview = async (event) => {
    event.preventDefault();
    setReviewMessage("");
    try {
      await submitReview(Number(id), reviewForm.rating, reviewForm.comment);
      setReviewForm({ rating: 5, comment: "" });
      setReviewMessage("Thanks! Your review was added and analysed.");
      await loadReviewSummary();
    } catch (err) {
      setReviewMessage(
        err.status === 401 ? "Please log in to write a review." : err.message
      );
    }
  };

  // Similar products: content-based model, falling back to NLP embeddings
  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setRecommendationsLoading(true);
        setRecommendedProducts([]);

        const data = await getSimilarProducts(id, 5);
        setSimilarSource(data.source || "");

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
              <Star
                className={reviewSummary?.average_rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"}
                size={19}
              />
              <span className="text-gray-500 text-sm">
                {reviewSummary?.average_rating
                  ? `${reviewSummary.average_rating} / 5 · ${reviewSummary.total_reviews} reviews`
                  : "Rating not available"}
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
                Similar products{similarSource ? ` · ${similarSource}` : ""}.
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

        {/* AI Review Analysis (VADER sentiment + TF-IDF themes) */}
        <section className="mt-14 bg-white rounded-3xl p-6 md:p-10 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <div className="bg-purple-100 text-purple-600 p-3 rounded-xl">
              <Sparkles size={25} />
            </div>

            <div>
              <h2 className="text-2xl font-bold">AI Review Analysis</h2>
              <p className="text-gray-500 text-sm">
                Sentiment of every customer review (VADER) and the themes they mention.
              </p>
            </div>
          </div>

          {reviewLoading && (
            <p className="mt-8 text-gray-500">Analysing reviews…</p>
          )}

          {!reviewLoading && reviewError && (
            <p className="mt-8 rounded-xl bg-yellow-50 p-4 text-sm text-yellow-800">
              Review analysis is unavailable right now ({reviewError}).
            </p>
          )}

          {!reviewLoading && reviewSummary && (
            <>
              <div className="mt-8">
                <SentimentSummary summary={reviewSummary} />
              </div>

              <div className="mt-8 bg-purple-50 rounded-2xl p-5">
                <div className="flex items-center gap-2 text-purple-700 font-bold">
                  <MessageSquare size={19} />
                  AI Verdict
                </div>
                <p className="text-gray-700 mt-3 leading-7">{reviewSummary.verdict}</p>
              </div>

              {reviewSummary.reviews?.length > 0 && (
                <div className="mt-8">
                  <h3 className="font-bold text-lg mb-4">
                    Customer Reviews ({reviewSummary.reviews.length})
                  </h3>
                  <ul className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                    {reviewSummary.reviews.map((review) => (
                      <li key={review.id} className="rounded-xl border border-gray-100 p-4">
                        <div className="flex flex-wrap items-center gap-2 text-sm">
                          <span className="text-yellow-500" aria-label={`${review.rating} stars`}>
                            {"★".repeat(review.rating)}
                            <span className="text-gray-300">{"★".repeat(5 - review.rating)}</span>
                          </span>
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${SENTIMENT_BADGE[review.sentiment]}`}
                          >
                            {review.sentiment} ({review.compound > 0 ? "+" : ""}{review.compound})
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-gray-600 leading-6">{review.comment}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {/* Write a review */}
          <form onSubmit={handleSubmitReview} className="mt-8 rounded-2xl border border-gray-200 p-5">
            <h3 className="font-bold">Write a review</h3>
            <div className="mt-3 flex items-center gap-1" role="radiogroup" aria-label="Rating">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  type="button"
                  key={value}
                  role="radio"
                  aria-checked={reviewForm.rating === value}
                  aria-label={`${value} star${value > 1 ? "s" : ""}`}
                  onClick={() => setReviewForm((f) => ({ ...f, rating: value }))}
                >
                  <Star
                    size={24}
                    className={value <= reviewForm.rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"}
                  />
                </button>
              ))}
            </div>
            <textarea
              value={reviewForm.comment}
              onChange={(e) => setReviewForm((f) => ({ ...f, comment: e.target.value }))}
              required
              rows={3}
              placeholder="What did you like or dislike?"
              className="mt-3 w-full rounded-xl border border-gray-200 p-3 text-sm outline-none focus:border-purple-500"
            />
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <button
                type="submit"
                className="rounded-xl bg-purple-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-purple-700"
              >
                Submit review
              </button>
              {reviewMessage && <p className="text-sm text-gray-600">{reviewMessage}</p>}
            </div>
          </form>
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
