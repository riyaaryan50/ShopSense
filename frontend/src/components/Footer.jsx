
import { Link } from "react-router-dom";

function Footer() {
  return (
    <footer className="bg-brand-700 text-stone-300 mt-16">
      <div className="max-w-7xl mx-auto px-6 py-12">

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">

          {/* Brand */}
          <div>
            <Link to="/" className="text-2xl font-bold text-white">
              ShopSense <span className="text-gold-400">AI</span>
            </Link>

            <p className="mt-4 text-gray-400 leading-7">
              Your personal AI shopping assistant.
              Discover products you love with intelligent
              and personalized recommendations.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold text-lg mb-5">
              Quick Links
            </h3>

            <ul className="space-y-3">
              <li><Link to="/" className="hover:text-gold-300">Home</Link></li>
              <li><Link to="/history" className="hover:text-gold-300">Interaction History</Link></li>
              <li><Link to="/wishlist" className="hover:text-gold-300">My Wishlist</Link></li>
              <li><Link to="/cart" className="hover:text-gold-300">Shopping Cart</Link></li>
            </ul>
          </div>

          {/* Categories */}
          <div>
            <h3 className="text-white font-semibold text-lg mb-5">
              Categories
            </h3>

            <ul className="space-y-3">
              <li><a href="/#products" className="hover:text-gold-300">Laptops &amp; Tablets</a></li>
              <li><a href="/#products" className="hover:text-gold-300">Audio</a></li>
              <li><a href="/#products" className="hover:text-gold-300">Study Essentials</a></li>
              <li><a href="/#products" className="hover:text-gold-300">Hostel Essentials</a></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-white font-semibold text-lg mb-5">
              Contact Us
            </h3>

            <p className="mb-3">support@shopsense.ai</p>
            <p className="text-gray-400">India</p>
          </div>

        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-700 mt-12 pt-6 text-center">
          <p className="text-sm text-gray-400">
            © 2026 ShopSense AI. All rights reserved.
          </p>

          <p className="text-sm text-gray-500 mt-2">
            Made with ❤️ for smarter shopping.
          </p>
        </div>

      </div>
    </footer>
  );
}

export default Footer;
