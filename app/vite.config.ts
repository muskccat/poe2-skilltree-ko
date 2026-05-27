import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages 프로젝트 사이트: /poe2-skilltree-ko/
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/poe2-skilltree-ko/" : "/",
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
}));
