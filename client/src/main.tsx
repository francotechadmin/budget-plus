import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

import { Auth0Provider, AppState } from "@auth0/auth0-react";
import { getConfig } from "./lib/config";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const onRedirectCallback = (appState?: AppState) => {
  window.history.pushState(
    {},
    document.title,
    appState?.targetUrl || window.location.pathname
  );
};

const config = getConfig();

const providerConfig = {
  domain: config.domain,
  clientId: config.clientId,
  onRedirectCallback,
  authorizationParams: {
    redirect_uri: config.redirectUri,
    audience: config.audience,
  },
};

// Create a QueryClient instance
const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Auth0Provider {...providerConfig}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </Auth0Provider>
  </StrictMode>
);
