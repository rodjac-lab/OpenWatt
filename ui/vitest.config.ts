import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "happy-dom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html", "lcov"],
      exclude: [
        "node_modules/",
        "vitest.setup.ts",
        "vitest.config.ts",
        "**/*.config.*",
        "**/*/types.ts",
        "**/__tests__/**",
        "**/*.test.*",
        ".next/",
        "app/**/*",  // Exclude Next.js app directory (layout, page files)
        "lib/**/*",  // Exclude OpenAPI types and other generated files
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
});
