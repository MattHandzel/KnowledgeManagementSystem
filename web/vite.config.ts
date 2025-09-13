import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:7123",
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Backend server not ready yet, waiting for it to start...');
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log(`Proxying ${req.method} ${req.url} to backend`);
          });
        }
      },
      "/ws": {
        target: "ws://localhost:7123",
        ws: true,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err) => {
            console.log('WebSocket backend not ready yet, waiting for it to start...');
          });
        }
      },
    },
  },
});
