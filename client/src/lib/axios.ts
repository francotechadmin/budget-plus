// lib/api.ts
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// adds access tokens in all api requests
export function addAccessTokenInterceptor(
  getAccessTokenSilently: () => Promise<string>
) {
  api.interceptors.request.use(async (config) => {
    // Get the token (wait for it before proceeding)
    const token = await getAccessTokenSilently();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
}
