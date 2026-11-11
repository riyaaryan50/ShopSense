
import {
  createContext,
  useContext,
  useState,
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
    throw new Error("Please log in to use your cart.");
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
    throw new Error(data.message || "Something went wrong.");
  }

  return data;
}

export function CartProvider({ children }) {
  const [cart, setCart] = useState([]);
  const [wishlist, setWishlist] = useState([]);

  // Fetch saved cart from Flask backend
  const refreshCart = async () => {
    try {
      const data = await apiRequest(`${API_URL}/cart/`);

      // Fetch product details for images and categories
      const productResponse = await fetch(
        `${API_URL}/products/`
      );

      if (!productResponse.ok) {
        throw new Error("Unable to fetch product details.");
      }

      const productData = await productResponse.json();

      const products = Array.isArray(productData)
        ? productData
        : productData.products || [];

      // Convert backend cart items into frontend format
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

  // Add product to backend cart
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
    } catch (error) {
      console.error("Error adding product:", error.message);
      alert(error.message);
    }
  };

  // Update product quantity
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

  // Remove product from backend cart
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

  // Existing wishlist functionality
  const toggleWishlist = (product) => {
    setWishlist((prevWishlist) => {
      const exists = prevWishlist.some(
        (item) => item.id === product.id
      );

      if (exists) {
        return prevWishlist.filter(
          (item) => item.id !== product.id
        );
      }

      return [...prevWishlist, product];
    });
  };

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
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  return useContext(CartContext);
}
