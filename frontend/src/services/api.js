import axios from "axios";
import { supabase } from "./supabase.js";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use(async (config) => {
  // Always read the freshest session token from supabase-js; it handles refresh
  // automatically. Fall back gracefully when there is no session yet (e.g.
  // the /auth/me call that runs before login).
  const { data } = await supabase.auth.getSession();
  const token = data?.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
