declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'd3' {
  export * from 'd3'
}

// 环境变量类型声明
interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_API_BASE_URL: string
  readonly VITE_APP_NEO4J_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}