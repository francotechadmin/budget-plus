import axios from "axios";

// adds access tokens in all api requests
// this interceptor is only added when the auth0 instance is ready and exports the getAccessTokenSilently method
export const addAccessTokenInterceptor = (
  getAccessTokenSilently: () => Promise<string>
) => {
  axios.interceptors.request.use(async (config) => {
    const token = await getAccessTokenSilently();
    config.headers.Authorization = `Bearer ${token}`;

    // root url for api requests
    config.baseURL = import.meta.env.VITE_API_URL;

    return config;
  });
};

// export default httpClient;
