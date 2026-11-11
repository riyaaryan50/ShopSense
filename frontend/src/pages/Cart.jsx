
import { useCart } from "../context/CartContext";
import { Link } from "react-router-dom";
import {
  Trash2,
  ShoppingBag,
  Plus,
  Minus,
  ArrowLeft,
  ShieldCheck,
  Sparkles,
  ShoppingCart,
} from "lucide-react";

function Cart() {
  const { cart, removeFromCart, updateQuantity } = useCart();

  const totalAmount = cart.reduce(
    (total, item) => total + item.price * item.quantity,
    0
  );

  const totalItems = cart.reduce(
    (sum, item) => sum + item.quantity,
    0
  );

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
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-8 mb-9">
          <div>
            <p className="text-purple-600 font-semibold text-sm flex items-center gap-2">
              <Sparkles size={16} />
              YOUR SHOPPING BAG
            </p>

            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2">
              My Shopping Cart
            </h1>

            <p className="text-gray-500 mt-2">
              Review your items before checkout.
            </p>
          </div>

          {cart.length > 0 && (
            <div className="bg-purple-100 text-purple-700 px-5 py-3 rounded-xl font-semibold w-fit">
              {totalItems} {totalItems === 1 ? "Item" : "Items"}
            </div>
          )}
        </div>

        {/* Empty Cart */}
        {cart.length === 0 ? (
          <div className="bg-white rounded-3xl p-10 md:p-16 text-center shadow-lg shadow-purple-100/50 border border-purple-100">

            <div className="bg-purple-100 w-24 h-24 rounded-full flex items-center justify-center mx-auto">
              <ShoppingBag size={43} className="text-purple-600" />
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mt-7">
              Your Cart is Empty!
            </h2>

            <p className="text-gray-500 mt-3 max-w-md mx-auto">
              Looks like you haven't added anything yet.
              Explore our collection and find something you love.
            </p>

            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 mt-7 bg-purple-600 text-white px-7 py-3.5 rounded-xl font-semibold hover:bg-purple-700 hover:shadow-lg transition"
            >
              <ShoppingCart size={19} />
              Explore Products
            </Link>

          </div>
        ) : (

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

            {/* Cart Items */}
            <div className="lg:col-span-2 space-y-5">

              {cart.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-2xl border border-purple-100 shadow-sm hover:shadow-md transition p-4 md:p-6 flex flex-col sm:flex-row gap-5 items-start sm:items-center"
                >

                  {/* Product Image */}
                  <div className="bg-purple-50 rounded-xl p-2 shrink-0">
                    <img
                      src={item.image}
                      alt={item.name}
                      className="w-full sm:w-28 h-36 sm:h-28 object-contain rounded-lg"
                    />
                  </div>

                  {/* Product Information */}
                  <div className="flex-1 w-full">

                    <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-3 py-1 rounded-full">
                      {item.category}
                    </span>

                    <h3 className="font-bold text-lg text-gray-900 mt-3">
                      {item.name}
                    </h3>

                    <p className="text-purple-600 font-bold text-lg mt-2">
                      ₹{item.price.toLocaleString("en-IN")}
                    </p>

                    {/* Quantity Controls */}
                    <div className="flex items-center gap-4 mt-4">

                      <span className="text-sm text-gray-500">
                        Quantity:
                      </span>

                      <div className="flex items-center gap-3 bg-purple-50 border border-purple-100 rounded-lg p-1">

                        <button
                          onClick={() => updateQuantity(item.id, -1)}
                          className="p-1.5 rounded-md text-purple-600 hover:bg-purple-200 transition"
                          aria-label="Decrease quantity"
                        >
                          <Minus size={16} />
                        </button>

                        <span className="font-semibold text-gray-800 min-w-5 text-center">
                          {item.quantity}
                        </span>

                        <button
                          onClick={() => updateQuantity(item.id, 1)}
                          className="p-1.5 rounded-md text-purple-600 hover:bg-purple-200 transition"
                          aria-label="Increase quantity"
                        >
                          <Plus size={16} />
                        </button>

                      </div>
                    </div>

                  </div>

                  {/* Price and Remove */}
                  <div className="flex sm:flex-col items-center justify-between w-full sm:w-auto sm:items-end gap-4">

                    <div className="text-right">
                      <p className="text-xs text-gray-400">
                        Item Total
                      </p>

                      <p className="font-bold text-gray-900 text-lg mt-1">
                        ₹{(item.price * item.quantity).toLocaleString("en-IN")}
                      </p>
                    </div>

                    <button
                      onClick={() => removeFromCart(item.id)}
                      className="flex items-center gap-2 text-red-500 hover:text-red-700 text-sm font-medium transition"
                      aria-label={`Remove ${item.name}`}
                    >
                      <Trash2 size={17} />
                      Remove
                    </button>

                  </div>

                </div>
              ))}

            </div>

            {/* Order Summary */}
            <div className="lg:col-span-1">

              <div className="bg-white rounded-2xl border border-purple-100 shadow-lg shadow-purple-100/50 p-6 sticky top-28">

                <div className="flex items-center gap-3 mb-7">
                  <div className="bg-purple-100 p-3 rounded-xl">
                    <ShoppingBag size={22} className="text-purple-600" />
                  </div>

                  <h2 className="text-xl font-bold text-gray-900">
                    Order Summary
                  </h2>
                </div>

                <div className="space-y-4">

                  <div className="flex justify-between text-gray-600">
                    <span>Total Items</span>
                    <span className="font-semibold text-gray-900">
                      {totalItems}
                    </span>
                  </div>

                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal</span>
                    <span className="font-semibold text-gray-900">
                      ₹{totalAmount.toLocaleString("en-IN")}
                    </span>
                  </div>

                  <div className="flex justify-between text-gray-600">
                    <span>Delivery</span>
                    <span className="font-semibold text-green-600">
                      Free
                    </span>
                  </div>

                </div>

                <div className="border-t border-dashed border-purple-200 my-6" />

                <div className="flex justify-between items-center">
                  <span className="font-bold text-gray-900 text-lg">
                    Total Amount
                  </span>

                  <span className="text-2xl font-bold text-purple-600">
                    ₹{totalAmount.toLocaleString("en-IN")}
                  </span>
                </div>

                {/* Checkout */}
                <button
                  disabled
                  className="w-full mt-7 bg-gray-300 text-gray-500 py-4 rounded-xl font-semibold cursor-not-allowed"
                >
                  Checkout Coming Soon
                </button>

                <p className="text-xs text-gray-400 text-center mt-3">
                  Online payment integration will be added later.
                </p>

                {/* Security Information */}
                <div className="flex items-center justify-center gap-2 bg-purple-50 rounded-xl p-4 mt-6">
                  <ShieldCheck size={19} className="text-purple-600" />

                  <span className="text-xs text-gray-600 font-medium">
                    Secure shopping experience
                  </span>
                </div>

              </div>

            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default Cart;
