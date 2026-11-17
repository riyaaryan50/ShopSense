
import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  Search,
  ShoppingCart,
  Heart,
  Sparkles,
  Menu,
  X,
  UserRound,
  Bot,
} from "lucide-react";
import { useCart } from "../context/CartContext";

function getCurrentUser() {
  const token =
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token");

  const user =
    localStorage.getItem("user") ||
    sessionStorage.getItem("user");

  if (!token || !user) return null;

  try {
    return JSON.parse(user);
  } catch {
    return null;
  }
}

function Navbar({ searchQuery, setSearchQuery }) {
  const { cart, wishlist } = useCart();

  const navigate = useNavigate();
  const location = useLocation();

  const [currentUser, setCurrentUser] = useState(getCurrentUser);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // On the home page the search box filters the grid live; on every other
  // page it keeps its own text and Enter takes you to the home results.
  const standalone = typeof setSearchQuery !== "function";
  const [localQuery, setLocalQuery] = useState("");
  const query = standalone ? localQuery : searchQuery;
  const setQuery = standalone ? setLocalQuery : setSearchQuery;

  const submitSearch = (event) => {
    if (event.key !== "Enter") return;
    const text = query.trim();
    if (standalone) {
      if (text) navigate(`/?q=${encodeURIComponent(text)}`);
    } else {
      document.getElementById("products")?.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Keep authentication state synchronized
  useEffect(() => {
    setCurrentUser(getCurrentUser());
  }, [location.pathname]);

  // Listen for authentication changes in other tabs
  useEffect(() => {
    const syncAuth = () => {
      setCurrentUser(getCurrentUser());
    };

    window.addEventListener("storage", syncAuth);

    return () => {
      window.removeEventListener("storage", syncAuth);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");

    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");

    setCurrentUser(null);
    setMobileMenuOpen(false);

    window.dispatchEvent(new Event("auth-changed"));

    navigate("/");
  };

  const cartCount = cart.reduce(
    (total, item) => total + item.quantity,
    0
  );

  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <header className="sticky top-0 z-50 bg-canvas/85 backdrop-blur-xl border-b border-black/5">
      <div className="max-w-7xl mx-auto px-5 md:px-8">

        <div className="h-20 flex items-center justify-between gap-5">

          {/* Logo */}
          <Link
            to="/"
            onClick={closeMenu}
            className="flex items-center gap-2 shrink-0"
          >
            <div className="bg-brand-700 text-gold-300 p-2.5 rounded-xl shadow-sm ring-1 ring-gold-400/30">
              <Sparkles size={23} />
            </div>

            <div>
              <h1 className="text-xl font-bold tracking-tight">
                ShopSense<span className="text-gold-500"> AI</span>
              </h1>

              <p className="text-[10px] text-gray-400 tracking-widest uppercase">
                Smart Shopping
              </p>
            </div>
          </Link>

          {/* Desktop Search */}
          <div className="hidden md:block flex-1 max-w-md">
            <div className="relative">
              <Search
                size={18}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
              />

              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={submitSearch}
                aria-label="Search products"
                placeholder="Search products..."
                className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-11 pr-4 py-3 text-sm outline-none focus:border-brand-500 focus:bg-white transition"
              />
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-6 text-sm font-medium text-gray-600">

            <Link to="/" className="hover:text-brand-600">
              Home
            </Link>

            <a href="/#products" className="hover:text-brand-600">
              Products
            </a>

            <a href="/#recommendations" className="hover:text-brand-600">
              AI Discover
            </a>

            <Link to="/survey" className="hover:text-brand-600">
              Survey
            </Link>

            <Link
              to="/chatbot"
              className="flex items-center gap-1.5 text-brand-700 hover:text-brand-900"
            >
              <Bot size={18} />
              AI Assistant
            </Link>

          </nav>

          {/* Action Icons */}
          <div className="flex items-center gap-2 md:gap-4">

            {/* Wishlist */}
            <Link
              to="/wishlist"
              className="relative p-2.5 rounded-xl hover:bg-brand-50 text-gray-600 hover:text-brand-600"
              aria-label="Wishlist"
            >
              <Heart size={21} />

              {wishlist.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-brand-600 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center">
                  {wishlist.length}
                </span>
              )}
            </Link>

            {/* Cart */}
            <Link
              to="/cart"
              className="relative p-2.5 rounded-xl hover:bg-brand-50 text-gray-600 hover:text-brand-600"
              aria-label="Shopping cart"
            >
              <ShoppingCart size={21} />

              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-brand-600 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </Link>

            {/* Authentication */}
            {currentUser ? (
              <div className="hidden sm:flex items-center gap-3">

                <span className="text-sm font-semibold text-gray-700">
                  Hi, {currentUser.name || currentUser.username || "User"}
                </span>

                <button
                  onClick={handleLogout}
                  className="bg-white text-brand-700 ring-1 ring-black/10 hover:ring-brand-700 px-4 py-2.5 rounded-xl text-sm font-semibold transition"
                >
                  Logout
                </button>

              </div>
            ) : (
              <Link
                to="/login"
                title="Login"
                className="hidden sm:flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold"
              >
                <UserRound size={17} />
                Login
              </Link>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={23} /> : <Menu size={23} />}
            </button>

          </div>
        </div>

        {/* Mobile Search */}
        <div className="md:hidden pb-4">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />

            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={submitSearch}
              aria-label="Search products"
              placeholder="Search products..."
              className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-11 pr-4 py-3 text-sm outline-none focus:border-brand-500"
            />
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-100 py-4 space-y-4">

            <Link
              to="/"
              onClick={closeMenu}
              className="block font-medium"
            >
              Home
            </Link>

            <a
              href="/#products"
              onClick={closeMenu}
              className="block font-medium"
            >
              Products
            </a>

            <a
              href="/#recommendations"
              onClick={closeMenu}
              className="block font-medium"
            >
              AI Discover
            </a>

            <Link
              to="/survey"
              onClick={closeMenu}
              className="block font-medium"
            >
              Preference Survey
            </Link>

            <Link
              to="/chatbot"
              onClick={closeMenu}
              className="flex items-center gap-2 font-semibold text-brand-700"
            >
              <Bot size={18} />
              AI Assistant
            </Link>

            <Link
              to="/wishlist"
              onClick={closeMenu}
              className="block font-medium"
            >
              My Wishlist
            </Link>

            <Link
              to="/cart"
              onClick={closeMenu}
              className="block font-medium"
            >
              Shopping Cart
            </Link>

            {/* Mobile Authentication */}
            {currentUser ? (
              <div className="space-y-3">

                <p className="font-semibold text-gray-700">
                  Welcome, {currentUser.name || currentUser.username || "User"}
                </p>

                <button
                  onClick={handleLogout}
                  className="text-red-600 font-semibold"
                >
                  Logout
                </button>

              </div>
            ) : (
              <Link
                to="/login"
                onClick={closeMenu}
                className="block font-medium text-brand-600"
              >
                Login / Sign Up
              </Link>
            )}

          </div>
        )}

      </div>
    </header>
  );
}

export default Navbar;
