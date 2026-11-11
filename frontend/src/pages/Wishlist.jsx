
import { useCart } from "../context/CartContext";
import { Link } from "react-router-dom";
import {
  Heart,
  ShoppingCart,
  Trash2,
  ArrowLeft,
  Sparkles,
  ArrowRight,
} from "lucide-react";

function Wishlist() {
  const { wishlist, toggleWishlist, addToCart } = useCart();

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 via-white to-white px-5 py-10 md:px-8">

      <div className="max-w-7xl mx-auto">

        {/* Back Navigation */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-purple-600 font-semibold hover:text-purple-800 transition"
        >
          <ArrowLeft size={19} />
          Continue Shopping
        </Link>

        {/* Page Heading */}
        <div className="mt-8 mb-9">
          <p className="text-purple-600 font-semibold text-sm flex items-center gap-2">
            <Sparkles size={16} />
            YOUR FAVOURITES
          </p>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-2">

            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
                My Wishlist
                <Heart
                  size={29}
                  className="inline-block ml-3 text-purple-600 fill-purple-600"
                />
              </h1>

              <p className="text-gray-500 mt-2">
                All the products you love, in one place.
              </p>
            </div>

            {wishlist.length > 0 && (
              <span className="bg-purple-100 text-purple-700 px-5 py-3 rounded-xl font-semibold w-fit">
                {wishlist.length} Saved {wishlist.length === 1 ? "Item" : "Items"}
              </span>
            )}

          </div>
        </div>

        {/* Empty Wishlist */}
        {wishlist.length === 0 ? (

          <div className="bg-white rounded-3xl p-10 md:p-16 text-center shadow-lg shadow-purple-100/50 border border-purple-100">

            <div className="bg-purple-100 w-24 h-24 rounded-full flex items-center justify-center mx-auto">
              <Heart
                size={43}
                className="text-purple-600"
              />
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mt-7">
              Your Wishlist is Empty!
            </h2>

            <p className="text-gray-500 mt-3 max-w-md mx-auto">
              You haven't saved any favourites yet.
              Explore our collection and save products you love.
            </p>

            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 mt-7 bg-purple-600 text-white px-7 py-3.5 rounded-xl font-semibold hover:bg-purple-700 hover:shadow-lg transition"
            >
              Explore Products
              <ArrowRight size={19} />
            </Link>

          </div>

        ) : (

          /* Wishlist Products */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-7">

            {wishlist.map((product) => (

              <div
                key={product.id}
                className="group bg-white rounded-2xl overflow-hidden border border-purple-100 shadow-sm hover:shadow-xl hover:shadow-purple-100 transition duration-300"
              >

                {/* Product Image */}
                <div className="relative bg-purple-50 overflow-hidden">

                  <Link to={`/product/${product.id}`}>
                    <img
                      src={product.image}
                      alt={product.name}
                      className="w-full h-60 object-contain p-5 group-hover:scale-105 transition duration-500"
                    />
                  </Link>

                  <div className="absolute top-4 right-4 bg-white p-2.5 rounded-full shadow-sm">
                    <Heart
                      size={19}
                      className="text-purple-600 fill-purple-600"
                    />
                  </div>

                  <span className="absolute top-4 left-4 bg-purple-600 text-white text-xs font-semibold px-3 py-1.5 rounded-full">
                    Saved
                  </span>

                </div>

                {/* Product Information */}
                <div className="p-5">

                  <p className="text-sm text-purple-600 font-medium">
                    {product.category}
                  </p>

                  <Link to={`/product/${product.id}`}>
                    <h3 className="font-bold text-lg text-gray-900 mt-2 hover:text-purple-600 transition">
                      {product.name}
                    </h3>
                  </Link>

                  <p className="text-purple-600 font-bold text-xl mt-3">
                    ₹{product.price.toLocaleString("en-IN")}
                  </p>

                  {/* Add to Cart */}
                  <button
                    onClick={() => addToCart(product)}
                    className="w-full mt-5 bg-purple-600 text-white py-3 rounded-xl font-semibold hover:bg-purple-700 hover:shadow-lg hover:shadow-purple-200 transition flex items-center justify-center gap-2"
                  >
                    <ShoppingCart size={18} />
                    Add to Cart
                  </button>

                  {/* Remove from Wishlist */}
                  <button
                    onClick={() => toggleWishlist(product)}
                    className="w-full mt-3 border border-purple-200 text-purple-600 py-3 rounded-xl font-semibold hover:bg-purple-50 transition flex items-center justify-center gap-2"
                  >
                    <Trash2 size={17} />
                    Remove
                  </button>

                </div>

              </div>

            ))}

          </div>

        )}

      </div>
    </div>
  );
}

export default Wishlist;
