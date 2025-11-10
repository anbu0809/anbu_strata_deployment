// vite.config.ts
import { defineConfig } from "file:///C:/Users/Localuser/Desktop/finalsStrata/anbu_strata_deployment/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/Localuser/Desktop/finalsStrata/anbu_strata_deployment/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
var vite_config_default = defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    //local
    // host: '0.0.0.0', server
    port: 3e3,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        //local
        //target: 'http://34.41.49.200:8000', server
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: "dist",
    assetsDir: "assets"
  },
  appType: "spa"
  // Set the app type to single page application
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJjOlxcXFxVc2Vyc1xcXFxMb2NhbHVzZXJcXFxcRGVza3RvcFxcXFxmaW5hbHNTdHJhdGFcXFxcYW5idV9zdHJhdGFfZGVwbG95bWVudFxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiYzpcXFxcVXNlcnNcXFxcTG9jYWx1c2VyXFxcXERlc2t0b3BcXFxcZmluYWxzU3RyYXRhXFxcXGFuYnVfc3RyYXRhX2RlcGxveW1lbnRcXFxcZnJvbnRlbmRcXFxcdml0ZS5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL2M6L1VzZXJzL0xvY2FsdXNlci9EZXNrdG9wL2ZpbmFsc1N0cmF0YS9hbmJ1X3N0cmF0YV9kZXBsb3ltZW50L2Zyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcclxuaW1wb3J0IHJlYWN0IGZyb20gJ0B2aXRlanMvcGx1Z2luLXJlYWN0J1xyXG5cclxuLy8gaHR0cHM6Ly92aXRlanMuZGV2L2NvbmZpZy9cclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcclxuICBwbHVnaW5zOiBbcmVhY3QoKV0sXHJcbiAgc2VydmVyOiB7XHJcbiAgICBob3N0OiAnMTI3LjAuMC4xJywvL2xvY2FsXHJcbiAgIC8vIGhvc3Q6ICcwLjAuMC4wJywgc2VydmVyXHJcbiAgICBwb3J0OiAzMDAwLFxyXG4gICAgcHJveHk6IHtcclxuICAgICAgJy9hcGknOiB7XHJcbiAgICAgICAgdGFyZ2V0OiAnaHR0cDovLzEyNy4wLjAuMTo4MDAwJywvL2xvY2FsXHJcbiAgICAgICAgLy90YXJnZXQ6ICdodHRwOi8vMzQuNDEuNDkuMjAwOjgwMDAnLCBzZXJ2ZXJcclxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXHJcbiAgICAgICAgc2VjdXJlOiBmYWxzZSxcclxuICAgICAgfVxyXG4gICAgfVxyXG4gIH0sXHJcbiAgYnVpbGQ6IHtcclxuICAgIG91dERpcjogJ2Rpc3QnLFxyXG4gICAgYXNzZXRzRGlyOiAnYXNzZXRzJyxcclxuICB9LFxyXG4gIGFwcFR5cGU6ICdzcGEnLCAvLyBTZXQgdGhlIGFwcCB0eXBlIHRvIHNpbmdsZSBwYWdlIGFwcGxpY2F0aW9uXHJcbn0pIl0sCiAgIm1hcHBpbmdzIjogIjtBQUFxWixTQUFTLG9CQUFvQjtBQUNsYixPQUFPLFdBQVc7QUFHbEIsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDMUIsU0FBUyxDQUFDLE1BQU0sQ0FBQztBQUFBLEVBQ2pCLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQTtBQUFBO0FBQUEsSUFFTixNQUFNO0FBQUEsSUFDTixPQUFPO0FBQUEsTUFDTCxRQUFRO0FBQUEsUUFDTixRQUFRO0FBQUE7QUFBQTtBQUFBLFFBRVIsY0FBYztBQUFBLFFBQ2QsUUFBUTtBQUFBLE1BQ1Y7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUFBLEVBQ0EsT0FBTztBQUFBLElBQ0wsUUFBUTtBQUFBLElBQ1IsV0FBVztBQUFBLEVBQ2I7QUFBQSxFQUNBLFNBQVM7QUFBQTtBQUNYLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
