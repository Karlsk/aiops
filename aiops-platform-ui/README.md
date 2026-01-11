# AIOps Platform UI

Terra AIOps 网络运维平台的前端应用，基于 Vue 3 + TypeScript + Element Plus 构建，提供直观的网络运维管理界面。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **UI 组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **数据可视化**: D3.js
- **构建工具**: Vite
- **HTTP 客户端**: Axios
- **工具库**: Lodash-es

## 功能特性

### 1. SDN 控制器管理
- 控制器列表展示
- 添加/编辑/删除控制器配置
- 控制器连接状态监控
- 网络拓扑可视化
- 拓扑快照管理
- 实时监控数据展示
- 日志查询

### 2. 知识图谱
- 网络拓扑知识图谱可视化
- 基于 D3.js 的交互式图谱展示
- 节点和边关系展示
- 图谱布局和缩放
- 节点详情查看

### 3. MCP 服务器管理
- MCP 服务器配置管理
- 服务器列表和状态监控
- 工具列表查看
- 工具调用测试
- 服务器连接测试

### 4. 响应式设计
- 适配桌面端和大屏展示
- 自适应布局
- 优雅的交互体验

## 项目结构

```
aiops-platform-ui/
├── src/
│   ├── router/
│   │   └── index.ts           # 路由配置
│   ├── stores/
│   │   ├── controller.ts      # SDN控制器状态管理
│   │   ├── mcp.ts             # MCP服务器状态管理
│   │   └── neo4j.ts           # Neo4j图数据库状态管理
│   ├── views/
│   │   ├── Home.vue           # 主页
│   │   ├── KnowledgeGraph.vue # 知识图谱页面
│   │   ├── ControllerList.vue # 控制器列表页面
│   │   ├── ControllerDetail.vue # 控制器详情页面
│   │   ├── MCPList.vue        # MCP服务器列表页面
│   │   └── MCPDetail.vue      # MCP服务器详情页面
│   ├── App.vue                # 根组件
│   ├── main.ts                # 应用入口
│   ├── style.css              # 全局样式
│   └── vite-env.d.ts          # TypeScript类型声明
├── .env.development           # 开发环境配置
├── .env.production            # 生产环境配置
├── index.html                 # HTML入口文件
├── package.json               # 项目依赖配置
├── tsconfig.json              # TypeScript配置
├── vite.config.ts             # Vite配置
├── auto-imports.d.ts          # 自动导入类型声明
└── components.d.ts            # 组件类型声明
```

## 快速开始

### 环境要求

- Node.js >= 18
- npm >= 9 或 pnpm >= 8

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 pnpm (推荐)
pnpm install
```

### 开发环境配置

编辑 `.env.development` 文件，配置后端 API 地址：

```env
# 应用标题
VITE_APP_TITLE=AIOps 网络运维平台

# 后端 API 地址
VITE_APP_API_BASE_URL=http://localhost:7082

# Neo4j API 地址
VITE_APP_NEO4J_API_BASE_URL=http://localhost:7082/api/v1/graph/database
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
# 类型检查
npm run type-check

# 构建
npm run build
```

构建产物将输出到 `dist/` 目录。

### 预览生产版本

```bash
npm run preview
```

## 开发指南

### 项目配置

#### Vite 配置

[vite.config.ts](file:///Users/gaorj/PycharmProjects/Tethrnet/terra-aiops/aiops-platform-ui/vite.config.ts) 中配置了：

- Vue 3 支持
- Element Plus 自动导入
- Vue/Vue Router/Pinia API 自动导入
- TypeScript 路径别名 `@` -> `src/`
- 开发服务器端口：3000
- API 代理：`/api` -> `http://localhost:7082`

#### TypeScript 配置

- 严格模式开启
- 路径别名支持
- Vue 3 类型支持
- 自动导入类型声明

### 添加新页面

1. 在 `src/views/` 中创建 Vue 组件
2. 在 `src/router/index.ts` 中添加路由配置
3. 如需状态管理，在 `src/stores/` 中创建 Pinia store

示例路由配置：

```typescript
{
  path: '/new-page',
  name: 'NewPage',
  component: () => import('@/views/NewPage.vue'),
  meta: {
    title: '新页面'
  }
}
```

### 状态管理

使用 Pinia 进行状态管理，stores 示例：

```typescript
import { defineStore } from 'pinia'

export const useMyStore = defineStore('myStore', {
  state: () => ({
    data: []
  }),
  actions: {
    async fetchData() {
      // 实现数据获取逻辑
    }
  }
})
```

### API 调用

使用 Axios 进行 HTTP 请求：

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL
})

// GET 请求
const data = await api.get('/api/v1/endpoint')

// POST 请求
const result = await api.post('/api/v1/endpoint', payload)
```

### 组件自动导入

项目配置了自动导入功能：

- **Vue API**: `ref`, `computed`, `onMounted` 等无需手动导入
- **Vue Router**: `useRouter`, `useRoute` 自动可用
- **Pinia**: `defineStore`, `storeToRefs` 自动可用
- **Element Plus**: 所有组件和图标按需自动导入

### 样式开发

- 全局样式在 `src/style.css` 中定义
- 组件样式使用 `<style scoped>` 避免污染
- 支持 Element Plus 主题定制

## 目录说明

### `/src/views`

页面组件目录，每个页面对应一个独立的 Vue 组件。

- **Home.vue**: 平台主页，展示概览信息
- **KnowledgeGraph.vue**: 知识图谱可视化页面，使用 D3.js 渲染
- **ControllerList.vue**: SDN 控制器列表管理页面
- **ControllerDetail.vue**: 控制器详情页，包含拓扑、监控、日志等
- **MCPList.vue**: MCP 服务器列表管理页面
- **MCPDetail.vue**: MCP 服务器详情和工具管理页面

### `/src/stores`

Pinia 状态管理 store：

- **controller.ts**: SDN 控制器数据状态管理
- **mcp.ts**: MCP 服务器数据状态管理
- **neo4j.ts**: Neo4j 图数据库连接和查询状态管理

### `/src/router`

Vue Router 路由配置，定义页面路由和导航逻辑。

## 生产部署

### 环境变量配置

编辑 `.env.production` 文件：

```env
VITE_APP_TITLE=AIOps 网络运维平台
VITE_APP_API_BASE_URL=https://your-api-domain.com
VITE_APP_NEO4J_API_BASE_URL=https://your-api-domain.com/api/v1/graph/database
```

### 构建部署

```bash
# 构建生产版本
npm run build

# 将 dist/ 目录部署到静态服务器
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api {
        proxy_pass http://backend:7082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker 部署

```dockerfile
# 构建阶段
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## 浏览器兼容性

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 常见问题

### 1. API 请求失败

检查 `.env.development` 中的 `VITE_APP_API_BASE_URL` 配置是否正确，确保后端服务已启动。

### 2. 组件样式异常

确保 Element Plus 正确安装，检查 `vite.config.ts` 中的自动导入配置。

### 3. 路由跳转 404

确保路由配置正确，检查组件路径是否存在。

### 4. TypeScript 类型错误

运行 `npm run type-check` 检查类型错误，确保 `.d.ts` 文件正确生成。

## 开发规范

- 使用 TypeScript 编写代码，避免使用 `any` 类型
- 组件命名使用 PascalCase
- 文件命名使用 PascalCase (组件) 或 camelCase (工具函数)
- 使用 Composition API 而非 Options API
- 合理拆分组件，保持单一职责
- 使用 ESLint 和 Prettier 保持代码风格一致

## 许可证

[添加许可证信息]

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

[添加联系方式]
