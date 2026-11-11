
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
} from "lucide-react";

import Navbar from "../components/Navbar";
import { useCart } from "../context/CartContext";
import { logInteraction } from "../services/interactionService";

const API_URL = "http://127.0.0.1:5000/api/products/";

// Local product images stored in frontend/public/images/
const localProductImages = {
  "Mechanical Keyboard": "/images/mechanical-keyboard.jpg",
  "Wireless Mouse": "/images/wireless-mouse.jpg",
  "Cotton T-Shirt": "/images/cotton-tshirt.jpg",
  "Table Lamp": "/images/table-lamp.jpg",
  "Non Stick Cookware Set": "/images/non-stick-cookware-set.jpg",
  "Mixer Grinder": "/images/mixer-grinder.jpg",
  "The Alchemist": "/images/the-alchemist.jpg",
  "Cricket Bat": "/images/cricket-bat.jpg",
  "Electric Kettle": "/images/electric-kettle.jpg",
  "Leather Backpack": "/images/leather-backpack.jpg",
  "Smartphone": "/images/smartphone.jpg",
  "Atomic Habits": "/images/atomic-habits.jpg",
  "Rich Dad Poor Dad": "/images/rich-dad-poor-dad.jpg",
  "Yoga Mat": "/images/yoga-mat.jpg",
  "Denim Jeans": "/images/denim-jeans.jpg",
  "Football": "/images/football.jpg",
  "Wireless Headphones": "/images/wireless-headphones.jpg",
  "Dumbbell Set": "/images/dumbbell-set.jpg",
  "Smart Watch": "/images/smart-watch.jpg",
  "Running Shoes": "/images/running-shoes.jpg",
};

const categories = [
  { name: "All", icon: Sparkles },
  { name: "Electronics", icon: Headphones },
  { name: "Fashion", icon: Shirt },
  { name: "Home & Kitchen", icon: House },
  { name: "Sports", icon: Dumbbell },
  { name: "Books", icon: BookOpen },
];

function Home() {
  const [products, setProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
          image:
            localProductImages[product.name] ||
            product.image_url ||
            "",
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

  // Search and category filtering
  const filteredProducts = products.filter((product) => {
    const query = searchQuery.toLowerCase();

    const matchesSearch =
      product.name.toLowerCase().includes(query) ||
      (product.description || "").toLowerCase().includes(query);

    const matchesCategory =
      selectedCategory === "All" ||
      product.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

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
                ShopSense AI is designed to understand your interests
                and help you discover relevant products.
              </p>
            </div>

            <div className="bg-white/15 rounded-2xl p-6 min-w-48 text-center">
              <Sparkles size={36} className="mx-auto mb-2" />
              <p className="font-bold text-xl">AI Discovery</p>
              <p className="text-sm text-purple-100">
                Coming soon
              </p>
            </div>
          </div>
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
              <p className="text-sm text-gray-500 mb-5">
                Showing {filteredProducts.length} of {products.length} products
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredProducts.map((product) => {
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

                        <Link to={`/product/${product.id}`}>
                          <h3 className="font-bold text-lg mt-2 hover:text-purple-600">
                            {product.name}
                          </h3>
                        </Link>

                        <p className="text-sm text-gray-500 mt-2">
                          {product.description}
                        </p>

                        <p className="text-xs text-gray-400 mt-3">
                          {product.stock > 0
                            ? `${product.stock} in stock`
                            : "Out of stock"}
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
            </>
          )}
        </section>
      </main>

      {/* Floating AI Chatbot Button */}
      <Link
        to="/chatbot"
        aria-label="Open ShopSense AI Assistant"
        className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-full bg-gradient-to-r from-purple-700 to-indigo-600 px-5 py-4 text-white shadow-xl transition duration-300 hover:scale-105 hover:shadow-2xl"
      >
        <Bot size={25} />
        <span className="font-semibold">Ask AI</span>
      </Link>
    </div>
  );
}

export default Home;
