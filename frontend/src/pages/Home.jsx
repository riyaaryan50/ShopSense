
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  ShoppingCart,
  Heart,
  Sparkles,
  ArrowRight,
  Headphones,
  Shirt,
  Dumbbell,
  BookOpen,
  House,
  Bot,
  ClipboardList,
} from "lucide-react";

import Navbar from "../components/Navbar";
import { useCart } from "../context/CartContext";
import { logInteraction } from "../services/interactionService";
import {
  getMyRecommendations,
  getPopular,
  semanticSearch,
} from "../services/aiService";
import { API_URL as API_BASE, getToken } from "../config";

const API_URL = `${API_BASE}/products/`;
const MIN_SEMANTIC_SCORE = 0.2;
const PAGE_SIZE = 8;

const SORTERS = {
  relevance: null,
  price_asc: (a, b) => Number(a.price) - Number(b.price),
  price_desc: (a, b) => Number(b.price) - Number(a.price),
  name: (a, b) => a.name.localeCompare(b.name),
};

const categories = [
  { name: "All", icon: Sparkles },
  { name: "Laptops", icon: Bot },
  { name: "Tablets", icon: BookOpen },
  { name: "Smartphones", icon: Headphones },
  { name: "Audio", icon: Headphones },
  { name: "Computer Accessories", icon: House },
  { name: "Study Essentials", icon: BookOpen },
  { name: "Hostel Essentials", icon: House },
  { name: "Backpacks", icon: Shirt },
  { name: "Storage & Data", icon: Dumbbell },
];

function Home() {
  const [products, setProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [personalizedProducts, setPersonalizedProducts] = useState([]);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [recommendationError, setRecommendationError] = useState("");
  const [recommendationMeta, setRecommendationMeta] = useState(null);
  const [semanticResults, setSemanticResults] = useState(null);
  const [sortBy, setSortBy] = useState("relevance");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [loggedInUser, setLoggedInUser] = useState(() => {
    try {
      const user =
        localStorage.getItem("user") ||
        sessionStorage.getItem("user");

      return user ? JSON.parse(user) : null;
    } catch {
      return null;
    }
  });

  const { addToCart, wishlist, toggleWishlist } = useCart();

  // Fetch products from Flask backend
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(API_URL);

        if (!response.ok) {
          throw new Error("Unable to fetch products.");
        }

        const data = await response.json();

        // Connect backend products with local images
        const formattedProducts = data.map((product) => ({
          ...product,
          image: product.image_url || "",
        }));

        setProducts(formattedProducts);
      } catch (err) {
        console.error("Product fetching error:", err);
        setError(
          "Could not load products. Please check whether the backend is running."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

// Unified recommendations from the backend gateway: blends the content-based
// model (history), survey answers (NLP semantic match), the hybrid NCF service
// when deployed, and a popularity baseline. Guests get popular products.
const fetchPersonalizedRecommendations = async (user) => {
  try {
    setRecommendationLoading(true);
    setRecommendationError("");

    const data = user?.id && getToken()
      ? await getMyRecommendations(5)
      : await getPopular(5);

    setRecommendationMeta({
      explanation: data.explanation ||
        "Popular with other shoppers right now. Log in or take the survey for personal picks.",
      hasSurvey: Boolean(data.has_survey),
      coldStart: data.cold_start ?? true,
    });

    setPersonalizedProducts(
      (data.recommendations || []).map((product) => ({
        ...product,
        image: product.image_url || "",
      }))
    );
  } catch (error) {
    console.error("Recommendation error:", error);
    setRecommendationError(error.message);
  } finally {
    setRecommendationLoading(false);
  }
};

// Semantic search (Member 4 NLP service via the backend proxy).
useEffect(() => {
  const query = searchQuery.trim();
  // Short queries use keyword filtering; stale semantic results are ignored
  // because `semanticActive` requires the query to match.
  if (query.length < 3) return;
  let cancelled = false;
  const timer = setTimeout(async () => {
    try {
      const data = await semanticSearch(query, 12);
      if (!cancelled) {
        setSemanticResults({ query, engine: data.engine, results: data.results || [] });
      }
    } catch {
      if (!cancelled) setSemanticResults(null);
    }
  }, 350);
  return () => {
    cancelled = true;
    clearTimeout(timer);
  };
}, [searchQuery]);

// Fetch recommendations and respond to login/logout

// Fetch recommendations and respond to login/logout/cart/wishlist changes
  useEffect(() => {
    // Initial recommendation fetch
    fetchPersonalizedRecommendations(loggedInUser);

    // Handle login/logout
    const handleAuthChange = () => {
      try {
        const user =
          localStorage.getItem("user") ||
          sessionStorage.getItem("user");

        const parsedUser = user ? JSON.parse(user) : null;

        setLoggedInUser(parsedUser);
      } catch {
        setLoggedInUser(null);
      }
    };

  // Handle cart and wishlist changes
    const handleRecommendationRefresh = () => {
      console.log("Recommendation refresh event received!");
      const user =
        localStorage.getItem("user") ||
        sessionStorage.getItem("user");

      const currentUser = user ? JSON.parse(user) : null;

      if (currentUser?.id) {
        console.log(
          "Refreshing recommendations for user:",
          currentUser.id
        );
        fetchPersonalizedRecommendations(currentUser);
      }
    };

    window.addEventListener("auth-changed", handleAuthChange);

    window.addEventListener(
      "recommendations-updated",
      handleRecommendationRefresh
    );

    return () => {
      window.removeEventListener("auth-changed", handleAuthChange);

      window.removeEventListener(
        "recommendations-updated",
        handleRecommendationRefresh
      );
    };
  }, [loggedInUser?.id]);



  const matchesCategory = (product) =>
    selectedCategory === "All" || product.category === selectedCategory;

  // Semantic results are used when they belong to the current query;
  // otherwise fall back to simple keyword filtering.
  const semanticActive =
    semanticResults && semanticResults.query === searchQuery.trim();

  const matchedProducts = semanticActive
    ? semanticResults.results
        .filter((item) =>
          semanticResults.engine === "keyword-fallback" ||
          (item.score ?? 1) >= MIN_SEMANTIC_SCORE
        )
        .map((item) => ({
          ...(products.find((p) => p.id === item.id) || item),
          image: item.image_url || "",
          semanticScore: item.score,
        }))
        .filter(matchesCategory)
    : products.filter((product) => {
        const query = searchQuery.toLowerCase();
        const matchesSearch =
          product.name.toLowerCase().includes(query) ||
          (product.description || "").toLowerCase().includes(query);
        return matchesSearch && matchesCategory(product);
      });

  const filteredProducts = SORTERS[sortBy]
    ? [...matchedProducts].sort(SORTERS[sortBy])
    : matchedProducts;
  const visibleProducts = filteredProducts.slice(0, visibleCount);

  const handleAddToCart = (product) => {
    addToCart(product);
    logInteraction(product.id, "add_to_cart");
  };

  const handleWishlist = (product) => {
    const exists = wishlist.some(
      (item) => item.id === product.id
    );

    toggleWishlist(product);

    logInteraction(
      product.id,
      exists ? "remove_from_wishlist" : "add_to_wishlist"
    );
  };

  return (
    <div className="min-h-screen bg-[#f8f8fc] text-gray-900">
      <Navbar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />

      <main className="max-w-7xl mx-auto px-5 md:px-8">

        {/* Hero Section */}
        <section className="grid lg:grid-cols-2 gap-10 items-center py-14 md:py-20">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-purple-100 text-purple-700 px-4 py-2 text-sm font-semibold mb-6">
              <Sparkles size={16} />
              Smart Shopping Starts Here
            </div>

            <h1 className="text-4xl md:text-6xl font-bold leading-tight">
              Shopping made
              <span className="block text-purple-600">
                smarter with AI.
              </span>
            </h1>

            <p className="mt-6 text-gray-500 text-lg leading-8 max-w-xl">
              Discover products that match your interests.
              Get personalized recommendations and enjoy
              a smarter shopping experience with ShopSense AI.
            </p>

            <div className="flex flex-wrap gap-4 mt-8">
              <a
                href="#products"
                className="bg-purple-600 hover:bg-purple-700 text-white px-7 py-3.5 rounded-xl font-semibold flex items-center gap-2"
              >
                Explore Products <ArrowRight size={18} />
              </a>

              <a
                href="#recommendations"
                className="bg-white border border-gray-200 hover:border-purple-400 px-7 py-3.5 rounded-xl font-semibold"
              >
                Discover AI
              </a>
            </div>

            <div className="flex gap-8 mt-10">
              <div>
                <h3 className="text-2xl font-bold">
                  {products.length}
                </h3>
                <p className="text-sm text-gray-500">Products</p>
              </div>

              <div>
                <h3 className="text-2xl font-bold">AI</h3>
                <p className="text-sm text-gray-500">
                  Powered discovery
                </p>
              </div>

              <div>
                <h3 className="text-2xl font-bold">24/7</h3>
                <p className="text-sm text-gray-500">
                  Shopping access
                </p>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-5 bg-purple-300 blur-3xl opacity-30 rounded-full" />

            <div className="relative w-full h-[350px] md:h-[480px] bg-gradient-to-br from-purple-200 to-indigo-200 rounded-3xl shadow-xl flex items-center justify-center overflow-hidden">
              <div className="text-center">
                <ShoppingCart
                  size={100}
                  className="mx-auto text-purple-600"
                />
                <p className="text-purple-800 font-bold text-2xl mt-5">
                  ShopSense AI
                </p>
                <p className="text-purple-700 mt-2">
                  Smart Shopping Experience
                </p>
              </div>
            </div>

            <div className="absolute bottom-6 left-6 right-6 bg-white/95 backdrop-blur rounded-2xl p-4 shadow-lg">
              <div className="flex items-center gap-3">
                <div className="bg-purple-100 p-3 rounded-xl text-purple-600">
                  <Sparkles />
                </div>

                <div>
                  <p className="font-bold">
                    AI Product Discovery
                  </p>
                  <p className="text-sm text-gray-500">
                    Find products you'll love.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* AI Banner */}
        <section
          id="recommendations"
          className="bg-gradient-to-r from-purple-700 to-indigo-600 rounded-3xl p-8 md:p-12 text-white mb-16"
        >
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div>
              <div className="flex items-center gap-2 text-purple-200 mb-3">
                <Sparkles size={18} />
                <span className="font-semibold">
                  INTELLIGENT SHOPPING
                </span>
              </div>

              <h2 className="text-3xl font-bold">
                Your shopping, personalized.
              </h2>

              <p className="mt-3 text-purple-100 max-w-xl">
                Answer a 1-minute survey about what you study, how you'll
                use it and your budget. Our AI matches your answers to every
                product and keeps learning from what you browse.
              </p>
            </div>

            <Link
              to="/survey"
              className="bg-white text-purple-700 hover:bg-purple-50 rounded-2xl px-7 py-5 min-w-48 text-center shadow-lg transition"
            >
              <ClipboardList size={32} className="mx-auto mb-2" />
              <p className="font-bold text-lg">
                {recommendationMeta?.hasSurvey ? "Update your survey" : "Take the survey"}
              </p>
              <p className="text-sm text-purple-500">Get matched picks →</p>
            </Link>
          </div>
        </section>

        {/* Personalized Recommendations */}
        <section className="mb-16">
          <div className="mb-7">
            <p className="text-purple-600 font-semibold text-sm">
              HYBRID AI · BROWSING HISTORY + SURVEY + POPULARITY
            </p>

            <h2 className="text-3xl font-bold mt-2">
              {loggedInUser ? "Recommended For You" : "Trending Now"}
            </h2>

            <p className="text-gray-500 mt-2">
              {recommendationMeta?.explanation ||
                "Products selected based on your shopping interests."}
            </p>

            {!loggedInUser && (
              <p className="text-sm mt-2">
                <Link to="/login" className="text-purple-600 font-semibold">Log in</Link>
                {" or "}
                <Link to="/survey" className="text-purple-600 font-semibold">take the survey</Link>
                {" for personalised picks."}
              </p>
            )}
          </div>

          {recommendationLoading && (
            <div className="bg-white rounded-2xl p-8 text-center text-purple-600">
              Finding products you may like...
            </div>
          )}

          {recommendationError && (
            <div className="bg-white rounded-2xl p-8 text-center">
              <p className="text-red-500">{recommendationError}</p>
              <button
                onClick={() =>
                    fetchPersonalizedRecommendations(loggedInUser)
                }
                className="mt-4 bg-purple-600 text-white px-5 py-2 rounded-xl"
              >
                Try Again
              </button>
              </div>
            )}

            {!recommendationLoading &&
              !recommendationError &&
              personalizedProducts.length === 0 && (
                <div className="bg-white rounded-2xl p-8 text-center">
                  <p className="text-gray-600">
                    Explore products, add items to your cart or wishlist,
                    and we'll personalize your recommendations.
                  </p>
                </div>
            )}

            {!recommendationLoading &&
              personalizedProducts.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-5">
                  {personalizedProducts.map((product) => (
                    <div
                      key={product.id}
                      className="bg-white rounded-2xl overflow-hidden border border-gray-100 hover:shadow-xl transition"
                    >
                      <Link to={`/product/${product.id}`}>
                        {product.image ? (
                          <img
                            src={product.image}
                            alt={product.name}
                            className="w-full h-44 object-cover"
                          />
                        ) : (
                          <div className="w-full h-44 bg-purple-50 flex items-center justify-center">
                            <ShoppingCart size={40} className="text-purple-400" />
                          </div>
                        )}

                        <div className="p-4">
                          <p className="text-purple-600 text-xs font-semibold uppercase">
                            {product.category}
                          </p>

                          <h3 className="font-bold mt-2">
                            {product.name}
                          </h3>

                          <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                            {product.description}
                          </p>

                          <p className="font-bold text-lg mt-3">
                            ₹{Number(product.price).toLocaleString("en-IN")}
                          </p>

                          {product.reason && (
                            <p className="mt-2 flex items-start gap-1.5 text-xs text-purple-700 bg-purple-50 rounded-lg px-2 py-1.5">
                              <Sparkles size={13} className="mt-0.5 shrink-0" />
                              {product.reason}
                            </p>
                          )}
                        </div>
                      </Link>
                    </div>
                  ))}
                </div>
              )}
        </section>

        {/* Categories */}
        <section className="mb-16">
          <div className="mb-7">
            <p className="text-purple-600 font-semibold text-sm">
              BROWSE COLLECTIONS
            </p>

            <h2 className="text-3xl font-bold mt-2">
              Shop by Category
            </h2>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {categories.map((category) => {
              const Icon = category.icon;

              return (
                <button
                  key={category.name}
                  onClick={() => {
                    setSelectedCategory(category.name);

                    document.getElementById("products")?.scrollIntoView({
                      behavior: "smooth",
                    });
                  }}
                  className={`p-5 rounded-2xl border text-left transition ${
                    selectedCategory === category.name
                      ? "bg-purple-600 text-white border-purple-600"
                      : "bg-white border-gray-100 hover:border-purple-300"
                  }`}
                >
                  <Icon size={26} className="mb-4" />

                  <h3 className="font-bold text-sm">
                    {category.name}
                  </h3>

                  <p
                    className={`text-xs mt-1 ${
                      selectedCategory === category.name
                        ? "text-purple-100"
                        : "text-gray-400"
                    }`}
                  >
                    Explore collection
                  </p>
                </button>
              );
            })}
          </div>
        </section>

        {/* Products */}
        <section id="products" className="mb-20">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4 mb-8">
            <div>
              <p className="text-purple-600 font-semibold text-sm">
                OUR COLLECTION
              </p>

              <h2 className="text-3xl font-bold mt-2">
                Discover Products
              </h2>

              <p className="text-gray-500 mt-2">
                Find something you'll love.
              </p>
            </div>

            <div className="relative">
              <Search
                size={18}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
              />

              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search products..."
                className="bg-white border border-gray-200 rounded-xl pl-11 pr-4 py-3 outline-none focus:border-purple-500 w-full sm:w-64"
              />
            </div>
          </div>

          {/* Category Filters */}
          <div className="flex flex-wrap gap-2 mb-8">
            {categories.map((category) => (
              <button
                key={category.name}
                onClick={() => setSelectedCategory(category.name)}
                className={`px-5 py-2 rounded-full text-sm font-medium ${
                  selectedCategory === category.name
                    ? "bg-purple-600 text-white"
                    : "bg-white text-gray-600 border border-gray-200"
                }`}
              >
                {category.name}
              </button>
            ))}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="bg-white rounded-2xl p-12 text-center">
              <p className="text-purple-600 font-semibold">
                Loading products...
              </p>
            </div>
          )}

          {/* Error State */}
          {!loading && error && (
            <div className="bg-white rounded-2xl p-12 text-center">
              <p className="text-red-500 font-medium">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 bg-purple-600 text-white px-6 py-2 rounded-xl"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && filteredProducts.length === 0 && (
            <div className="bg-white rounded-2xl p-12 text-center">
              <Search
                size={35}
                className="mx-auto text-gray-300 mb-4"
              />

              <h3 className="font-bold text-xl">
                No products found
              </h3>

              <p className="text-gray-500 mt-2">
                Try another search or category.
              </p>
            </div>
          )}

          {/* Product Cards */}
          {!loading && !error && filteredProducts.length > 0 && (
            <>
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-gray-500 flex flex-wrap items-center gap-2">
                Showing {visibleProducts.length} of {filteredProducts.length} products
                {semanticActive && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 text-purple-700 px-3 py-1 text-xs font-semibold">
                    <Sparkles size={13} />
                    {semanticResults.engine === "keyword-fallback"
                      ? "Keyword results (AI search offline)"
                      : `AI semantic search for “${semanticResults.query}”`}
                  </span>
                )}
              </p>

              <label className="flex items-center gap-2 text-sm text-gray-600">
                Sort by
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none focus:border-purple-500"
                >
                  <option value="relevance">{semanticActive ? "Relevance" : "Featured"}</option>
                  <option value="price_asc">Price: low to high</option>
                  <option value="price_desc">Price: high to low</option>
                  <option value="name">Name</option>
                </select>
              </label>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {visibleProducts.map((product) => {
                  const isWishlisted = wishlist.some(
                    (item) => item.id === product.id
                  );

                  return (
                    <div
                      key={product.id}
                      className="bg-white rounded-2xl overflow-hidden border border-gray-100 hover:shadow-xl transition group"
                    >
                      <div className="relative bg-gray-50">
                        <Link to={`/product/${product.id}`}>
                          {product.image ? (
                            <img
                              src={product.image}
                              alt={product.name}
                              onError={(e) => {
                                e.currentTarget.onerror = null;
                                e.currentTarget.style.display = "none";
                              }}
                              className="w-full h-56 object-cover group-hover:scale-105 transition duration-500"
                            />
                          ) : (
                            <div className="w-full h-56 flex items-center justify-center bg-purple-50 text-purple-400">
                              <ShoppingCart size={45} />
                            </div>
                          )}
                        </Link>

                        <button
                          onClick={() => handleWishlist(product)}
                          className="absolute top-4 right-4 bg-white rounded-full p-3 shadow-md"
                          aria-label="Toggle wishlist"
                        >
                          <Heart
                            size={19}
                            className={
                              isWishlisted
                                ? "fill-red-500 text-red-500"
                                : "text-gray-600"
                            }
                          />
                        </button>
                      </div>

                      <div className="p-5">
                        <p className="text-purple-600 text-xs font-semibold uppercase tracking-wide">
                          {product.category}
                        </p>

                        {product.brand && (
                          <p className="text-xs text-gray-500 mt-1">{product.brand}</p>
                        )}

                        {product.semanticScore != null && (
                          <p className="text-[11px] text-purple-600 mt-1 font-medium">
                            Relevance {Math.round(product.semanticScore * 100)}%
                          </p>
                        )}

                        <Link to={`/product/${product.id}`}>
                          <h3 className="font-bold text-lg mt-2 hover:text-purple-600">
                            {product.name}
                          </h3>
                        </Link>

                        <p className="text-sm text-gray-500 mt-2 line-clamp-3">
                          {product.description}
                        </p>

                        <p className="text-xs text-gray-400 mt-3">
                          Check seller availability before purchase
                        </p>

                        <div className="flex justify-between items-center mt-5">
                          <span className="text-xl font-bold">
                            ₹{Number(product.price).toLocaleString("en-IN")}
                          </span>

                          <button
                            onClick={() => handleAddToCart(product)}
                            disabled={product.stock <= 0}
                            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white p-3 rounded-xl"
                            aria-label="Add to cart"
                          >
                            <ShoppingCart size={19} />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {visibleProducts.length < filteredProducts.length && (
                <div className="mt-10 text-center">
                  <button
                    onClick={() => setVisibleCount((n) => n + PAGE_SIZE)}
                    className="rounded-xl border border-purple-200 bg-white px-8 py-3 font-semibold text-purple-700 hover:bg-purple-50"
                  >
                    Load More ({filteredProducts.length - visibleProducts.length} more)
                  </button>
                </div>
              )}
            </>
          )}
        </section>
      </main>

      {/* The floating AI assistant is rendered globally by <ChatWidget /> */}
    </div>
  );
}

export default Home;
