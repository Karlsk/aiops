import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: {
      title: '主页'
    }
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: () => import('@/views/KnowledgeGraph.vue'),
    meta: {
      title: '排障知识图谱'
    }
  },
  {
    path: '/controllers',
    name: 'ControllerList',
    component: () => import('@/views/ControllerList.vue'),
    meta: {
      title: 'SDN控制器管理'
    }
  },
  {
    path: '/controllers/:id',
    name: 'ControllerDetail',
    component: () => import('@/views/ControllerDetail.vue'),
    meta: {
      title: '控制器详情'
    }
  },
  {
    path: '/mcp',
    name: 'MCPList',
    component: () => import('@/views/MCPList.vue'),
    meta: {
      title: 'MCP 服务器管理'
    }
  },
  {
    path: '/mcp/:id',
    name: 'MCPDetail',
    component: () => import('@/views/MCPDetail.vue'),
    meta: {
      title: 'MCP 服务器详情'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - AIOps 网络运维平台`
  }
  next()
})

export default router