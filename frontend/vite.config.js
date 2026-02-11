import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";

// 憑證檔案名稱 (已根據實體檔案更正)
const certPath = path.resolve(__dirname, "192.168.90.168.pem");
const keyPath = path.resolve(__dirname, "192.168.90.168-key.pem");

const httpsConfig = fs.existsSync(certPath) && fs.existsSync(keyPath)
  ? {
    key: fs.readFileSync(keyPath),
    cert: fs.readFileSync(certPath),
  }
  : undefined;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5194,
    host: true, // 允許透過 IP 存取
    https: httpsConfig,
  },
  build: {
    sourcemap: true
  }
});
