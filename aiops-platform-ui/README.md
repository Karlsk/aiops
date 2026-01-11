# AIOps 网络运维平台 - 前端

基于 Vue3 + TypeScript + Element Plus 的网络运维管理平台前端项目。

## 功能特性

- 🏠 **主页** - 展示系统概览和统计信息
- 🕸️ **排障知识图谱** - 可视化的Neo4j图数据库操作界面
- 🎯 **拖拽式操作** - 支持节点和关系的可视化创建
- 📊 **实时数据** - 与后端Neo4j API实时交互
- 🎨 **现代化UI** - 基于Element Plus的美观界面

## 技术栈

- **Vue 3** - 前端框架
- **TypeScript** - 类型安全
- **Element Plus** - UI组件库
- **Vue Router** - 路由管理
- **Pinia** - 状态管理
- **D3.js** - 图形可视化
- **Axios** - HTTP客户端
- **Vite** - 构建工具

## 项目结构

```
src/
├── components/          # 公共组件
├── views/              # 页面组件
│   ├── Home.vue        # 主页
│   └── KnowledgeGraph.vue # 知识图谱页面
├── stores/             # Pinia状态管理
│   └── neo4j.ts        # Neo4j数据管理
├── router/             # 路由配置
│   └── index.ts
├── style.css           # 全局样式
├── App.vue            # 根组件
└── main.ts            # 应用入口
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

项目将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
```

### 类型检查

```bash
npm run type-check
```

## 功能说明

### 主页 (Home)

- 显示系统统计信息（节点数、关系数、故障案例等）
- 快速导航到知识图谱页面
- 系统状态概览
- 最近活动记录

### 排障知识图谱 (Knowledge Graph)

#### 核心功能

1. **节点管理**
   - 创建节点：支持自定义name、label和properties
   - 标签下拉选择：可选择已存在的标签或输入新标签
   - 属性管理：动态添加/删除键值对属性
   - 可视化显示：不同标签用不同颜色区分

2. **关系管理**
   - 创建关系：连接两个节点
   - 节点选择：根据标签筛选可用节点
   - 关系类型：支持下拉选择或新建
   - 关系属性：自定义关系的属性信息

3. **图谱交互**
   - 拖拽移动：支持节点拖拽
   - 缩放平移：鼠标滚轮缩放，拖拽平移
   - 适应屏幕：一键调整视图适应画布
   - 实时更新：操作后自动刷新图谱

#### 操作流程

1. **创建节点**
   - 点击"创建节点"按钮
   - 填写节点名称（必填）
   - 选择或输入节点标签（必填）
   - 可选：添加自定义属性
   - 点击创建，节点将出现在图谱中

2. **创建关系**
   - 点击"创建关系"按钮
   - 选择起始节点（标签+名称）
   - 选择目标节点（标签+名称）
   - 选择或输入关系类型（必填）
   - 可选：添加关系属性
   - 点击创建，关系线将出现在图谱中

## API集成

项目通过Pinia Store与后端Neo4j API集成：

### 主要接口

- `GET /api/v1/graph/database/labels` - 获取所有节点标签
- `GET /api/v1/graph/database/relationship-types` - 获取所有关系类型
- `GET /api/v1/graph/database/nodes` - 获取所有节点
- `GET /api/v1/graph/database/relationships` - 获取所有关系
- `POST /api/v1/graph/database/nodes` - 创建节点
- `POST /api/v1/neograph/database4j/relationships` - 创建关系

### 数据格式

#### 节点创建
```json
{
  "name": "服务器-001",
  "label": "Server",
  "properties": {
    "ip": "192.168.1.10",
    "status": "running"
  }
}
```

#### 关系创建
```json
{
  "from_node": {
    "name": "服务器-001",
    "label": "Server"
  },
  "to_node": {
    "name": "数据库-001",
    "label": "Database"
  },
  "relationship_type": "CONNECTS_TO",
  "relationship_properties": {
    "port": "3306",
    "protocol": "TCP"
  }
}
```

## 浏览器支持

- Chrome ≥ 87
- Firefox ≥ 78
- Safari ≥ 14
- Edge ≥ 88

## 开发注意事项

1. **代理配置**：开发环境下API请求通过Vite代理转发到后端服务器
2. **类型安全**：使用TypeScript确保类型安全，所有API接口都有对应的类型定义
3. **状态管理**：使用Pinia管理全局状态，包括Neo4j数据的缓存和更新
4. **错误处理**：完善的错误处理机制，用户操作失败时会显示相应的错误信息

## 许可证

MIT License