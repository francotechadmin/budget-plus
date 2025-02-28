import configJson from "../auth_config.json";

export function getConfig() {
  return {
    domain: configJson.domain,
    redirectUri: import.meta.env.VITE_REDIRECT_URI,
    clientId: configJson.clientId,
    audience: import.meta.env.VITE_AUDIENCE,
  };
}
