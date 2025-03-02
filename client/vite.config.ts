import path from "path";
import { defineConfig, loadEnv } from "vite";
import viteReact from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";

export default ({ mode }: { mode: string }) => {
  process.env = {
    ...process.env,
    ...loadEnv(mode, process.cwd()),
  };
  console.log("VITE_BASE_PATH", process.env.VITE_BASE_PATH);
  return defineConfig({
    plugins: [TanStackRouterVite(), viteReact()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: true,
      port: 3000,
    },
    base: process.env.VITE_BASE_PATH || "/",
  });
};
