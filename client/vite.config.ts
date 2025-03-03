import path from "path";
import { defineConfig, loadEnv } from "vite";
import viteReact from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import { VitePWA } from "vite-plugin-pwa";

export default ({ mode }: { mode: string }) => {
  process.env = {
    ...process.env,
    ...loadEnv(mode, process.cwd()),
  };

  return defineConfig({
    plugins: [
      TanStackRouterVite(),
      viteReact(),
      VitePWA({
        includeAssets: ["logo.ico", "apple-touch-icon.png"],
        manifest: {
          name: "Budget Plus",
          short_name: "Budget+",
          description: "Budget+ is a personal finance app",
          theme_color: "#ffffff",
          icons: [
            {
              src: "pwa-29x29.png",
              sizes: "29x29",
              type: "image/png",
            },
            {
              src: "pwa-40x40.png",
              sizes: "40x40",
              type: "image/png",
            },
            {
              src: "pwa-57x57.png",
              sizes: "57x57",
              type: "image/png",
            },
            {
              src: "pwa-58x58.png",
              sizes: "58x58",
              type: "image/png",
            },
            {
              src: "pwa-60x60.png",
              sizes: "60x60",
              type: "image/png",
            },
            {
              src: "pwa-80x80.png",
              sizes: "80x80",
              type: "image/png",
            },
            {
              src: "pwa-87x87.png",
              sizes: "87x87",
              type: "image/png",
            },
            {
              src: "pwa-114x114.png",
              sizes: "114x114",
              type: "image/png",
            },
            {
              src: "pwa-120x120.png",
              sizes: "120x120",
              type: "image/png",
            },
            {
              src: "pwa-180x180.png",
              sizes: "180x180",
              type: "image/png",
            },
            {
              src: "pwa-192x192.png",
              sizes: "192x192",
              type: "image/png",
            },
            {
              src: "pwa-512x512.png",
              sizes: "512x512",
              type: "image/png",
            },
            {
              src: "pwa-1024x1024.png",
              sizes: "1024x1024",
              type: "image/png",
            },
          ],
        },
        devOptions: {
          enabled: true,
          /* other options */
        },
      }),
    ],
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
