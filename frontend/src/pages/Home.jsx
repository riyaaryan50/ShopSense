
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  ShoppingCart,
  Heart,
  Sparkles,
  ArrowRight,
  Star,
  Headphones,
  Watch,
  Shirt,
  Laptop,
  Bot,
} from "lucide-react";

import Navbar from "../components/Navbar";
import { useCart } from "../context/CartContext";
import { logInteraction } from "../services/interactionService";

const products = [
  {
    id: 1,
    name: "Wireless Headphones",
    category: "Electronics",
    price: 2499,
    rating: 4.8,
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600",
    description: "Premium sound with comfortable wireless listening.",
  },
  {
    id: 2,
    name: "Smart Watch",
    category: "Electronics",
    price: 3999,
    rating: 4.7,
    image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600",
    description: "Track your fitness and stay connected.",
  },
  {
    id: 3,
    name: "Running Shoes",
    category: "Fashion",
    price: 2999,
    rating: 4.6,
    image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600",
    description: "Lightweight shoes for everyday comfort.",
  },
  {
    id: 4,
    name: "Travel Backpack",
    category: "Accessories",
    price: 1499,
    rating: 4.5,
    image: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600",
    description: "A stylish backpack for your daily essentials.",
  },
  {
    id: 5,
    name: "Bluetooth Speaker",
    category: "Electronics",
    price: 1999,
    rating: 4.7,
    image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600",
    description: "Enjoy powerful sound wherever you go.",
  },
  {
    id: 6,
    name: "Classic Sunglasses",
    category: "Fashion",
    price: 1299,
    rating: 4.4,
    image: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600",
    description: "A timeless style for sunny days.",
  },
  {
    id: 7,
    name: "Laptop",
    category: "Electronics",
    price: 54999,
    rating: 4.9,
    image: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600",
    description: "Powerful performance for work and creativity.",
  },
];

const categories = [
  { name: "All", icon: Sparkles },
  { name: "Electronics", icon: Headphones },
  { name: "Fashion", icon: Shirt },
  { name: "Accessories", icon: Watch },
];

function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  const { addToCart, wishlist, toggleWishlist } = useCart();

  const filteredProducts = products.filter((product) => {
    const matchesSearch = product.name
      .toLowerCase()
      .includes(searchQuery.toLowerCase());

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
                <h3 className="text-2xl font-bold">500+</h3>
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

            <img
              src="https://images.unsplash.com/photo-1607082349566-187342175e2f?w=1000"
              alt="Online shopping"
              className="relative w-full h-[350px] md:h-[480px] object-cover rounded-3xl shadow-xl"
            />

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

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                  className={`p-6 rounded-2xl border text-left transition ${
                    selectedCategory === category.name
                      ? "bg-purple-600 text-white border-purple-600"
                      : "bg-white border-gray-100 hover:border-purple-300"
                  }`}
                >
                  <Icon size={28} className="mb-4" />

                  <h3 className="font-bold">
                    {category.name}
                  </h3>

                  <p
                    className={`text-sm mt-1 ${
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

          {filteredProducts.length === 0 ? (
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
          ) : (
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
                        <img
                          src={product.image}
                          alt={product.name}
                          className="w-full h-56 object-cover group-hover:scale-105 transition duration-500"
                        />
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

                      <div className="flex items-center gap-1 mt-3 text-sm">
                        <Star
                          size={15}
                          className="fill-yellow-400 text-yellow-400"
                        />

                        <span className="font-semibold">
                          {product.rating}
                        </span>

                        <span className="text-gray-400">
                          (Demo rating)
                        </span>
                      </div>

                      <div className="flex justify-between items-center mt-5">
                        <span className="text-xl font-bold">
                          ₹{product.price.toLocaleString("en-IN")}
                        </span>

                        <button
                          onClick={() => handleAddToCart(product)}
                          className="bg-purple-600 hover:bg-purple-700 text-white p-3 rounded-xl"
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
