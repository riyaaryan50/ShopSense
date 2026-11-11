
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getInteractions,
  clearInteractions,
} from "../services/interactionService";

import {
  ArrowLeft,
  Clock,
  Eye,
  ShoppingCart,
  Heart,
  Trash2,
  Sparkles,
  History,
  Activity,
  Package,
} from "lucide-react";

const products = [
  { id: 1, name: "Wireless Headphones" },
  { id: 2, name: "Smart Watch" },
  { id: 3, name: "Running Shoes" },
  { id: 4, name: "Backpack" },
  { id: 5, name: "Bluetooth Speaker" },
  { id: 6, name: "Sunglasses" },
  { id: 7, name: "Laptop" },
];

function InteractionHistory() {
  const [interactions, setInteractions] = useState([]);

  useEffect(() => {
    setInteractions(getInteractions().reverse());
  }, []);

  const handleClearHistory = () => {
    const confirmed = window.confirm(
      "Are you sure you want to clear your entire interaction history?"
    );

    if (confirmed) {
      clearInteractions();
      setInteractions([]);
    }
  };

  const getProductName = (productId) => {
    const product = products.find(
      (item) => item.id === productId
    );

    return product ? product.name : `Product ${productId}`;
  };

  const getActionDetails = (action) => {
    const actions = {
      view: {
        label: "Viewed Product",
        icon: Eye,
        color: "text-blue-600",
        background: "bg-blue-50",
      },

      add_to_cart: {
        label: "Added to Cart",
        icon: ShoppingCart,
        color: "text-purple-600",
        background: "bg-purple-50",
      },

      add_to_wishlist: {
        label: "Added to Wishlist",
        icon: Heart,
        color: "text-pink-600",
        background: "bg-pink-50",
      },

      remove_from_wishlist: {
        label: "Removed from Wishlist",
        icon: Trash2,
        color: "text-red-600",
        background: "bg-red-50",
      },
    };

    return actions[action] || {
      label: action,
      icon: Activity,
      color: "text-gray-600",
      background: "bg-gray-100",
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 via-white to-white px-5 py-10 md:px-8">

      <div className="max-w-6xl mx-auto">

        {/* Back Navigation */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-purple-600 font-semibold hover:text-purple-800 transition"
        >
          <ArrowLeft size={19} />
          Back to Home
        </Link>

        {/* Heading */}
        <div className="mt-8 mb-9">

          <p className="text-purple-600 font-semibold text-sm flex items-center gap-2">
            <Sparkles size={16} />
            YOUR SHOPPING JOURNEY
          </p>

          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-5 mt-3">

            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
                Interaction History
              </h1>

              <p className="text-gray-500 mt-3">
                Keep track of your recent shopping activities.
              </p>
            </div>

            {interactions.length > 0 && (
              <button
                onClick={handleClearHistory}
                className="inline-flex items-center justify-center gap-2 bg-red-50 text-red-600 border border-red-100 px-5 py-3 rounded-xl font-semibold hover:bg-red-100 transition"
              >
                <Trash2 size={18} />
                Clear History
              </button>
            )}

          </div>
        </div>

        {/* Activity Summary */}
        {interactions.length > 0 && (

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">

            <div className="bg-white border border-purple-100 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-gray-500 font-medium">
                  Total Activities
                </p>

                <div className="bg-purple-100 p-3 rounded-xl">
                  <Activity className="text-purple-600" size={22} />
                </div>
              </div>

              <h2 className="text-3xl font-bold text-gray-900 mt-4">
                {interactions.length}
              </h2>
            </div>

            <div className="bg-white border border-purple-100 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-gray-500 font-medium">
                  Products Explored
                </p>

                <div className="bg-blue-50 p-3 rounded-xl">
                  <Eye className="text-blue-600" size={22} />
                </div>
              </div>

              <h2 className="text-3xl font-bold text-gray-900 mt-4">
                {new Set(interactions.map((item) => item.productId)).size}
              </h2>
            </div>

            <div className="bg-white border border-purple-100 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-gray-500 font-medium">
                  Cart Activities
                </p>

                <div className="bg-pink-50 p-3 rounded-xl">
                  <ShoppingCart className="text-pink-600" size={22} />
                </div>
              </div>

              <h2 className="text-3xl font-bold text-gray-900 mt-4">
                {interactions.filter(
                  (item) => item.action === "add_to_cart"
                ).length}
              </h2>
            </div>

          </div>
        )}

        {/* Empty History */}
        {interactions.length === 0 ? (

          <div className="bg-white rounded-3xl p-10 md:p-16 text-center shadow-lg shadow-purple-100/50 border border-purple-100">

            <div className="bg-purple-100 w-24 h-24 rounded-full flex items-center justify-center mx-auto">
              <History size={43} className="text-purple-600" />
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mt-7">
              No Activities Yet!
            </h2>

            <p className="text-gray-500 mt-3 max-w-md mx-auto">
              Your shopping journey starts here.
              Explore products, add favourites, and your activities
              will appear here.
            </p>

            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 mt-7 bg-purple-600 text-white px-7 py-3.5 rounded-xl font-semibold hover:bg-purple-700 transition"
            >
              Explore Products
              <Package size={19} />
            </Link>

          </div>

        ) : (

          /* Activity Timeline */
          <div className="bg-white rounded-2xl border border-purple-100 shadow-sm overflow-hidden">

            <div className="p-6 border-b border-purple-100 flex items-center gap-3">

              <div className="bg-purple-100 p-3 rounded-xl">
                <History size={22} className="text-purple-600" />
              </div>

              <div>
                <h2 className="font-bold text-lg text-gray-900">
                  Recent Activities
                </h2>

                <p className="text-sm text-gray-500">
                  {interactions.length} recorded activities
                </p>
              </div>

            </div>

            <div className="divide-y divide-purple-50">

              {interactions.map((interaction, index) => {

                const action = getActionDetails(interaction.action);
                const ActionIcon = action.icon;

                return (
                  <div
                    key={`${interaction.timestamp}-${index}`}
                    className="p-5 md:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-purple-50/50 transition"
                  >

                    <div className="flex items-center gap-4">

                      <div className={`${action.background} ${action.color} p-3.5 rounded-xl shrink-0`}>
                        <ActionIcon size={22} />
                      </div>

                      <div>
                        <h3 className="font-bold text-gray-900">
                          {getProductName(interaction.productId)}
                        </h3>

                        <p className={`text-sm font-semibold mt-1 ${action.color}`}>
                          {action.label}
                        </p>
                      </div>

                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-500 sm:ml-auto">
                      <Clock size={16} />

                      <span>
                        {new Date(
                          interaction.timestamp
                        ).toLocaleString("en-IN", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                      </span>
                    </div>

                  </div>
                );
              })}

            </div>

          </div>

        )}

        {/* Bottom Message */}
        <div className="text-center mt-10">
          <p className="text-purple-600 font-semibold flex items-center justify-center gap-2">
            <Sparkles size={17} />
            Shop smarter with ShopSense AI.
          </p>
        </div>

      </div>
    </div>
  );
}

export default InteractionHistory;
