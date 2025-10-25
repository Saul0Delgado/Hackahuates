import path from "path" // <-- ¡Asegúrate de importar 'path'!
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"), // <-- Esta sección es la clave
    },
  },
})