import { defineStore } from 'pinia'
import axios from 'axios'

// MCP 服务器类型定义
export interface MCPServer {
  id: number
  name: string
  url: string
  transport: string
  description?: string
  config?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface MCPServerCreate {
  name: string
  url: string
  transport: string
  description?: string
  config?: Record<string, any>
}

export interface MCPServerUpdate {
  name?: string
  url?: string
  transport?: string
  description?: string
  config?: Record<string, any>
}

export interface Tool {
  name: string
  description: string
  args_schema?: Record<string, any>
}

export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
}

// 配置axios
const api = axios.create({
  baseURL: '/api/v1/mcp',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('MCP API请求:', config.method?.toUpperCase(), config.url, config.data)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('MCP API响应:', response.config.url, response.data)
    return response
  },
  (error) => {
    console.error('MCP API错误:', error)
    if (error.response) {
      console.error('错误详情:', error.response.data)
    }
    return Promise.reject(error)
  }
)

export const useMCPStore = defineStore('mcp', {
  state: () => ({
    servers: [] as MCPServer[],
    currentServer: null as MCPServer | null,
    tools: [] as Tool[],
    loading: false,
    error: null as string | null
  }),

  getters: {
    getServerById: (state) => (id: number) => {
      return state.servers.find(s => s.id === id)
    }
  },

  actions: {
    // 获取所有服务器
    async fetchServers(): Promise<MCPServer[]> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<any>('/servers')
        this.servers = response.data.servers || []
        return this.servers
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '获取服务器列表失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个服务器
    async fetchServer(id: number): Promise<MCPServer> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<MCPServer>(`/servers/${id}`)
        this.currentServer = response.data
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '获取服务器详情失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建服务器
    async createServer(data: MCPServerCreate): Promise<MCPServer> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.post<MCPServer>('/servers', data)
        await this.fetchServers() // 刷新列表
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '创建服务器失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 更新服务器
    async updateServer(id: number, data: MCPServerUpdate): Promise<MCPServer> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.put<MCPServer>(`/servers/${id}`, data)
        await this.fetchServers() // 刷新列表
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '更新服务器失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 删除服务器
    async deleteServer(id: number): Promise<void> {
      try {
        this.loading = true
        this.error = null
        
        await api.delete(`/servers/${id}`)
        await this.fetchServers() // 刷新列表
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '删除服务器失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取工具列表
    async fetchTools(serverId: number): Promise<Tool[]> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<any>(`/${serverId}/tools`)
        this.tools = response.data.tools || []
        return this.tools
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '获取工具列表失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 调用工具
    async callTool(serverId: number, toolName: string, arguments_: Record<string, any>): Promise<any> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.post<any>(`/${serverId}/tools/call`, {
          tool_name: toolName,
          arguments: arguments_
        })
        return response.data.result
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '调用工具失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 清除错误
    clearError() {
      this.error = null
    }
  }
})
