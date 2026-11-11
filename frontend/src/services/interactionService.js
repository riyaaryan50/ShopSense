
const STORAGE_KEY = "shopsense_interactions";

// Save a user interaction
export const logInteraction = (productId, action) => {
  const interaction = {
    productId,
    action,
    timestamp: new Date().toISOString(),
  };

  const existingInteractions = JSON.parse(
    localStorage.getItem(STORAGE_KEY) || "[]"
  );

  existingInteractions.push(interaction);

  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(existingInteractions)
  );

  console.log("Interaction recorded:", interaction);
};

// Get all recorded interactions
export const getInteractions = () => {
  return JSON.parse(
    localStorage.getItem(STORAGE_KEY) || "[]"
  );
};

// Clear interaction history
export const clearInteractions = () => {
  localStorage.removeItem(STORAGE_KEY);
};
