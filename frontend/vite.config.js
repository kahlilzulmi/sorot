import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
	plugins: [vue(), tailwindcss()],
  root: '.',
  server: {
	port: 5173,
	strictPort: true,
	proxy: {
	  '/api': 'http://127.0.0.1:5000',
	  '/socket.io': {
		target: 'http://127.0.0.1:5000',
		ws: true
	  },
	  '/upload': 'http://127.0.0.1:5000',
	  '/downloaded': 'http://127.0.0.1:5000'
	}
  },
  resolve: {
	alias: {
	  // Needed when Vue templates are compiled at runtime from DOM/template files
	  vue: 'vue/dist/vue.esm-bundler.js'
	}
  },
  build: {
	outDir: path.resolve(__dirname, '../static/dist'),
	emptyOutDir: true,
	manifest: true,
	rollupOptions: {
	  input: {
		app: path.resolve(__dirname, 'src/main.ts')
	  }
	}
  }
})