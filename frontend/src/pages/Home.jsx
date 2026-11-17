
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
import ProductImage from "../components/ProductImage";

const API_URL = `${API_BASE}/products/`;
// Relevance cut-off depends on the search engine: MiniLM cosine scores for a
// good match are ~0.3-0.6, while the TF-IDF fallback used in the lightweight
// (Vercel) deployment scores good matches around 0.05-0.15.
const MIN_SEMANTIC_SCORE = 0.2;
const MIN_TFIDF_SCORE = 0.04;
const minScoreFor = (engine) =>
  engine && engine.startsWith("tfidf") ? MIN_TFIDF_SCORE : MIN_SEMANTIC_SCORE;
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
  const [searchQuery, setSearchQuery] = useState(
    () => new URLSearchParams(window.location.search).get("q") || ""
  );
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

  // Arriving from another page's search box (/?q=...): jump to the results.
  useEffect(() => {
    if (!new URLSearchParams(window.location.search).get("q")) return;
    const timer = setTimeout(
      () => document.getElementById("products")?.scrollIntoView({ behavior: "smooth" }),
      600
    );
    return () => clearTimeout(timer);
  }, []);

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
        "Popular with other shoppers right now.",
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
          (item.score ?? 1) >= minScoreFor(semanticResults.engine)
        )
        .map((item) => ({
          ...(products.find((p) => p.id === item.id) || item),
          image: item.image_url || "",
          // TF-IDF scores are not comparable to MiniLM's, so a percentage would
          // look misleadingly low; show the badge only for the embedding model.
          semanticScore: semanticResults.engine?.startsWith("tfidf") ? null : item.score,
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
    <div className="min-h-screen bg-canvas text-gray-900">
      <Navbar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />

      <main className="max-w-7xl mx-auto px-5 md:px-8">

        {/* Hero Section */}
        <section className="grid lg:grid-cols-[1.05fr_1fr] gap-12 lg:gap-16 items-center pt-12 pb-16 md:pt-20 md:pb-24">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 sm:px-4 py-1.5 text-[10px] sm:text-xs font-semibold uppercase tracking-[0.1em] sm:tracking-[0.16em] whitespace-nowrap text-gold-700 ring-1 ring-black/5 shadow-sm mb-7">
              <span className="h-1.5 w-1.5 rounded-full bg-gold-500" />
              Built for students · Powered by AI
            </div>

            <h1 className="text-[2.75rem] leading-[1.04] md:text-7xl text-brand-700">
              Everything college needs,
              <span className="block italic font-medium text-gold-600">chosen smarter.</span>
            </h1>

            <p className="mt-7 text-lg leading-8 text-stone-600 max-w-xl">
              Describe what you need in plain words, take a one-minute survey, and let
              ShopSense match you with the right laptop, headphones or hostel essentials,
              backed by what real buyers say.
            </p>

            <div className="flex flex-wrap gap-3 mt-9">
              <a
                href="#products"
                className="group inline-flex items-center gap-2 rounded-full bg-brand-700 px-7 py-3.5 font-semibold text-white shadow-lg shadow-black/10 transition hover:bg-brand-900"
              >
                Explore products
                <ArrowRight size={18} className="transition group-hover:translate-x-0.5" />
              </a>
              <Link
                to="/survey"
                className="inline-flex items-center gap-2 rounded-full bg-white px-7 py-3.5 font-semibold text-brand-700 ring-1 ring-black/10 transition hover:ring-gold-400"
              >
                <ClipboardList size={18} className="text-gold-600" />
                Take the 1-minute survey
              </Link>
            </div>

            <dl className="mt-12 grid max-w-md grid-cols-3 divide-x divide-black/10">
              {[
                [products.length || 20, "Curated products"],
                ["4", "AI models"],
                ["24/7", "Shopping assistant"],
              ].map(([value, label]) => (
                <div key={label} className="px-5 first:pl-0">
                  <dt className="sr-only">{label}</dt>
                  <dd className="font-display text-3xl font-semibold text-brand-700">{value}</dd>
                  <dd className="mt-1 text-xs uppercase tracking-[0.14em] text-stone-500">{label}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Product collage */}
          <div className="relative">
            <div className="absolute inset-0 md:-inset-6 rounded-[2.5rem] bg-gradient-to-br from-gold-100 via-brand-50 to-transparent" aria-hidden="true" />
            <div className="relative grid grid-cols-2 gap-4 md:gap-5">
              {[2, 7, 13, 11]
                .map((id) => products.find((p) => p.id === id))
                .filter(Boolean)
                .map((product, index) => (
                  <Link
                    key={product.id}
                    to={`/product/${product.id}`}
                    title={product.name}
                    aria-label={`${product.name}, ₹${Number(product.price).toLocaleString("en-IN")}`}
                    className={`group relative block aspect-[4/5] rounded-3xl bg-white p-6 ring-1 ring-black/5 shadow-[0_10px_30px_-12px_rgba(0,0,0,0.18)] transition hover:-translate-y-1 hover:shadow-[0_20px_40px_-14px_rgba(0,0,0,0.25)] ${
                      index % 2 === 1 ? "translate-y-10" : ""
                    }`}
                  >
                    <span className="absolute left-4 top-4 z-10 rounded-full bg-canvas px-3 py-1 text-xs font-semibold text-brand-700 ring-1 ring-black/5">
                      ₹{Number(product.price).toLocaleString("en-IN")}
                    </span>
                    <ProductImage
                      src={product.image}
                      alt=""
                      className="h-full w-full object-contain transition duration-500 group-hover:scale-105"
                    />
                  </Link>
                ))}
            </div>

            <div className="absolute -bottom-10 left-4 md:-left-10 max-w-[260px] rounded-2xl bg-brand-700 p-4 text-white shadow-2xl ring-1 ring-white/10">
              <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-gold-300">
                <Sparkles size={14} /> Semantic search
              </p>
              <p className="mt-2 text-sm leading-6 text-stone-200">
                “something to keep my tea hot in class” finds the thermos — no exact keywords needed.
              </p>
            </div>
          </div>
        </section>

        {/* AI Banner */}
        <section
          id="recommendations"
          className="bg-gradient-to-r from-brand-700 to-brand-600 rounded-3xl p-8 md:p-12 text-white mb-16"
        >
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div>
              <div className="flex items-center gap-2 text-brand-200 mb-3">
                <Sparkles size={18} />
                <span className="font-semibold">
                  INTELLIGENT SHOPPING
                </span>
              </div>

              <h2 className="text-3xl font-bold">
                Your shopping, personalized.
              </h2>

              <p className="mt-3 text-brand-100 max-w-xl">
                Answer a 1-minute survey about what you study, how you'll
                use it and your budget. Our AI matches your answers to every
                product and keeps learning from what you browse.
              </p>
            </div>

            <Link
              to="/survey"
              className="bg-white text-brand-700 hover:bg-brand-50 rounded-2xl px-7 py-5 min-w-48 text-center shadow-lg transition"
            >
              <ClipboardList size={32} className="mx-auto mb-2" />
              <p className="font-bold text-lg">
                {recommendationMeta?.hasSurvey ? "Update your survey" : "Take the survey"}
              </p>
              <p className="text-sm text-brand-500">Get matched picks →</p>
            </Link>
          </div>
        </section>

        {/* Personalized Recommendations */}
        <section className="mb-16">
          <div className="mb-7">
            <p className="text-gold-600 font-semibold text-xs uppercase tracking-[0.18em]">
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
                <Link to="/login" className="text-brand-600 font-semibold">Log in</Link>
                {" or "}
                <Link to="/survey" className="text-brand-600 font-semibold">take the survey</Link>
                {" for personalised picks."}
              </p>
            )}
          </div>

          {recommendationLoading && (
            <div className="bg-white rounded-2xl p-8 text-center text-brand-600">
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
                className="mt-4 bg-brand-600 text-white px-5 py-2 rounded-xl"
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
                          <ProductImage src={product.image} alt={product.name} className="w-full h-44 object-contain bg-white p-5" />
                        ) : (
                          <div className="w-full h-44 bg-brand-50 flex items-center justify-center">
                            <ShoppingCart size={40} className="text-brand-400" />
                          </div>
                        )}

                        <div className="p-4">
                          <p className="text-gold-600 text-[11px] font-semibold uppercase tracking-[0.14em]">
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
                            <p className="mt-2 flex items-start gap-1.5 text-xs text-brand-700 bg-brand-50 rounded-lg px-2 py-1.5">
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
            <p className="text-gold-600 font-semibold text-xs uppercase tracking-[0.18em]">
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
                      ? "bg-brand-600 text-white border-brand-600"
                      : "bg-white border-gray-100 hover:border-brand-300"
                  }`}
                >
                  <Icon size={26} className="mb-4" />

                  <h3 className="font-bold text-sm">
                    {category.name}
                  </h3>

                  <p
                    className={`text-xs mt-1 ${
                      selectedCategory === category.name
                        ? "text-brand-100"
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
              <p className="text-gold-600 font-semibold text-xs uppercase tracking-[0.18em]">
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
                className="bg-white border border-gray-200 rounded-xl pl-11 pr-4 py-3 outline-none focus:border-brand-500 w-full sm:w-64"
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
                    ? "bg-brand-600 text-white"
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
              <p className="text-brand-600 font-semibold">
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
                className="mt-4 bg-brand-600 text-white px-6 py-2 rounded-xl"
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
                  <span className="inline-flex items-center gap-1 rounded-full bg-brand-100 text-brand-700 px-3 py-1 text-xs font-semibold">
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
                  className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500"
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
                            <ProductImage src={product.image} alt={product.name} className="w-full h-60 object-contain bg-white p-7 group-hover:scale-[1.03] transition duration-500" />
                          ) : (
                            <div className="w-full h-56 flex items-center justify-center bg-brand-50 text-brand-400">
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
                        <p className="text-gold-600 text-[11px] font-semibold uppercase tracking-[0.14em]">
                          {product.category}
                        </p>

                        {product.brand && (
                          <p className="text-xs text-gray-500 mt-1">{product.brand}</p>
                        )}

                        {product.semanticScore != null && (
                          <p className="text-[11px] text-brand-600 mt-1 font-medium">
                            Relevance {Math.round(product.semanticScore * 100)}%
                          </p>
                        )}

                        <Link to={`/product/${product.id}`}>
                          <h3 className="font-bold text-lg mt-2 hover:text-brand-600">
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
                            className="bg-brand-600 hover:bg-brand-700 disabled:bg-gray-400 text-white p-3 rounded-xl"
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
                    className="rounded-xl border border-brand-200 bg-white px-8 py-3 font-semibold text-brand-700 hover:bg-brand-50"
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
