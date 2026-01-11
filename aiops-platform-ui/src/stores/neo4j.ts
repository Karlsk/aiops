import { defineStore } from 'pinia'
import axios from 'axios'

// API接口类型定义
export interface NodeInfo {
  name: string
  label: string
}

export interface NodeCreate {
  name: string
  label: string
  properties?: Record<string, any>
}

export interface RelationshipCreate {
  from_node: NodeInfo
  to_node: NodeInfo
  relationship_type: string
  relationship_properties?: Record<string, any>
}

export interface RelationshipInfo {
  from_node: NodeInfo
  to_node: NodeInfo
  relationship_type: string
  relationship_properties?: Record<string, any>
}

export interface ApiResponse<T = any> {
  status: string
  message?: string
  data?: T
}

export interface DatabaseInfo {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
}

export interface DatabaseCreate {
  name: string
  description?: string
}

// 配置axios默认设置
const api = axios.create({
  baseURL: '/api/v1/graph/database',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API请求:', config.method?.toUpperCase(), config.url, config.data)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API响应:', response.config.url, response.data)
    return response
  },
  (error) => {
    console.error('API错误:', error)
    if (error.response) {
      console.error('错误详情:', error.response.data)
    }
    return Promise.reject(error)
  }
)

export const useNeo4jStore = defineStore('neo4j', {
  state: () => ({
    labels: [] as string[],
    relationshipTypes: [] as string[],
    nodes: [] as NodeCreate[],
    relationships: [] as RelationshipInfo[],
    databases: [] as DatabaseInfo[],
    currentDatabase: 'default' as string, // 默认使用 'default' 画布
    loading: false,
    error: null as string | null
  }),

  actions: {
    // 获取所有节点标签
    async getLabels(): Promise<string[]> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<{ labels: string[] }>('/labels')
        this.labels = response.data.labels || []
        return this.labels
      } catch (error: any) {
        this.error = error.message || '获取标签失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取所有关系类型
    async getRelationshipTypes(): Promise<string[]> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<{ relationship_types: string[] }>('/relationship-types')
        this.relationshipTypes = response.data.relationship_types || []
        return this.relationshipTypes
      } catch (error: any) {
        this.error = error.message || '获取关系类型失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取所有节点
    async getAllNodes(label?: string, limit: number = 100): Promise<NodeCreate[]> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        if (label) params.append('label', label)
        params.append('limit', limit.toString())
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await api.get<ApiResponse<NodeCreate[]>>(`/nodes?${params.toString()}`)
        
        if (response.data.status === 'success' && response.data.data) {
          this.nodes = response.data.data
          return this.nodes
        } else {
          throw new Error(response.data.message || '获取节点失败')
        }
      } catch (error: any) {
        this.error = error.message || '获取节点失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取所有关系
    async getAllRelationships(
      relationshipType?: string,
      fromLabel?: string,
      toLabel?: string,
      limit: number = 100
    ): Promise<RelationshipInfo[]> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        if (relationshipType) params.append('relationship_type', relationshipType)
        if (fromLabel) params.append('from_label', fromLabel)
        if (toLabel) params.append('to_label', toLabel)
        params.append('limit', limit.toString())
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await api.get<ApiResponse<RelationshipInfo[]>>(`/relationships?${params.toString()}`)
        
        if (response.data.status === 'success' && response.data.data) {
          this.relationships = response.data.data
          return this.relationships
        } else {
          throw new Error(response.data.message || '获取关系失败')
        }
      } catch (error: any) {
        this.error = error.message || '获取关系失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 通过label和name获取单个节点
    async getNodeByLabelAndName(label: string, name: string): Promise<NodeCreate> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<ApiResponse<NodeCreate>>(`/nodes/${encodeURIComponent(label)}/${encodeURIComponent(name)}`)
        
        if (response.data.status === 'success' && response.data.data) {
          return response.data.data
        } else {
          throw new Error(response.data.message || '获取节点失败')
        }
      } catch (error: any) {
        this.error = error.message || '获取节点失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建节点
    async createNode(nodeData: NodeCreate): Promise<NodeCreate> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await api.post<ApiResponse<NodeCreate>>(`/nodes?${params.toString()}`, nodeData)
        
        if (response.data.status === 'success') {
          // 刷新节点列表
          await this.getAllNodes()
          return response.data.data!
        } else {
          throw new Error(response.data.message || '创建节点失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '创建节点失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 删除节点
    async deleteNode(nodeInfo: NodeInfo): Promise<void> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await api.delete<ApiResponse>(`/nodes?${params.toString()}`, { data: nodeInfo })
        
        if (response.data.status === 'success') {
          // 刷新节点列表
          await this.getAllNodes()
        } else {
          throw new Error(response.data.message || '删除节点失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '删除节点失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建关系
    async createRelationship(relationshipData: RelationshipCreate): Promise<RelationshipInfo> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await api.post<ApiResponse<RelationshipInfo>>(`/relationships?${params.toString()}`, relationshipData)
        
        if (response.data.status === 'success') {
          // 刷新关系列表
          await this.getAllRelationships()
          return response.data.data!
        } else {
          throw new Error(response.data.message || '创建关系失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '创建关系失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 删除关系
    async deleteRelationship(relationshipData: {
      from_node: NodeInfo
      to_node: NodeInfo
      relationship_type: string
    }): Promise<void> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await api.delete<ApiResponse>(`/relationships?${params.toString()}`, { data: relationshipData })
        
        if (response.data.status === 'success') {
          // 刷新关系列表
          await this.getAllRelationships()
        } else {
          throw new Error(response.data.message || '删除关系失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '删除关系失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 通过 relationship ID 精确删除关系
    async deleteRelationshipById(relationshipId: string): Promise<void> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.delete<ApiResponse>('/relationships/by-id', { 
          data: { relationship_id: relationshipId }
        })
        
        if (response.data.status === 'success') {
          // 刷新关系列表
          await this.getAllRelationships()
        } else {
          throw new Error(response.data.message || '删除关系失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '删除关系失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 条件查询关系
    async queryRelationships(query: {
      from_node?: NodeInfo
      to_node?: NodeInfo
      relationship_type: string
    }): Promise<RelationshipInfo[]> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.post<ApiResponse<RelationshipInfo[]>>('/relationships/query', query)
        
        if (response.data.status === 'success' && response.data.data) {
          return response.data.data
        } else {
          throw new Error(response.data.message || '查询关系失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '查询关系失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取所有节点位置（按画布隔离）
    async getAllNodePositions(): Promise<Record<string, { x: number; y: number }>> {
      try {
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await axios.get<ApiResponse<Record<string, { x: number; y: number }>>>(`/api/v1/graph/positions?${params.toString()}`)
        
        if (response.data.status === 'success' && response.data.data) {
          return response.data.data
        } else {
          return {}
        }
      } catch (error: any) {
        console.error('获取节点位置失败:', error)
        return {}
      }
    },

    // 批量保存节点位置（按画布隔离）
    async saveAllNodePositions(positions: Record<string, { x: number; y: number }>): Promise<void> {
      try {
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await axios.post<ApiResponse>(`/api/v1/graph/positions?${params.toString()}`, { positions })
        
        if (response.data.status !== 'success') {
          throw new Error(response.data.message || '保存节点位置失败')
        }
      } catch (error: any) {
        console.error('保存节点位置失败:', error)
        throw error
      }
    },

    // 更新单个节点位置（按画布隔离）- 推荐在拖拽时使用此方法
    async updateNodePosition(node_id: string, x: number, y: number): Promise<void> {
      try {
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await axios.put<ApiResponse>(`/api/v1/graph/positions/${encodeURIComponent(node_id)}?${params.toString()}`, {
          node_id,
          x,
          y
        })
        
        if (response.data.status !== 'success') {
          throw new Error(response.data.message || '更新节点位置失败')
        }
      } catch (error: any) {
        console.error('更新节点位置失败:', error)
        throw error
      }
    },

    // 清空所有节点位置（按画布隔离）
    async clearAllNodePositions(): Promise<void> {
      try {
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await axios.delete<ApiResponse>(`/api/v1/graph/positions?${params.toString()}`)
        
        if (response.data.status !== 'success') {
          throw new Error(response.data.message || '清空节点位置失败')
        }
      } catch (error: any) {
        console.error('清空节点位置失败:', error)
        throw error
      }
    },

    // 清除错误状态
    clearError() {
      this.error = null
    },

    // 将Neo4j图转换为Mermaid流程图
    async convertToMermaid(name: string): Promise<{
      mermaid: string
      stats: {
        paths_count: number
        nodes_count: number
        edges_count: number
      }
    }> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        params.append('name', name)
        const database = this.currentDatabase || 'default'
        params.append('database', database)
        console.log('[convertToMermaid] Calling API with params:', { name, database })
        
        const response = await api.get<ApiResponse<{
          mermaid: string
          stats: {
            paths_count: number
            nodes_count: number
            edges_count: number
          }
        }>>(`/mermaid?${params.toString()}`)
        
        if (response.data.status === 'success' && response.data.data) {
          return response.data.data
        } else {
          throw new Error(response.data.message || '转换Mermaid失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '转换Mermaid失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 更新节点
    async updateNode(nodeData: NodeCreate): Promise<NodeCreate> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await api.put<ApiResponse<NodeCreate>>(`/nodes?${params.toString()}`, nodeData)
        
        if (response.data.status === 'success') {
          // 刷新节点列表
          await this.getAllNodes()
          return response.data.data!
        } else {
          throw new Error(response.data.message || '更新节点失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '更新节点失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 更新关系
    async updateRelationship(relationshipData: RelationshipCreate): Promise<RelationshipInfo> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        if (this.currentDatabase) params.append('database', this.currentDatabase)
        
        const response = await api.put<ApiResponse<RelationshipInfo>>(`/relationships?${params.toString()}`, relationshipData)
        
        if (response.data.status === 'success') {
          // 刷新关系列表
          await this.getAllRelationships()
          return response.data.data!
        } else {
          throw new Error(response.data.message || '更新关系失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '更新关系失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 将Neo4j图转换为JSON格式（结构化Plan Schema）
    async convertToJson(name: string): Promise<{
      id: string
      nodes: Record<string, any>
      edges: Array<{
        from: string
        to: string
        condition?: string
      }>
      start: string
      stats: {
        nodes_count: number
        edges_count: number
      }
    }> {
      try {
        this.loading = true
        this.error = null
        
        const params = new URLSearchParams()
        params.append('name', name)
        const database = this.currentDatabase || 'default'
        params.append('database', database)
        console.log('[convertToJson] Calling API with params:', { name, database })
        
        const response = await api.get<ApiResponse<{
          id: string
          nodes: Record<string, any>
          edges: Array<{
            from: string
            to: string
            condition?: string
          }>
          start: string
          stats: {
            nodes_count: number
            edges_count: number
          }
        }>>(`/json?${params.toString()}`)
        
        if (response.data.status === 'success' && response.data.data) {
          return response.data.data
        } else {
          throw new Error(response.data.message || '转换JSON失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '转换JSON失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // ==================== Database 管理方法 ====================

    // 获取所有数据库
    async getDatabases(): Promise<DatabaseInfo[]> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.get<ApiResponse<DatabaseInfo[]>>('/databases')
        
        if (response.data.status === 'success' && response.data.data) {
          this.databases = response.data.data
          return this.databases
        } else {
          throw new Error(response.data.message || '获取数据库列表失败')
        }
      } catch (error: any) {
        this.error = error.message || '获取数据库列表失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建数据库
    async createDatabase(databaseData: DatabaseCreate): Promise<DatabaseInfo> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.post<ApiResponse<DatabaseInfo>>('/databases', databaseData)
        
        if (response.data.status === 'success' && response.data.data) {
          // 刷新数据库列表
          await this.getDatabases()
          return response.data.data
        } else {
          throw new Error(response.data.message || '创建数据库失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '创建数据库失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 删除数据库
    async deleteDatabase(name: string): Promise<void> {
      try {
        this.loading = true
        this.error = null
        
        const response = await api.delete<ApiResponse>(`/databases/${encodeURIComponent(name)}`)
        
        if (response.data.status === 'success') {
          // 如果删除的是当前数据库，切换到 default
          if (this.currentDatabase === name) {
            this.currentDatabase = 'default'
          }
          // 刷新数据库列表
          await this.getDatabases()
        } else {
          throw new Error(response.data.message || '删除数据库失败')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || error.message || '删除数据库失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 切换当前数据库
    switchDatabase(databaseName: string) {
      this.currentDatabase = databaseName || 'default'
    }
  }
})