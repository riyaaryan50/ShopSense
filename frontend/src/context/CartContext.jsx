
import {
  createContext,
  useContext,
  useState,
  useEffect,
} from "react";

const CartContext = createContext();

const API_URL = "http://127.0.0.1:5000/api";

function getToken() {
  return (
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token")
  );
}

async function apiRequest(url, options = {}) {
  const token = getToken();

  if (!token) {
    throw new Error("Please log in to continue.");
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.error || data.message || "Something went wrong."
    );
  }

  return data;
}

export function CartProvider({ children }) {
  const [cart, setCart] = useState([]);
  const [wishlist, setWishlist] = useState([]);

  // Fetch product details
  const fetchProducts = async () => {
    const response = await fetch(`${API_URL}/products/`);

    if (!response.ok) {
      throw new Error("Unable to fetch product details.");
    }

    const data = await response.json();

    return Array.isArray(data) ? data : data.products || [];
  };

  // =========================
  // CART FUNCTIONS
  // =========================

  const refreshCart = async () => {
    if (!getToken()) {
      setCart([]);
      return [];
    }

    try {
      const data = await apiRequest(`${API_URL}/cart/`);
      const products = await fetchProducts();

      const updatedCart = (data.items || []).map((item) => {
        const product = products.find(
          (p) => Number(p.id) === Number(item.product_id)
        );

        return {
          ...item,
          id: item.cart_item_id,
          product_id: item.product_id,
          name: item.product_name,
          image: product?.image_url || product?.image || "",
          category: product?.category || "General",
          price: Number(item.price),
          quantity: Number(item.quantity),
        };
      });

      setCart(updatedCart);
      return updatedCart;
    } catch (error) {
      console.error("Error fetching cart:", error.message);
      return null;
    }
  };


  const addToCart = async (product) => {
    try {
      await apiRequest(`${API_URL}/cart/`, {
        method: "POST",
        body: JSON.stringify({
          product_id: product.id,
          quantity: 1,
        }),
      });

      await refreshCart();

      // Notify homepage to refresh personalized recommendations
      window.dispatchEvent(
        new Event("recommendations-updated")
      );

    } catch (error) {
      console.error("Error adding product:", error.message);
      alert(error.message);
    }
  };


  const updateQuantity = async (cartItemId, change) => {
    try {
      const item = cart.find(
        (item) => item.id === cartItemId
      );

      if (!item) return;

      const newQuantity = item.quantity + change;

      if (newQuantity <= 0) {
        await removeFromCart(cartItemId);
        return;
      }

      await apiRequest(`${API_URL}/cart/${cartItemId}`, {
        method: "PUT",
        body: JSON.stringify({
          quantity: newQuantity,
        }),
      });

      await refreshCart();
    } catch (error) {
      console.error("Error updating cart:", error.message);
      alert(error.message);
    }
  };

  const removeFromCart = async (cartItemId) => {
    try {
      await apiRequest(`${API_URL}/cart/${cartItemId}`, {
        method: "DELETE",
      });

      await refreshCart();
    } catch (error) {
      console.error("Error removing product:", error.message);
      alert(error.message);
    }
  };

  // =========================
  // WISHLIST FUNCTIONS
  // =========================

  const refreshWishlist = async () => {
    if (!getToken()) {
      setWishlist([]);
      return [];
    }

    try {
      const data = await apiRequest(`${API_URL}/wishlist/`);
      const products = await fetchProducts();

      const updatedWishlist = (data.wishlist || [])
        .map((item) => {
          const product = products.find(
            (p) => Number(p.id) === Number(item.product_id)
          );

          if (!product) return null;

          return {
            ...product,
            wishlist_item_id: item.wishlist_item_id,
          };
        })
        .filter(Boolean);

      setWishlist(updatedWishlist);
      return updatedWishlist;
    } catch (error) {
      console.error("Error fetching wishlist:", error.message);
      return null;
    }
  };

  const toggleWishlist = async (product) => {
    try {
      if (!getToken()) {
        alert("Please log in to use your wishlist.");
        return;
      }

      const existingItem = wishlist.find(
        (item) => Number(item.id) === Number(product.id)
      );

      if (existingItem) {
        await apiRequest(
          `${API_URL}/wishlist/${existingItem.wishlist_item_id}`,
          { method: "DELETE" }
        );
      } else {
        await apiRequest(`${API_URL}/wishlist/`, {
          method: "POST",
          body: JSON.stringify({
            product_id: product.id,
          }),
        });
      }

      await refreshWishlist();
      window.dispatchEvent(
        new Event("recommendations-updated")
      );
    } catch (error) {
      console.error("Wishlist error:", error.message);
      alert(error.message);
    }
  };

  // =========================
  // AUTHENTICATION SYNC
  // =========================

  useEffect(() => {
    const syncUserData = () => {
      if (getToken()) {
        refreshCart();
        refreshWishlist();
      } else {
        setCart([]);
        setWishlist([]);
      }
    };

    syncUserData();

    window.addEventListener("auth-changed", syncUserData);

    return () => {
      window.removeEventListener("auth-changed", syncUserData);
    };
  }, []);

  return (
    <CartContext.Provider
      value={{
        cart,
        wishlist,
        addToCart,
        updateQuantity,
        removeFromCart,
        toggleWishlist,
        refreshCart,
        refreshWishlist,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  return useContext(CartContext);
}
