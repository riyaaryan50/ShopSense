
const API_URL = "http://127.0.0.1:5000/api";

// Fetch all products
export const getProducts = async () => {
  try {
    const response = await fetch(`${API_URL}/products/`);

    if (!response.ok) {
      throw new Error("Failed to fetch products");
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching products:", error);
    throw error;
  }
};

// Fetch a single product
export const getProductById = async (productId) => {
  try {
    const products = await getProducts();

    return products.find(
      (product) => Number(product.id) === Number(productId)
    );
  } catch (error) {
    console.error("Error fetching product:", error);
    throw error;
  }
};
