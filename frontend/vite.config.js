import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  base: '/OpenAdjust/',   // exakt der GitHub-Repo-Name (Groß/Klein beachten!)
  plugins: [vue()],
})
