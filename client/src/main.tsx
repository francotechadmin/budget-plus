import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

import { Auth0Provider, AppState } from "@auth0/auth0-react";
import { getConfig } from "./lib/config";

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
    redirect_uri: window.location.origin,
    ...(config.audience ? { audience: config.audience } : null),
  },
};

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Auth0Provider {...providerConfig}>
      <App />
    </Auth0Provider>
  </StrictMode>
);
