// Small helper to centralize API base URL
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8080";

export const api = (path) => `${API_BASE}${path}`;

export default api;
