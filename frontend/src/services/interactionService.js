
const API_URL = "http://127.0.0.1:5000/api/interactions/";

function getToken() {
  return (
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token")
  );
}

// Record interaction in Flask and PostgreSQL
export const logInteraction = async (productId, action) => {
  const token = getToken();

  if (!token) {
    console.log("Login required for interaction tracking.");
    return null;
  }

  // Convert frontend event names into backend event names
  const eventMapping = {
    view: "view",
    click: "click",
    add_to_cart: "cart",
    add_to_wishlist: "wishlist",
    remove_from_wishlist: "wishlist",
    purchase: "purchase",
  };

  const eventType = eventMapping[action];

  if (!eventType) {
    console.error("Unsupported interaction:", action);
    return null;
  }

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        product_id: productId,
        event_type: eventType,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Interaction recording failed.");
    }

    console.log("Interaction recorded in database:", data);

    return data.interaction;
  } catch (error) {
    console.error("Interaction tracking error:", error.message);
    return null;
  }
};

// Fetch logged-in user's interaction history
export const getInteractions = async () => {
  const token = getToken();

  if (!token) return [];

  try {
    const response = await fetch(API_URL, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Unable to fetch history.");
    }

    return (data.interactions || []).map((item) => ({
      id: item.id,
      productId: item.product_id,
      action: item.event_type,
      timestamp: item.created_at,
    }));
  } catch (error) {
    console.error("History fetching error:", error.message);
    return [];
  }
};

// Clearing history is not supported by the current backend API
export const clearInteractions = () => {
  alert("Clearing interaction history is not available yet.");
};
