const API_BASE_URL = "http://127.0.0.1:5000";

export const getProducts = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/products/`);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    const products = await response.json();
    return products;
  } catch (error) {
    console.error("Failed to fetch products:", error);
    throw error;
  }
};