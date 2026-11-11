
import { useState } from "react";
import { Link } from "react-router-dom";
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

function Navbar({ searchQuery, setSearchQuery }) {
  const { cart, wishlist } = useCart();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const cartCount = cart.reduce(
    (total, item) => total + item.quantity,
    0
  );

  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-5 md:px-8">
        <div className="h-20 flex items-center justify-between gap-5">

          {/* Logo */}
          <Link
            to="/"
            onClick={closeMenu}
            className="flex items-center gap-2 shrink-0"
          >
            <div className="bg-purple-600 text-white p-2.5 rounded-xl">
              <Sparkles size={23} />
            </div>

            <div>
              <h1 className="text-xl font-bold tracking-tight">
                ShopSense<span className="text-purple-600"> AI</span>
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
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search products..."
                className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-11 pr-4 py-3 text-sm outline-none focus:border-purple-500 focus:bg-white transition"
              />
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-6 text-sm font-medium text-gray-600">
            <Link to="/" className="hover:text-purple-600">
              Home
            </Link>

            <a href="/#products" className="hover:text-purple-600">
              Products
            </a>

            <a href="/#recommendations" className="hover:text-purple-600">
              AI Discover
            </a>

            <Link
              to="/chatbot"
              className="flex items-center gap-1.5 text-purple-700 hover:text-purple-900"
            >
              <Bot size={18} />
              AI Assistant
            </Link>
          </nav>

          {/* Action Icons */}
          <div className="flex items-center gap-2 md:gap-4">
            <Link
              to="/wishlist"
              className="relative p-2.5 rounded-xl hover:bg-purple-50 text-gray-600 hover:text-purple-600"
              aria-label="Wishlist"
            >
              <Heart size={21} />
              {wishlist.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-purple-600 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center">
                  {wishlist.length}
                </span>
              )}
            </Link>

            <Link
              to="/cart"
              className="relative p-2.5 rounded-xl hover:bg-purple-50 text-gray-600 hover:text-purple-600"
              aria-label="Shopping cart"
            >
              <ShoppingCart size={21} />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-purple-600 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </Link>

            <Link
              to="/login"
              title="Login"
              className="hidden sm:flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold"
            >
              <UserRound size={17} />
              Login
            </Link>

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
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products..."
              className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-11 pr-4 py-3 text-sm outline-none focus:border-purple-500"
            />
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-100 py-4 space-y-4">
            <Link to="/" onClick={closeMenu} className="block font-medium">
              Home
            </Link>

            <a href="/#products" onClick={closeMenu} className="block font-medium">
              Products
            </a>

            <a href="/#recommendations" onClick={closeMenu} className="block font-medium">
              AI Discover
            </a>

            <Link
              to="/chatbot"
              onClick={closeMenu}
              className="flex items-center gap-2 font-semibold text-purple-700"
            >
              <Bot size={18} />
              AI Assistant
            </Link>

            <Link to="/wishlist" onClick={closeMenu} className="block font-medium">
              My Wishlist
            </Link>

            <Link to="/cart" onClick={closeMenu} className="block font-medium">
              Shopping Cart
            </Link>

            <Link
              to="/login"
              onClick={closeMenu}
              className="block font-medium text-purple-600"
            >
              Login / Sign Up
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}

export default Navbar;
