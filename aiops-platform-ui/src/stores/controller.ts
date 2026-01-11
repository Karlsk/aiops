import { defineStore } from 'pinia'
import axios from 'axios'

// 控制器类型定义
export interface SDNController {
  id: number
  name: string
  type: string
  host: string
  port: number
  username?: string
  status: string
  config?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ControllerCreate {
  name: string
  type: string
  host: string
  port: number
  username?: string
  password?: string
  api_token?: string
  config?: Record<string, any>
}

export interface ControllerUpdate {
  name?: string
  host?: string
  port?: number
  username?: string
  password?: string
  api_token?: string
  config?: Record<string, any>
  status?: string
}

export interface TopologySnapshot {
  id: number
  controller_id: number
  database_name: string
  snapshot_time: string
  node_count: number
  link_count: number
  description?: string
  metadata?: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface ApiResponse<T = any> {
  status: string
  message?: string
  data?: T
}

export interface TopologySnapshotsResponse {
  snapshots: TopologySnapshot[]
  total: number
}

// 配置axios
const api = axios.create({
  baseURL: '/api/v1/sdn',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('SDN API请求:', config.method?.toUpperCase(), config.url, config.data)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('SDN API响应:', response.config.url, response.data)
    return response
  },
  (error) => {
    console.error('SDN API错误:', error)
    if (error.response) {
      console.error('错误详情:', error.response.data)
    }
    return Promise.reject(error)
  }
)

export const useControllerStore = defineStore('controller', {
  state: () => ({
    controllers: [] as SDNController[],
    currentController: null as SDNController | null,
    snapshots: [] as TopologySnapshot[],
    loading: false,
    error: null as string | null
  }),

  getters: {
    getControllerById: (state) => (id: number) => {
      return state.controllers.find(c => c.id === id)
    },
    
    activeControllers: (state) => {
      return state.controllers.filter(c => c.status === 'active')
    },
    
    controllersByType: (state) => (type: string) => {
      return state.controllers.filter(c => c.type === type)
    }
  },

  actions: {
    // 获取所有控制器
    async fetchControllers(): Promise<SDNController[]> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<SDNController[]>('/controllers')
        this.controllers = response.data || []
        return this.controllers
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '获取控制器列表失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个控制器
    async fetchController(id: number): Promise<SDNController> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<SDNController>(`/controllers/${id}`)
        this.currentController = response.data
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '获取控制器详情失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建控制器
    async createController(data: ControllerCreate): Promise<SDNController> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.post<SDNController>('/controllers', data)
        await this.fetchControllers() // 刷新列表
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '创建控制器失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 更新控制器
    async updateController(id: number, data: ControllerUpdate): Promise<SDNController> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.put<SDNController>(`/controllers/${id}`, data)
        await this.fetchControllers() // 刷新列表
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '更新控制器失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 删除控制器
    async deleteController(id: number): Promise<void> {
      try {
        this.loading = true
        this.error = null
        
        await api.delete(`/controllers/${id}`)
        await this.fetchControllers() // 刷新列表
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '删除控制器失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 测试控制器连接
    async testConnection(id: number): Promise<any> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.post<ApiResponse>(`/controllers/${id}/test`)
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '测试连接失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取拓扑
    async getTopology(id: number): Promise<any> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<ApiResponse>(`/controllers/${id}/topology`)
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '获取拓扑失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 同步快照
    async syncSnapshot(id: number): Promise<TopologySnapshot> {
      try {
        this.loading = true
        this.error = null
        
        // 使用后端实际的API路径
        const response = await api.get<ApiResponse>(`/controllers/${id}/sync_topology`)
        
        // 同步成功后，可能需要手动刷新快照列表
        if (response.data.status === 'success') {
          await this.fetchSnapshots(id)
          // 返回最新的快照（假设是列表中的第一个）
          if (this.snapshots.length > 0) {
            return this.snapshots[0]
          }
        }
        
        throw new Error('同步快照失败')
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '同步快照失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取快照列表
    async fetchSnapshots(controllerId: number): Promise<TopologySnapshot[]> {
      try {
        this.loading = true
        this.error = null
        
        // 使用后端实际的API路径，带controller_id参数过滤
        const response = await api.get<TopologySnapshotsResponse>(`/snapshots?controller_id=${controllerId}`)
        
        // 处理响应数据
        if (response.data && response.data.snapshots) {
          this.snapshots = response.data.snapshots || []
        } else if (Array.isArray(response.data)) {
          // 兼容直接返回数组的情况
          this.snapshots = response.data
        } else {
          this.snapshots = []
        }
        
        return this.snapshots
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '获取快照列表失败'
        this.snapshots = []
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个快照
    async fetchSnapshot(controllerId: number, snapshotId: number): Promise<TopologySnapshot> {
      try {
        this.loading = true
        this.error = null
        
        // 使用后端实际的API路径
        const response = await api.get<TopologySnapshot>(`/snapshots/${snapshotId}`)
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '获取快照详情失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 删除快照
    async deleteSnapshot(controllerId: number, snapshotId: number): Promise<void> {
      try {
        this.loading = true
        this.error = null
        
        // 使用后端实际的API路径
        await api.delete(`/snapshots/${snapshotId}`)
        await this.fetchSnapshots(controllerId) // 刷新快照列表
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '删除快照失败'
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
