<template>
  <div class="knowledge-graph-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <!-- 画布选择器 -->
      <div class="canvas-selector">
        <el-select
          v-model="currentCanvas"
          placeholder="选择画布"
          style="width: 200px; margin-right: 10px"
          @change="onCanvasChange"
        >
          <el-option
            label="default (默认画布)"
            value="default"
          />
          <el-option
            v-for="db in filteredDatabases"
            :key="db.id"
            :label="db.name"
            :value="db.name"
          >
            <span>{{ db.name }}</span>
            <span v-if="db.description" style="color: #8492a6; font-size: 12px; margin-left: 8px">
              ({{ db.description }})
            </span>
          </el-option>
        </el-select>
        <el-button type="primary" @click="showCreateCanvasDialog = true">
          <el-icon><Plus /></el-icon>
          新建画布
        </el-button>
        <el-button 
          type="danger" 
          @click="confirmDeleteCanvas"
          :disabled="!currentCanvas || currentCanvas === 'default'"
        >
          <el-icon><Delete /></el-icon>
          删除画布
        </el-button>
      </div>
      
      <el-divider direction="vertical" />
      
      <el-button type="primary" @click="showCreateNodeDialog = true">
        <el-icon><Plus /></el-icon>
        创建节点
      </el-button>
      <el-button type="success" @click="showCreateRelationDialog = true">
        <el-icon><Connection /></el-icon>
        创建关系
      </el-button>
      <el-button @click="refreshGraph">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button @click="fitToScreen">
        <el-icon><FullScreen /></el-icon>
        适应屏幕
      </el-button>
      <el-button @click="resetNodePositions">
        <el-icon><Refresh /></el-icon>
        重置位置
      </el-button>
      <el-divider direction="vertical" />
      <el-button type="info" @click="loadGraphData">
        <el-icon><Download /></el-icon>
        加载数据
      </el-button>
    </div>

    <!-- 图谱画布 -->
    <div 
      class="graph-canvas" 
      ref="graphContainer" 
      @click="hideContextMenu"
      @mouseup="handleCanvasMouseUp"
      @contextmenu="handleCanvasContextMenu"
      :class="{ 'link-creation-mode': linkCreationMode }"
    >
      <div v-if="linkCreationMode" class="link-creation-hint">
        <el-icon><Connection /></el-icon>
        <span>拖动到目标节点创建关系 | 按 ESC 取消</span>
      </div>
    </div>

    <!-- 右键上下文菜单 -->
    <div
      v-show="contextMenu.show"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <div v-if="contextMenu.type === 'node'" class="menu-content">
        <div class="menu-header">
          <strong>{{ (contextMenu.data as NodeData)?.name }}</strong>
          <span class="label-tag">{{ (contextMenu.data as NodeData)?.label }}</span>
        </div>
        <el-divider style="margin: 8px 0" />
        <div class="menu-item" @click="showNodeDetailFromContext">
          <el-icon color="#67c23a"><InfoFilled /></el-icon>
          <span>查看详情</span>
        </div>
        <div class="menu-item" @click="updateNodeFromContext">
          <el-icon color="#409eff"><Document /></el-icon>
          <span>更新节点</span>
        </div>
        <div class="menu-item" @click="startLinkCreationFromContext">
          <el-icon color="#409eff"><Connection /></el-icon>
          <span>创建关系</span>
        </div>
        <div 
          v-if="(contextMenu.data as NodeData)?.label === 'Event'"
          class="menu-item" 
          @click="generatePlanFromContext"
        >
          <el-icon color="#409eff"><Document /></el-icon>
          <span>生成Plan (Mermaid)</span>
        </div>
        <div 
          v-if="(contextMenu.data as NodeData)?.label === 'Event'"
          class="menu-item" 
          @click="generateJsonPlanFromContext"
        >
          <el-icon color="#67c23a"><Document /></el-icon>
          <span>生成Plan (JSON)</span>
        </div>
        <div class="menu-item" @click="copyNodeFromContext">
          <el-icon color="#409eff"><DocumentCopy /></el-icon>
          <span>复制节点</span>
        </div>
        <div class="menu-item" @click="deleteNodeFromContext">
          <el-icon color="#f56c6c"><Delete /></el-icon>
          <span>删除节点</span>
        </div>
      </div>
      <div v-else-if="contextMenu.type === 'link'" class="menu-content">
        <div class="menu-header">
          <strong>{{ (contextMenu.data as LinkData)?.type }}</strong>
        </div>
        <el-divider style="margin: 8px 0" />
        <div class="menu-item" @click="updateRelationshipFromContext">
          <el-icon color="#409eff"><Document /></el-icon>
          <span>更新关系</span>
        </div>
        <div class="menu-item" @click="deleteLinkFromContext">
          <el-icon color="#e6a23c"><Close /></el-icon>
          <span>删除关系</span>
        </div>
      </div>
      <div v-else-if="contextMenu.type === 'canvas'" class="menu-content">
        <div class="menu-header">
          <strong>画布操作</strong>
        </div>
        <el-divider style="margin: 8px 0" />
        <div class="menu-item" @click="showCreateNodeDialogFromContext">
          <el-icon color="#409eff"><Plus /></el-icon>
          <span>创建节点</span>
        </div>
      </div>
    </div>

    <!-- 创建画布对话框 -->
    <el-dialog
      v-model="showCreateCanvasDialog"
      title="创建画布"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="canvasFormRef"
        :model="canvasForm"
        :rules="canvasRules"
        label-width="100px"
      >
        <el-form-item label="画布名称" prop="name">
          <el-input 
            v-model="canvasForm.name" 
            placeholder="请输入画布名称（英文或数字）"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="画布描述" prop="description">
          <el-input 
            v-model="canvasForm.description" 
            type="textarea"
            placeholder="请输入画布描述（可选）"
            maxlength="200"
            show-word-limit
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateCanvasDialog = false">取消</el-button>
        <el-button type="primary" @click="createCanvas" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 创建节点对话框 -->
    <el-dialog
      v-model="showCreateNodeDialog"
      :title="updatingNode ? '更新节点' : '创建节点'"
      width="500px"
      :close-on-click-modal="false"
      @close="resetNodeForm"
    >
      <el-form
        ref="nodeFormRef"
        :model="nodeForm"
        :rules="nodeRules"
        label-width="100px"
      >
        <el-form-item label="节点名称" prop="name">
          <el-input v-model="nodeForm.name" placeholder="请输入节点名称" />
        </el-form-item>
        <el-form-item label="节点标签" prop="label">
          <el-select
            v-model="nodeForm.label"
            placeholder="选择或输入新标签"
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option
              v-for="label in mergedLabels"
              :key="label"
              :label="label"
              :value="label"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="节点属性">
          <el-button
            type="text"
            @click="addNodeProperty"
            :icon="Plus"
            style="margin-bottom: 10px"
          >
            添加属性
          </el-button>
          <div
            v-for="(prop, index) in nodeForm.properties"
            :key="index"
            class="property-item"
          >
            <el-select
              v-model="prop.key"
              placeholder="选择或输入属性名"
              filterable
              allow-create
              style="width: 40%; margin-right: 10px"
            >
              <el-option
                v-for="key in presetPropertyKeys"
                :key="key"
                :label="key"
                :value="key"
              />
            </el-select>
            <el-input
              v-model="prop.value"
              placeholder="属性值"
              style="width: 40%; margin-right: 10px"
            />
            <el-button type="danger" text @click="removeNodeProperty(index)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateNodeDialog = false">取消</el-button>
        <el-button type="primary" @click="updatingNode ? updateNode() : createNode()" :loading="creating">
          {{ updatingNode ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 创建关系对话框 -->
    <el-dialog
      v-model="showCreateRelationDialog"
      :title="updatingRelationship ? '更新关系' : '创建关系'"
      width="600px"
      :close-on-click-modal="false"
      @close="resetRelationForm"
    >
      <el-form
        ref="relationFormRef"
        :model="relationForm"
        :rules="relationRules"
        label-width="100px"
      >
        <el-form-item label="起始节点" prop="fromNode">
          <el-row :gutter="10">
            <el-col :span="12">
              <el-select
                v-model="relationForm.fromNode.label"
                placeholder="选择标签"
                @change="onFromLabelChange"
              >
                <el-option
                  v-for="label in existingLabels"
                  :key="label"
                  :label="label"
                  :value="label"
                />
              </el-select>
            </el-col>
            <el-col :span="12">
              <el-select
                v-model="relationForm.fromNode.name"
                placeholder="选择节点"
                filterable
              >
                <el-option
                  v-for="node in fromNodeOptions"
                  :key="node.name"
                  :label="node.name"
                  :value="node.name"
                />
              </el-select>
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="目标节点" prop="toNode">
          <el-row :gutter="10">
            <el-col :span="12">
              <el-select
                v-model="relationForm.toNode.label"
                placeholder="选择标签"
                @change="onToLabelChange"
              >
                <el-option
                  v-for="label in existingLabels"
                  :key="label"
                  :label="label"
                  :value="label"
                />
              </el-select>
            </el-col>
            <el-col :span="12">
              <el-select
                v-model="relationForm.toNode.name"
                placeholder="选择节点"
                filterable
              >
                <el-option
                  v-for="node in toNodeOptions"
                  :key="node.name"
                  :label="node.name"
                  :value="node.name"
                />
              </el-select>
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="关系类型" prop="relationshipType">
          <el-select
            v-model="relationForm.relationshipType"
            placeholder="选择或输入新关系类型"
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option
              v-for="type in mergedRelationshipTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关系属性">
          <el-button
            type="text"
            @click="addRelationProperty"
            :icon="Plus"
            style="margin-bottom: 10px"
          >
            添加属性
          </el-button>
          <div
            v-for="(prop, index) in relationForm.properties"
            :key="index"
            class="property-item"
          >
            <el-select
              v-model="prop.key"
              placeholder="选择或输入属性名"
              filterable
              allow-create
              style="width: 40%; margin-right: 10px"
            >
              <el-option
                v-for="key in presetRelationPropertyKeys"
                :key="key"
                :label="key"
                :value="key"
              />
            </el-select>
            <el-input
              v-model="prop.value"
              placeholder="属性值"
              style="width: 40%; margin-right: 10px"
            />
            <el-button type="danger" text @click="removeRelationProperty(index)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateRelationDialog = false">取消</el-button>
        <el-button type="primary" @click="updatingRelationship ? updateRelation() : createRelation()" :loading="creating">
          {{ updatingRelationship ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Mermaid预览对话框 -->
    <el-dialog
      v-model="showMermaidDialog"
      title="Plan 流程图预览"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="generatingPlan" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>正在生成 Plan...</p>
      </div>
      <div v-else-if="mermaidCode" class="mermaid-preview">
        <div class="mermaid-stats">
          <el-tag type="success">路径数: {{ mermaidStats.paths_count }}</el-tag>
          <el-tag type="info" style="margin-left: 8px">节点数: {{ mermaidStats.nodes_count }}</el-tag>
          <el-tag type="warning" style="margin-left: 8px">边数: {{ mermaidStats.edges_count }}</el-tag>
        </div>
        <div class="mermaid-container">
          <pre class="mermaid-code">{{ mermaidCode }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="showMermaidDialog = false">关闭</el-button>
        <el-button type="primary" @click="copyMermaidCode" :disabled="!mermaidCode">
          <el-icon><CopyDocument /></el-icon>
          复制代码
        </el-button>
      </template>
    </el-dialog>

    <!-- JSON Plan 预览对话框 -->
    <el-dialog
      v-model="showJsonPlanDialog"
      title="Plan JSON 上缠"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="generatingPlan" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>正在生成 Plan...</p>
      </div>
      <div v-else-if="jsonPlanData" class="json-plan-preview">
        <div class="plan-stats">
          <el-tag type="success">Plan ID: {{ jsonPlanData.id }}</el-tag>
          <el-tag type="info" style="margin-left: 8px">节点数: {{ jsonPlanData.stats.nodes_count }}</el-tag>
          <el-tag type="warning" style="margin-left: 8px">边数: {{ jsonPlanData.stats.edges_count }}</el-tag>
        </div>
        
        <el-divider content-position="left">流程起始节点</el-divider>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="节点ID">
            <el-tag>{{ jsonPlanData.start }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">流程节点</el-divider>
        <div class="nodes-container">
          <div v-for="(nodeInfo, nodeId) in jsonPlanData.nodes" :key="nodeId" class="node-item">
            <div class="node-header">
              <el-tag type="primary">{{ nodeId }}</el-tag>
              <el-tag :type="nodeInfo.type === 'tool_action' ? 'success' : 'warning'" style="margin-left: 8px">
                {{ nodeInfo.type }}
              </el-tag>
            </div>
            <div class="node-content">
              <el-descriptions :column="2" border size="small" style="margin-top: 8px">
                <el-descriptions-item label="按钮" :span="2" v-if="nodeInfo.action">
                  {{ nodeInfo.action }}
                </el-descriptions-item>
                <el-descriptions-item label="描述" :span="2" v-if="nodeInfo.description">
                  {{ nodeInfo.description }}
                </el-descriptions-item>
                <el-descriptions-item label="理由" :span="2" v-if="nodeInfo.reason">
                  {{ nodeInfo.reason }}
                </el-descriptions-item>
                <el-descriptions-item label="输出" :span="2" v-if="nodeInfo.outputs && nodeInfo.outputs.length > 0">
                  <el-tag v-for="output in nodeInfo.outputs" :key="output" style="margin-right: 4px">
                    {{ output }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </div>

        <el-divider content-position="left">流程边（关系）</el-divider>
        <div class="edges-container">
          <div v-for="(edge, index) in jsonPlanData.edges" :key="index" class="edge-item">
            <div class="edge-flow">
              <el-tag type="primary">{{ edge.from }}</el-tag>
              <el-icon style="margin: 0 8px"><ArrowRight /></el-icon>
              <el-tag type="primary">{{ edge.to }}</el-tag>
            </div>
            <div v-if="edge.condition" class="edge-condition">
              <span style="color: #909399; font-size: 12px">[条件] {{ edge.condition }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showJsonPlanDialog = false">关闭x</el-button>
        <el-button type="primary" @click="copyJsonPlanCode" :disabled="!jsonPlanData">
          <el-icon><CopyDocument /></el-icon>
          复制JSON
        </el-button>
      </template>
    </el-dialog>
    <el-dialog
      v-model="showNodeDetailDialog"
      title="节点详情"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedNode" class="node-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="节点ID">
            {{ selectedNode.id }}
          </el-descriptions-item>
          <el-descriptions-item label="节点名称">
            <strong>{{ selectedNode.name }}</strong>
          </el-descriptions-item>
          <el-descriptions-item label="节点标签" :span="2">
            <el-tag type="primary" size="large">{{ selectedNode.label }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">节点属性</el-divider>
        <div v-if="selectedNode.properties && Object.keys(selectedNode.properties).length > 0" class="properties-section">
          <el-tag
            v-for="(value, key) in selectedNode.properties"
            :key="key"
            class="property-tag"
            type="info"
          >
            <strong>{{ key }}:</strong> {{ value }}
          </el-tag>
        </div>
        <div v-else class="empty-state">
          <el-empty description="该节点暂无自定义属性" :image-size="60" />
        </div>

        <el-divider content-position="left">节点位置</el-divider>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="X 坐标">
            {{ selectedNode.x?.toFixed(2) || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="Y 坐标">
            {{ selectedNode.y?.toFixed(2) || 'N/A' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="showNodeDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Connection, Delete, Close, Refresh, FullScreen, Download, Document, CopyDocument, Loading, InfoFilled, ArrowRight, DocumentCopy } from '@element-plus/icons-vue'
import * as d3 from 'd3'
import { useNeo4jStore } from '@/stores/neo4j'
import type { DatabaseInfo } from '@/stores/neo4j'

// 类型定义
interface NodeData {
  id: string
  name: string
  label: string
  properties?: Record<string, any>
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface LinkData {
  source: string | NodeData
  target: string | NodeData
  type: string
  properties?: Record<string, any>
}

interface GraphData {
  nodes: NodeData[]
  links: LinkData[]
}

interface PropertyItem {
  key: string
  value: string
}

// 响应式数据
const graphContainer = ref<HTMLDivElement>()
const showCreateNodeDialog = ref(false)
const showCreateRelationDialog = ref(false)
const showMermaidDialog = ref(false)
const showJsonPlanDialog = ref(false)
const showNodeDetailDialog = ref(false)
const showCreateCanvasDialog = ref(false)
const creating = ref(false)
const deleting = ref(false)
const generatingPlan = ref(false)
const selectedNode = ref<NodeData | null>(null)
const updatingNode = ref(false) // 是否在更新节点
const updatingRelationship = ref(false) // 是否在更新关系
const mermaidCode = ref('')
const mermaidStats = ref({
  paths_count: 0,
  nodes_count: 0,
  edges_count: 0
})

// JSON Plan 相关
const jsonPlanData = ref<{
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
} | null>(null)

// 拖拽连线相关
const linkCreationMode = ref(false)
const linkSourceNode = ref<NodeData | null>(null)
const tempLink = ref<any>(null)

// 画布相关
const databases = ref<DatabaseInfo[]>([])
const currentCanvas = ref<string>('default') // 默认使用 'default' 画布

// 右键菜单相关
const contextMenu = ref({
  show: false,
  x: 0,
  y: 0,
  type: '' as 'node' | 'link' | 'canvas' | '',
  data: null as NodeData | LinkData | null
})

// 新节点的初始位置（从右键菜单获取）
const newNodePosition = ref<{ x: number; y: number } | null>(null)

// 表单引用
const nodeFormRef = ref<FormInstance>()
const relationFormRef = ref<FormInstance>()
const canvasFormRef = ref<FormInstance>()

// Neo4j Store
const neo4jStore = useNeo4jStore()

// 现有标签和关系类型
const existingLabels = ref<string[]>([])
const existingRelationshipTypes = ref<string[]>([])
const fromNodeOptions = ref<NodeData[]>([])
const toNodeOptions = ref<NodeData[]>([])

// 预设的节点标签和属性名
const presetLabels = ['Step', 'Event', 'Output']
const presetPropertyKeys = ['Action', 'Observation', 'FinalAnswer']

// 预设的关系类型和关系属性名
const presetRelationshipTypes = ['Sequence', 'Branch']
const presetRelationPropertyKeys = ['Condition']

// 节点表单
const nodeForm = ref({
  name: '',
  label: '',
  properties: [] as PropertyItem[]
})

// 关系表单
const relationForm = ref({
  fromNode: {
    label: '',
    name: ''
  },
  toNode: {
    label: '',
    name: ''
  },
  relationshipType: '',
  properties: [] as PropertyItem[]
})

// 画布表单
const canvasForm = ref({
  name: '',
  description: ''
})

// 表单验证规则
const nodeRules: FormRules = {
  name: [
    { required: true, message: '请输入节点名称', trigger: 'blur' }
  ],
  label: [
    { required: true, message: '请选择或输入节点标签', trigger: 'change' }
  ]
}

const relationRules: FormRules = {
  fromNode: [
    { required: true, message: '请选择起始节点', trigger: 'change' }
  ],
  toNode: [
    { required: true, message: '请选择目标节点', trigger: 'change' }
  ],
  relationshipType: [
    { required: true, message: '请选择或输入关系类型', trigger: 'change' }
  ]
}

const canvasRules: FormRules = {
  name: [
    { required: true, message: '请输入画布名称', trigger: 'blur' },
    { 
      pattern: /^[a-zA-Z0-9_-]+$/, 
      message: '画布名称只能包含英文、数字、下划线和短横线', 
      trigger: 'blur' 
    }
  ]
}

// D3.js相关变量
let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>
let simulation: d3.Simulation<NodeData, LinkData>
let graphData: GraphData = { nodes: [], links: [] }

// 简单的字符串哈希函数（替代MD5）
const simpleHash = (str: string): string => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36)
}

// 计算关系（relationship）唯一标识的哈希值
const getRelationshipHash = (link: LinkData): string => {
  const sourceId = typeof link.source === 'string' ? link.source : link.source.id
  const targetId = typeof link.target === 'string' ? link.target : link.target.id
  
  // 使用关系的关键属性计算哈希
  const relationshipKey = JSON.stringify({
    source: sourceId,
    target: targetId,
    type: link.type,
    properties: link.properties || {}
  })
  return simpleHash(relationshipKey)
}

// 保存单个节点位置（增量更新，推荐在拖拽时使用）
const saveNodePosition = async (node: NodeData) => {
  if (node.x === undefined || node.y === undefined) return
  
  try {
    await neo4jStore.updateNodePosition(node.id, node.x, node.y)
  } catch (error) {
    console.error('保存节点位置失败:', error)
  }
}

// 批量保存节点位置（全量更新，仅在初始化时使用）
const saveNodePositions = async () => {
  const positions: Record<string, { x: number; y: number }> = {}
  graphData.nodes.forEach(node => {
    if (node.x !== undefined && node.y !== undefined) {
      positions[node.id] = { x: node.x, y: node.y }
    }
  })
  
  try {
    await neo4jStore.saveAllNodePositions(positions)
  } catch (error) {
    console.error('保存节点位置失败:', error)
  }
}

// 从后端加载节点位置
const loadNodePositions = async (): Promise<Record<string, { x: number; y: number }>> => {
  try {
    return await neo4jStore.getAllNodePositions()
  } catch (error) {
    console.error('加载节点位置失败:', error)
    return {}
  }
}

// 清除保存的节点位置
const clearNodePositions = async () => {
  try {
    await neo4jStore.clearAllNodePositions()
  } catch (error) {
    console.error('清空节点位置失败:', error)
  }
}

// 初始化图谱
const initGraph = () => {
  if (!graphContainer.value) return

  // 清除现有内容
  d3.select(graphContainer.value).selectAll('*').remove()

  const width = graphContainer.value.clientWidth
  const height = graphContainer.value.clientHeight

  // 创建SVG
  svg = d3.select(graphContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  // 添加缩放功能
  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      svg.select('.graph-group').attr('transform', event.transform)
    })

  svg.call(zoom)

  // 创建图形组
  const graphGroup = svg.append('g').attr('class', 'graph-group')

  // 创建箭头标记（多种颜色，更大更清晰）
  const defs = svg.append('defs')
  
  // 默认箭头（紧靠节点，小尺寸）- 用于未定义的关系类型
  defs.append('marker')
    .attr('id', 'arrow-default')
    .attr('viewBox', '0 -6 12 12')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 8)
    .attr('markerHeight', 8)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5L3,0Z')
    .attr('fill', '#909399')
    .style('stroke', 'none')

  // Sequence 箭头（蓝色，紧靠节点，小尺寸）
  defs.append('marker')
    .attr('id', 'arrow-sequence')
    .attr('viewBox', '0 -6 12 12')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 8)
    .attr('markerHeight', 8)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5L3,0Z')
    .attr('fill', '#409eff')
    .style('stroke', 'none')

  // Branch 箭头（橙色，紧靠节点，小尺寸）
  defs.append('marker')
    .attr('id', 'arrow-branch')
    .attr('viewBox', '0 -6 12 12')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 8)
    .attr('markerHeight', 8)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5L3,0Z')
    .attr('fill', '#e6a23c')
    .style('stroke', 'none')

  // Dependency 箭头（绿色，紧靠节点，小尺寸）
  defs.append('marker')
    .attr('id', 'arrow-dependency')
    .attr('viewBox', '0 -6 12 12')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 8)
    .attr('markerHeight', 8)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5L3,0Z')
    .attr('fill', '#67c23a')
    .style('stroke', 'none')

  // Trigger 箭头（红色，紧靠节点，小尺寸）
  defs.append('marker')
    .attr('id', 'arrow-trigger')
    .attr('viewBox', '0 -6 12 12')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 8)
    .attr('markerHeight', 8)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5L3,0Z')
    .attr('fill', '#f56c6c')
    .style('stroke', 'none')

  // 添加阴影滤镜
  const filter = defs.append('filter')
    .attr('id', 'drop-shadow')
    .attr('height', '130%')

  filter.append('feGaussianBlur')
    .attr('in', 'SourceAlpha')
    .attr('stdDeviation', 3)

  filter.append('feOffset')
    .attr('dx', 2)
    .attr('dy', 2)
    .attr('result', 'offsetblur')

  filter.append('feComponentTransfer')
    .append('feFuncA')
    .attr('type', 'linear')
    .attr('slope', 0.3)

  const feMerge = filter.append('feMerge')
  feMerge.append('feMergeNode')
  feMerge.append('feMergeNode')
    .attr('in', 'SourceGraphic')

  // 初始化力仿真
  simulation = d3.forceSimulation<NodeData>()
    .force('link', d3.forceLink<NodeData, LinkData>().id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(30))
}

// 更新图谱显示
const updateGraph = () => {
  if (!svg || !simulation) return

  const graphGroup = svg.select('.graph-group')

  // 为每条连线生成唯一ID（如果还没有）
  graphData.links.forEach((link, index) => {
    if (!(link as any).__uniqueId) {
      (link as any).__uniqueId = `link_${Date.now()}_${index}_${Math.random().toString(36).substring(2, 9)}`
    }
  })

  // 计算相同方向的连线数量和索引
  const linkCounts = new Map<string, number>()
  const linkIndexes = new Map<any, number>() // 使用link对象本身作为key
  
  // 统计每个方向的连线总数
  graphData.links.forEach((link) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
    const targetId = typeof link.target === 'string' ? link.target : link.target.id
    const directionKey = `${sourceId}->${targetId}`
    linkCounts.set(directionKey, (linkCounts.get(directionKey) || 0) + 1)
  })

  // 为每个方向的连线按顺序分配索引
  const directionIndexCounters = new Map<string, number>()
  graphData.links.forEach((link) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
    const targetId = typeof link.target === 'string' ? link.target : link.target.id
    const directionKey = `${sourceId}->${targetId}`
    
    const currentIndex = directionIndexCounters.get(directionKey) || 0
    linkIndexes.set(link, currentIndex) // 直接使用link对象作为key
    directionIndexCounters.set(directionKey, currentIndex + 1)
  })

  // 更新链接 - 使用 path 替代 line 以支持曲线
  const link = graphGroup.selectAll('.link')
    .data(graphData.links, (d: any) => d.__uniqueId) // 使用唯一ID作为key

  link.exit().remove()

  const linkEnter = link.enter().append('path')
    .attr('class', 'link')
    .attr('data-link-id', (d: any) => d.__uniqueId) // 添加data属性
    .attr('fill', 'none')
    .attr('stroke', d => getLinkColor(d.type))
    .attr('stroke-width', d => d.type === 'Branch' ? 3 : 2)
    .attr('stroke-dasharray', d => d.type === 'Branch' ? '5,5' : 'none')
    .attr('marker-end', d => {
      const markerType = d.type.toLowerCase()
      // 检查是否有对应的箭头标记,如果没有则使用默认箭头
      const knownTypes = ['sequence', 'branch', 'dependency', 'trigger']
      const markerId = knownTypes.includes(markerType) ? markerType : 'default'
      return `url(#arrow-${markerId})`
    })
    .style('cursor', 'pointer')
    .style('opacity', 0.8)
    .on('click', (event: any, d: LinkData) => {
      event.stopPropagation()
      showLinkContextMenu(event, d)
    })
    .on('mouseenter', function(event: any, d: LinkData) {
      d3.select(this)
        .style('opacity', 1)
        .attr('stroke-width', 4)
    })
    .on('mouseleave', function(event: any, d: LinkData) {
      d3.select(this)
        .style('opacity', 0.8)
        .attr('stroke-width', d.type === 'Branch' ? 3 : 2)
    })

  const linkUpdate = linkEnter.merge(link)

  // 更新节点
  const node = graphGroup.selectAll('.node')
    .data(graphData.nodes, (d: any) => d.id)

  node.exit().remove()

  const nodeEnter = node.enter().append('g')
    .attr('class', 'node')
    .style('cursor', 'pointer')
    .on('contextmenu', (event: any, d: NodeData) => {
      event.preventDefault()
      event.stopPropagation()
      showNodeContextMenu(event, d)
    })
    .on('click', (event: any, d: NodeData) => {
      event.stopPropagation()
      handleNodeClick(event, d)
    })
    .call(d3.drag<SVGGElement, NodeData>()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded))

  // 添加节点圆圈
  nodeEnter.append('circle')
    .attr('r', 25)
    .attr('fill', d => getNodeColor(d.label))
    .attr('stroke', d => getNodeStrokeColor(d.label))
    .attr('stroke-width', 3)
    .attr('filter', 'url(#drop-shadow)')
    .style('cursor', 'pointer')

  // 添加节点标签文字描边（增强可读性）
  nodeEnter.append('text')
    .attr('class', 'node-text-stroke')
    .attr('dy', 5)
    .attr('text-anchor', 'middle')
    .attr('fill', 'none')
    .attr('stroke', '#000')
    .attr('stroke-width', 3)
    .attr('font-size', '15px')
    .attr('font-weight', 'bold')
    .style('pointer-events', 'none')
    .style('user-select', 'none')
    .text(d => d.name.length > 6 ? d.name.substring(0, 5) + '...' : d.name)

  // 添加节点标签（主文字）
  nodeEnter.append('text')
    .attr('class', 'node-text')
    .attr('dy', 5)
    .attr('text-anchor', 'middle')
    .attr('fill', '#fff')
    .attr('font-size', '15px')
    .attr('font-weight', 'bold')
    .style('pointer-events', 'none')
    .style('user-select', 'none')
    .text(d => d.name.length > 6 ? d.name.substring(0, 5) + '...' : d.name)

  // 添加节点名称提示（完整名称）
  nodeEnter.append('title')
    .text(d => `${d.label}: ${d.name}`)

  const nodeUpdate = nodeEnter.merge(node)

  // 添加关系标签
  const relationLabel = graphGroup.selectAll('.relation-label')
    .data(graphData.links, (d: any) => d.__uniqueId) // 使用唯一ID

  relationLabel.exit().remove()
  
  // 添加关系标签背景
  const relationLabelBgGroup = graphGroup.selectAll('.relation-label-group')
    .data(graphData.links, (d: any) => d.__uniqueId) // 使用唯一ID
  
  relationLabelBgGroup.exit().remove()
  
  const relationLabelBgEnter = relationLabelBgGroup.enter().append('g')
    .attr('class', 'relation-label-group')
    .attr('data-link-id', (d: any) => d.__uniqueId) // 添加data属性
    .style('cursor', 'pointer')
    .on('click', (event: any, d: LinkData) => {
      event.stopPropagation()
      showLinkContextMenu(event, d)
    })
    .on('mouseenter', function(event: any, d: any) {
      // 高亮标签背景
      d3.select(this).select('.relation-label-bg')
        .style('opacity', 1)
        .attr('stroke-width', 2.5)
      
      // 同时高亮对应的连线（使用唯一ID匹配）
      graphGroup.selectAll('.link')
        .filter((linkData: any) => linkData.__uniqueId === d.__uniqueId)
        .style('opacity', 1)
        .attr('stroke-width', 4)
    })
    .on('mouseleave', function(event: any, d: any) {
      // 恢复标签背景
      d3.select(this).select('.relation-label-bg')
        .style('opacity', 0.95)
        .attr('stroke-width', 1.5)
      
      // 恢复连线
      graphGroup.selectAll('.link')
        .filter((linkData: any) => linkData.__uniqueId === d.__uniqueId)
        .style('opacity', 0.8)
        .attr('stroke-width', d.type === 'Branch' ? 3 : 2)
    })

  relationLabelBgEnter.append('rect')
    .attr('class', 'relation-label-bg')
    .attr('fill', d => getLinkColor(d.type))
    .attr('rx', 4)
    .attr('ry', 4)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('opacity', 0.95)

  // 添加关系标签文字描边
  relationLabelBgEnter.append('text')
    .attr('class', 'relation-label-stroke')
    .attr('text-anchor', 'middle')
    .attr('fill', 'none')
    .attr('stroke', '#000')
    .attr('stroke-width', 2.5)
    .attr('font-size', '13px')
    .attr('font-weight', 'bold')
    .style('pointer-events', 'none')
    .text(d => d.type)

  const relationLabelEnter = relationLabelBgEnter.append('text')
    .attr('class', 'relation-label')
    .attr('text-anchor', 'middle')
    .attr('fill', '#fff')
    .attr('font-size', '13px')
    .attr('font-weight', 'bold')
    .style('pointer-events', 'none')
    .text(d => d.type)

  const relationLabelBgUpdate = relationLabelBgEnter.merge(relationLabelBgGroup)

  // 更新仿真
  simulation.nodes(graphData.nodes)
  simulation.force<d3.ForceLink<NodeData, LinkData>>('link')!.links(graphData.links)

  simulation.on('tick', () => {
    // 更新连线路径 - 使用二次贝塞尔曲线避免重叠
    linkUpdate.attr('d', (d: any) => {
      const sourceId = d.source.id || d.source
      const targetId = d.target.id || d.target
      const directionKey = `${sourceId}->${targetId}`
      
      const totalLinks = linkCounts.get(directionKey) || 1
      const linkIndex = linkIndexes.get(d) ?? 0 // 使用link对象本身作为key
      
      const dx = d.target.x - d.source.x
      const dy = d.target.y - d.source.y
      const dr = Math.sqrt(dx * dx + dy * dy)
      
      if (dr === 0) return `M${d.source.x},${d.source.y}L${d.target.x},${d.target.y}`
      
      // 只有1条连线时使用直线，多条连线时使用曲线
      if (totalLinks === 1) {
        return `M${d.source.x},${d.source.y}L${d.target.x},${d.target.y}`
      }
      
      // 多条同向连线时，使用二次贝塞尔曲线分散显示
      const baseOffset = 30 // 基础偏移量
      const maxOffset = baseOffset + (totalLinks - 2) * 15 // 每多一条线增加15像素
      
      // 计算当前连线的偏移量（居中分布）
      const offset = (linkIndex - (totalLinks - 1) / 2) * (maxOffset / Math.max(totalLinks - 1, 1))
      
      // 计算控制点（在连线中点的垂直方向偏移）
      const midX = (d.source.x + d.target.x) / 2
      const midY = (d.source.y + d.target.y) / 2
      const controlX = midX - (dy / dr) * offset
      const controlY = midY + (dx / dr) * offset
      
      // 使用二次贝塞尔曲线
      return `M${d.source.x},${d.source.y}Q${controlX},${controlY} ${d.target.x},${d.target.y}`
    })

    nodeUpdate.attr('transform', d => `translate(${d.x},${d.y})`)

    // 更新关系标签组的位置
    relationLabelBgUpdate.attr('transform', (d: any) => {
      const sourceId = d.source.id || d.source
      const targetId = d.target.id || d.target
      const directionKey = `${sourceId}->${targetId}`
      
      const totalLinks = linkCounts.get(directionKey) || 1
      const linkIndex = linkIndexes.get(d) ?? 0 // 使用link对象本身作为key
      
      const dx = d.target.x - d.source.x
      const dy = d.target.y - d.source.y
      const dr = Math.sqrt(dx * dx + dy * dy)
      
      // 计算标签位置(在曲线的控制点位置，即曲线中点)
      let x = (d.source.x + d.target.x) / 2
      let y = (d.source.y + d.target.y) / 2
      
      // 多条连线时，标签位置需要跟随曲线偏移
      if (totalLinks > 1 && dr !== 0) {
        const baseOffset = 30 // 与连线保持一致
        const maxOffset = baseOffset + (totalLinks - 2) * 15 // 与连线保持一致
        const offset = (linkIndex - (totalLinks - 1) / 2) * (maxOffset / Math.max(totalLinks - 1, 1))
        
        // 标签位置在贝塞尔曲线的控制点处
        const offsetX = -dy / dr * offset
        const offsetY = dx / dr * offset
        x += offsetX
        y += offsetY
      }
      
      return `translate(${x},${y})`
    })
    
    // 更新标签背景尺寸和位置（增大以适应更大的文字）
    relationLabelBgUpdate.select('.relation-label-bg')
      .attr('x', -30)
      .attr('y', -11)
      .attr('width', 60)
      .attr('height', 22)
    
    // 更新标签文字描边位置
    relationLabelBgUpdate.select('.relation-label-stroke')
      .attr('x', 0)
      .attr('y', 5)
    
    // 更新标签文字位置
    relationLabelBgUpdate.select('.relation-label')
      .attr('x', 0)
      .attr('y', 5)
  })

  simulation.alpha(1).restart()
}

// 获取节点颜色
const getNodeColor = (label: string): string => {
  const colors: Record<string, string> = {
    'Event': '#e74c3c',      // 红色 - 事件
    'Step': '#3498db',       // 蓝色 - 步骤
    'Output': '#2ecc71',     // 绿色 - 输出
    'Server': '#9b59b6',     // 紫色
    'Database': '#1abc9c',   // 青色
    'User': '#f39c12',       // 橙色
    'Service': '#16a085',    // 深青色
    'Network': '#f1c40f',    // 黄色
    'Device': '#e67e22'      // 深橙色
  }
  return colors[label] || '#34495e'  // 默认深灰色
}

// 获取节点边框颜色（更深的颜色）
const getNodeStrokeColor = (label: string): string => {
  const colors: Record<string, string> = {
    'Event': '#c0392b',
    'Step': '#2980b9',
    'Output': '#27ae60',
    'Server': '#8e44ad',
    'Database': '#16a085',
    'User': '#d68910',
    'Service': '#138d75',
    'Network': '#f39c12',
    'Device': '#ca6f1e'
  }
  return colors[label] || '#2c3e50'
}

// 获取连线颜色
const getLinkColor = (type: string): string => {
  const colors: Record<string, string> = {
    'Sequence': '#409eff',   // 蓝色 - 顺序
    'Branch': '#e6a23c',     // 橙色 - 分支
    'Dependency': '#67c23a', // 绿色 - 依赖
    'Trigger': '#f56c6c'     // 红色 - 触发
  }
  return colors[type] || '#909399'  // 默认灰色
}

// 拖拽事件处理
const dragStarted = (event: any, d: NodeData) => {
  // 如果处于连线创建模式，不处理拖拽
  if (linkCreationMode.value) {
    return
  }
  
  // 如果按住 Shift 键，进入连线创建模式
  if (event.sourceEvent.shiftKey) {
    event.sourceEvent.stopPropagation()
    startLinkCreation(d)
    return
  }
  
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

const dragged = (event: any, d: NodeData) => {
  // 如果处于连线创建模式，更新临时连线
  if (linkCreationMode.value && linkSourceNode.value) {
    updateTempLink(event)
    return
  }
  
  d.fx = event.x
  d.fy = event.y
}

const dragEnded = (event: any, d: NodeData) => {
  // 如果处于连线创建模式，不处理位置
  if (linkCreationMode.value) {
    return
  }
  
  if (!event.active) simulation.alphaTarget(0)
  // 保持节点在拖动后的位置固定
  d.fx = d.x
  d.fy = d.y
  
  // 拖拽结束后保存单个节点位置（增量更新，更高效）
  saveNodePosition(d)
}

// 合并预设标签和现有标签(去重)
const mergedLabels = computed(() => {
  const allLabels = [...presetLabels, ...existingLabels.value]
  return Array.from(new Set(allLabels))
})

// 合并预设关系类型和现有关系类型(去重)
const mergedRelationshipTypes = computed(() => {
  const allTypes = [...presetRelationshipTypes, ...existingRelationshipTypes.value]
  return Array.from(new Set(allTypes))
})

// 过滤数据库列表（排除 default，因为已在模板中硬编码）
const filteredDatabases = computed(() => {
  return databases.value.filter(db => db.name !== 'default')
})

// 加载现有数据
const loadExistingData = async () => {
  try {
    const [labels, relationshipTypes] = await Promise.all([
      neo4jStore.getLabels(),
      neo4jStore.getRelationshipTypes()
    ])
    existingLabels.value = labels
    existingRelationshipTypes.value = relationshipTypes
  } catch (error) {
    console.error('加载现有数据失败:', error)
    ElMessage.error('加载现有数据失败')
  }
}

// 加载图谱数据
const loadGraphData = async () => {
  try {
    const [nodes, relationships] = await Promise.all([
      neo4jStore.getAllNodes(),
      neo4jStore.getAllRelationships()
    ])

    // 从后端加载保存的节点位置
    const savedPositions = await loadNodePositions()

    // 转换节点数据
    graphData.nodes = nodes.map(node => {
      const nodeId = `${node.label}-${node.name}`
      const savedPos = savedPositions[nodeId]
      
      return {
        id: nodeId,
        name: node.name,
        label: node.label,
        properties: node.properties,
        // 如果有保存的位置，使用保存的位置并固定；否则让 D3 自动计算
        x: savedPos?.x,
        y: savedPos?.y,
        fx: savedPos?.x ?? null, // 只有保存了位置的节点才固定
        fy: savedPos?.y ?? null
      }
    })

    // 转换关系数据
    graphData.links = relationships.map(rel => ({
      source: `${rel.from_node.label}-${rel.from_node.name}`,
      target: `${rel.to_node.label}-${rel.to_node.name}`,
      type: rel.relationship_type,
      properties: rel.relationship_properties
    }))

    updateGraph()
    ElMessage.success('图谱数据加载成功')
  } catch (error) {
    console.error('加载图谱数据失败:', error)
    ElMessage.error('加载图谱数据失败')
  }
}

// 节点属性操作
const addNodeProperty = () => {
  nodeForm.value.properties.push({ key: '', value: '' })
}

const removeNodeProperty = (index: number) => {
  nodeForm.value.properties.splice(index, 1)
}

// 关系属性操作
const addRelationProperty = () => {
  relationForm.value.properties.push({ key: '', value: '' })
}

const removeRelationProperty = (index: number) => {
  relationForm.value.properties.splice(index, 1)
}

// 标签变化处理
const onFromLabelChange = async () => {
  if (relationForm.value.fromNode.label) {
    try {
      const nodes = await neo4jStore.getAllNodes(relationForm.value.fromNode.label)
      fromNodeOptions.value = nodes
    } catch (error) {
      console.error('获取节点选项失败:', error)
    }
  }
}

const onToLabelChange = async () => {
  if (relationForm.value.toNode.label) {
    try {
      const nodes = await neo4jStore.getAllNodes(relationForm.value.toNode.label)
      toNodeOptions.value = nodes
    } catch (error) {
      console.error('获取节点选项失败:', error)
    }
  }
}

// 创建节点
const createNode = async () => {
  if (!nodeFormRef.value) return

  try {
    await nodeFormRef.value.validate()
    creating.value = true

    const properties: Record<string, any> = {}
    nodeForm.value.properties.forEach(prop => {
      if (prop.key && prop.value) {
        properties[prop.key] = prop.value
      }
    })

    await neo4jStore.createNode({
      name: nodeForm.value.name,
      label: nodeForm.value.label,
      properties: Object.keys(properties).length > 0 ? properties : undefined
    })

    // 如果是从右键菜单创建的节点，立即保存位置
    if (newNodePosition.value) {
      const nodeId = `${nodeForm.value.label}-${nodeForm.value.name}`
      await neo4jStore.updateNodePosition(
        nodeId,
        newNodePosition.value.x,
        newNodePosition.value.y
      )
      newNodePosition.value = null
    }

    ElMessage.success('节点创建成功')
    showCreateNodeDialog.value = false
    resetNodeForm()
    await loadGraphData()
  } catch (error) {
    console.error('创建节点失败:', error)
    ElMessage.error('创建节点失败')
  } finally {
    creating.value = false
  }
}

// 更新节点
const updateNode = async () => {
  if (!nodeFormRef.value) return

  try {
    await nodeFormRef.value.validate()
    creating.value = true

    const properties: Record<string, any> = {}
    nodeForm.value.properties.forEach(prop => {
      if (prop.key && prop.value) {
        properties[prop.key] = prop.value
      }
    })

    await neo4jStore.updateNode({
      name: nodeForm.value.name,
      label: nodeForm.value.label,
      properties: Object.keys(properties).length > 0 ? properties : undefined
    })

    ElMessage.success('节点更新成功')
    showCreateNodeDialog.value = false
    updatingNode.value = false
    resetNodeForm()
    await loadGraphData()
  } catch (error) {
    console.error('更新节点失败:', error)
    ElMessage.error('更新节点失败')
  } finally {
    creating.value = false
  }
}

// 创建关系
const createRelation = async () => {
  if (!relationFormRef.value) return

  try {
    await relationFormRef.value.validate()
    creating.value = true

    const properties: Record<string, any> = {}
    relationForm.value.properties.forEach(prop => {
      if (prop.key && prop.value) {
        properties[prop.key] = prop.value
      }
    })

    await neo4jStore.createRelationship({
      from_node: {
        name: relationForm.value.fromNode.name,
        label: relationForm.value.fromNode.label
      },
      to_node: {
        name: relationForm.value.toNode.name,
        label: relationForm.value.toNode.label
      },
      relationship_type: relationForm.value.relationshipType,
      relationship_properties: Object.keys(properties).length > 0 ? properties : undefined
    })

    ElMessage.success('关系创建成功')
    showCreateRelationDialog.value = false
    resetRelationForm()
    await loadGraphData()
  } catch (error) {
    console.error('创建关系失败:', error)
    ElMessage.error('创建关系失败')
  } finally {
    creating.value = false
  }
}

// 更新关系
const updateRelation = async () => {
  if (!relationFormRef.value) return

  try {
    await relationFormRef.value.validate()
    creating.value = true

    const properties: Record<string, any> = {}
    relationForm.value.properties.forEach(prop => {
      if (prop.key && prop.value) {
        properties[prop.key] = prop.value
      }
    })

    await neo4jStore.updateRelationship({
      from_node: {
        name: relationForm.value.fromNode.name,
        label: relationForm.value.fromNode.label
      },
      to_node: {
        name: relationForm.value.toNode.name,
        label: relationForm.value.toNode.label
      },
      relationship_type: relationForm.value.relationshipType,
      relationship_properties: Object.keys(properties).length > 0 ? properties : undefined
    })

    ElMessage.success('关系更新成功')
    showCreateRelationDialog.value = false
    updatingRelationship.value = false
    resetRelationForm()
    await loadGraphData()
  } catch (error) {
    console.error('更新关系失败:', error)
    ElMessage.error('更新关系失败')
  } finally {
    creating.value = false
  }
}

// 从右键菜单显示节点详情
const showNodeDetailFromContext = () => {
  const nodeData = contextMenu.value.data as NodeData
  if (!nodeData) return

  console.log('显示节点详情:', nodeData)
  hideContextMenu()
  selectedNode.value = nodeData
  showNodeDetailDialog.value = true
}

// 从右键菜单更新节点
const updateNodeFromContext = () => {
  const nodeData = contextMenu.value.data as NodeData
  if (!nodeData) return

  hideContextMenu()

  // 填充节点表单
  nodeForm.value = {
    name: nodeData.name,
    label: nodeData.label,
    properties: Object.entries(nodeData.properties || {}).map(([key, value]) => ({
      key,
      value: String(value)
    }))
  }

  // 设置更新标记
  updatingNode.value = true
  // 显示创建节点对话框（复用），标题会改为"更新节点"
  showCreateNodeDialog.value = true
}

// 从右键菜单更新关系
const updateRelationshipFromContext = () => {
  const linkData = contextMenu.value.data as LinkData
  if (!linkData) return

  hideContextMenu()

  // 获取源和目标节点信息
  const sourceNode = typeof linkData.source === 'string' 
    ? graphData.nodes.find(n => n.id === linkData.source) 
    : (linkData.source as NodeData)
  const targetNode = typeof linkData.target === 'string'
    ? graphData.nodes.find(n => n.id === linkData.target)
    : (linkData.target as NodeData)

  if (!sourceNode || !targetNode) {
    ElMessage.error('无法获取关系的节点信息')
    return
  }

  // 填充关系表单
  relationForm.value = {
    fromNode: {
      label: sourceNode.label,
      name: sourceNode.name
    },
    toNode: {
      label: targetNode.label,
      name: targetNode.name
    },
    relationshipType: linkData.type,
    properties: Object.entries(linkData.properties || {}).map(([key, value]) => ({
      key,
      value: String(value)
    }))
  }

  // 设置更新标记
  updatingRelationship.value = true
  // 显示创建关系对话框（复用），标题会改为"更新关系"
  showCreateRelationDialog.value = true
}

// 显示节点右键菜单
const showNodeContextMenu = (event: MouseEvent, nodeData: NodeData) => {
  contextMenu.value = {
    show: true,
    x: event.clientX,
    y: event.clientY,
    type: 'node',
    data: nodeData
  }
}

// 显示关系线点击菜单
const showLinkContextMenu = (event: MouseEvent, linkData: LinkData) => {
  contextMenu.value = {
    show: true,
    x: event.clientX,
    y: event.clientY,
    type: 'link',
    data: linkData
  }
}

// 隐藏上下文菜单
const hideContextMenu = () => {
  contextMenu.value.show = false
  contextMenu.value.data = null
  contextMenu.value.type = ''
}

// ==================== 拖拽创建关系相关方法 ====================

// 开始创建连线
const startLinkCreation = (sourceNode: NodeData) => {
  linkCreationMode.value = true
  linkSourceNode.value = sourceNode
  
  // 创建临时连线
  const graphGroup = svg.select('.graph-group')
  tempLink.value = graphGroup.append('line')
    .attr('class', 'temp-link')
    .attr('stroke', '#409eff')
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '5,5')
    .attr('opacity', 0.6)
    .attr('pointer-events', 'none')
  
  ElMessage.info('拖动到目标节点以创建关系')
}

// 从右键菜单开始创建关系
const startLinkCreationFromContext = () => {
  const nodeData = contextMenu.value.data as NodeData
  if (!nodeData) return
  
  hideContextMenu()
  startLinkCreation(nodeData)
  
  // 注意：不需要添加 mousemove 监听，因为从右键菜单启动的连线创建
  // 会通过点击节点来完成，而不是鼠标移动
}

// 更新临时连线位置（用于 Shift + 拖拽）
const updateTempLink = (event: any) => {
  if (!tempLink.value || !linkSourceNode.value) return
  
  tempLink.value
    .attr('x1', linkSourceNode.value.x)
    .attr('y1', linkSourceNode.value.y)
    .attr('x2', event.x)
    .attr('y2', event.y)
}

// 处理画布鼠标移动（用于从右键菜单创建关系时）
const handleCanvasMouseMove = (event: MouseEvent) => {
  if (!linkCreationMode.value || !tempLink.value || !linkSourceNode.value) return
  
  const container = graphContainer.value
  if (!container) return
  
  const rect = container.getBoundingClientRect()
  const svgElement = container.querySelector('svg')
  if (!svgElement) return
  
  // 获取当前的缩放和平移变换
  const graphGroup = svg.select('.graph-group')
  const transform = (graphGroup.node() as any)?.transform?.baseVal
  let scale = 1
  let translateX = 0
  let translateY = 0
  
  if (transform && transform.length > 0) {
    const matrix = transform[0].matrix
    scale = matrix.a
    translateX = matrix.e
    translateY = matrix.f
  }
  
  // 计算鼠标在 SVG 坐标系中的位置
  const mouseX = (event.clientX - rect.left - translateX) / scale
  const mouseY = (event.clientY - rect.top - translateY) / scale
  
  tempLink.value
    .attr('x1', linkSourceNode.value.x)
    .attr('y1', linkSourceNode.value.y)
    .attr('x2', mouseX)
    .attr('y2', mouseY)
}

// 处理节点点击（用于简化创建关系）
const handleNodeClick = (event: any, node: NodeData) => {
  // 如果处于连线创建模式，完成连线创建
  if (linkCreationMode.value && linkSourceNode.value) {
    event.stopPropagation()
    handleNodeMouseUp(event, node)
    return
  }
}

// 处理节点鼠标释放
const handleNodeMouseUp = (event: any, targetNode: NodeData) => {
  if (!linkCreationMode.value || !linkSourceNode.value) return
  
  event.stopPropagation()
  
  // 移除临时连线
  if (tempLink.value) {
    tempLink.value.remove()
    tempLink.value = null
  }
  
  // 检查是否是同一个节点
  if (linkSourceNode.value.id === targetNode.id) {
    ElMessage.warning('无法创建指向自己的关系')
    linkCreationMode.value = false
    linkSourceNode.value = null
    return
  }
  
  // 填充关系表单
  relationForm.value.fromNode.label = linkSourceNode.value.label
  relationForm.value.fromNode.name = linkSourceNode.value.name
  relationForm.value.toNode.label = targetNode.label
  relationForm.value.toNode.name = targetNode.name
  
  // 重置连线创建模式
  linkCreationMode.value = false
  linkSourceNode.value = null
  
  // 显示创建关系对话框
  showCreateRelationDialog.value = true
}

// 取消连线创建
const cancelLinkCreation = () => {
  if (tempLink.value) {
    tempLink.value.remove()
    tempLink.value = null
  }
  linkCreationMode.value = false
  linkSourceNode.value = null
}

// 处理画布鼠标释放（用于取消连线创建）
const handleCanvasMouseUp = (event: any) => {
  if (linkCreationMode.value) {
    cancelLinkCreation()
    ElMessage.info('已取消创建关系')
  }
}

// 处理画布右键菜单
const handleCanvasContextMenu = (event: MouseEvent) => {
  event.preventDefault()
  event.stopPropagation()
  
  // 检查是否点击在 SVG 画布上（而不是节点或连线）
  const target = event.target as HTMLElement
  if (target.tagName === 'svg' || target.classList.contains('graph-canvas')) {
    // 计算不右键点在SVG坐标系中的位置
    const container = graphContainer.value
    if (container) {
      const rect = container.getBoundingClientRect()
      const svgElement = container.querySelector('svg') as SVGSVGElement
      if (svgElement) {
        // 获取当前的縮放和平移变换
        const graphGroup = svg.select('.graph-group')
        const transform = (graphGroup.node() as any)?.transform?.baseVal
        let scale = 1
        let translateX = 0
        let translateY = 0
        
        if (transform && transform.length > 0) {
          const matrix = transform[0].matrix
          scale = matrix.a
          translateX = matrix.e
          translateY = matrix.f
        }
        
        // 计算鼠标在 SVG 坐标系中的位置
        const mouseX = (event.clientX - rect.left - translateX) / scale
        const mouseY = (event.clientY - rect.top - translateY) / scale
        
        // 存储新节点的位置
        newNodePosition.value = { x: mouseX, y: mouseY }
      }
    }
    
    contextMenu.value = {
      show: true,
      x: event.clientX,
      y: event.clientY,
      type: 'canvas',
      data: null
    }
  }
}

// 从画布右键菜单显示创建节点对话框
const showCreateNodeDialogFromContext = () => {
  hideContextMenu()
  showCreateNodeDialog.value = true
}

// 从上下文菜单生成Plan
const generatePlanFromContext = async () => {
  const nodeData = contextMenu.value.data as NodeData
  if (!nodeData) {
    console.error('节点数据为空')
    return
  }

  console.log('开始生成Plan，节点:', nodeData.name, '标签:', nodeData.label)

  // 隐藏菜单
  hideContextMenu()

  // 打开Mermaid对话框
  console.log('打开Mermaid对话框')
  showMermaidDialog.value = true
  mermaidCode.value = ''
  mermaidStats.value = {
    paths_count: 0,
    nodes_count: 0,
    edges_count: 0
  }

  try {
    generatingPlan.value = true
    console.log('调用API生成Mermaid...')
    const result = await neo4jStore.convertToMermaid(nodeData.name)
    
    console.log('API返回结果:', result)
    mermaidCode.value = result.mermaid
    mermaidStats.value = result.stats
    
    ElMessage.success('Plan 生成成功')
  } catch (error: any) {
    console.error('生成 Plan 失败:', error)
    ElMessage.error(error.message || '生成 Plan 失败')
    showMermaidDialog.value = false
  } finally {
    generatingPlan.value = false
    console.log('生成完成，对话框状态:', showMermaidDialog.value)
  }
}

// 复制 Mermaid 代码
const copyMermaidCode = async () => {
  try {
    await navigator.clipboard.writeText(mermaidCode.value)
    ElMessage.success('Mermaid 代码已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

// 从上下文菜单生成JSON Plan
const generateJsonPlanFromContext = async () => {
  const nodeData = contextMenu.value.data as NodeData
  if (!nodeData) {
    console.error('节点数据为空')
    return
  }

  console.log('开始生成JSON Plan，节点:', nodeData.name, '标签:', nodeData.label)

  // 隐藏菜单
  hideContextMenu()

  // 打开JSON Plan对话框
  console.log('打开JSON Plan对话框')
  showJsonPlanDialog.value = true
  jsonPlanData.value = null

  try {
    generatingPlan.value = true
    console.log('调用API生成JSON Plan...')
    const result = await neo4jStore.convertToJson(nodeData.name)
    
    console.log('API返回结果:', result)
    jsonPlanData.value = result
    
    ElMessage.success('JSON Plan 生成成功')
  } catch (error: any) {
    console.error('生成 JSON Plan 失败:', error)
    ElMessage.error(error.message || '生成 JSON Plan 失败')
    showJsonPlanDialog.value = false
  } finally {
    generatingPlan.value = false
    console.log('生成完成，对话框状态:', showJsonPlanDialog.value)
  }
}

// 复制 JSON Plan 代码
const copyJsonPlanCode = async () => {
  try {
    if (!jsonPlanData.value) return
    const jsonString = JSON.stringify(jsonPlanData.value, null, 2)
    await navigator.clipboard.writeText(jsonString)
    ElMessage.success('JSON Plan 已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

// 从上下文菜单复制节点
const copyNodeFromContext = async () => {
  const nodeData = contextMenu.value.data as NodeData
  if (!nodeData) return

  // 隐藏菜单
  hideContextMenu()

  try {
    // 第一步：获取本节点的完整信息
    console.log('复制节点 - 第一步：获取节点信息', nodeData)

    // 第二步：填充节点表单并弹窗
    nodeForm.value = {
      name: nodeData.name, // 复制的节点名称（用户可修改）
      label: nodeData.label,
      properties: Object.entries(nodeData.properties || {}).map(([key, value]) => ({
        key,
        value: String(value)
      }))
    }

    // 设置新节点的初始位置（在原节点基础上向右下偏移50像素）
    if (nodeData.x !== undefined && nodeData.y !== undefined) {
      newNodePosition.value = {
        x: nodeData.x + 50,
        y: nodeData.y + 50
      }
      console.log('复制节点 - 设置初始位置:', newNodePosition.value)
    }

    console.log('复制节点 - 第二步：打开创建节点弹窗，内容已填充')
    showCreateNodeDialog.value = true
  } catch (error) {
    console.error('复制节点失败:', error)
    ElMessage.error('复制节点失败')
  }
}

// 从上下文菜单删除节点
const deleteNodeFromContext = async () => {
  const nodeData = contextMenu.value.data as NodeData
  if (!nodeData) return

  // 先隐藏右键菜单,避免与确认对话框遮挡
  hideContextMenu()

  try {
    deleting.value = true
    await neo4jStore.deleteNode({
      name: nodeData.name,
      label: nodeData.label
    })
    
    ElMessage.success('节点删除成功')
    await loadGraphData()
  } catch (error) {
    console.error('删除节点失败:', error)
    ElMessage.error('删除节点失败')
  } finally {
    deleting.value = false
  }
}

// 从上下文菜单删除关系
const deleteLinkFromContext = async () => {
  const linkData = contextMenu.value.data as any
  if (!linkData) return

  try {
    // 检查是否有 relationship id(用于精确匹配单条关系)
    const relationshipId = linkData.properties?._id
    
    if (!relationshipId) {
      ElMessage.warning('无法确定要删除的关系,请刷新后重试')
      return
    }
    
    // 先隐藏右键菜单,避免与确认对话框遮挡
    hideContextMenu()
    
    // 确认删除
    await ElMessageBox.confirm(
      `确定要删除此关系吗?\n类型: ${linkData.type}\nID: ${relationshipId}`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    deleting.value = true
    
    // 调用新的 API，通过 relationship ID 精确删除
    await neo4jStore.deleteRelationshipById(relationshipId)
    
    // 删除成功后,从本地图数据中移除这条特定的关系
    // 使用 _id 精确匹配,避免删除其他相同方向的关系
    const indexToRemove = graphData.links.findIndex(link => {
      const props = link.properties as any
      return props?._id === relationshipId
    })
    
    if (indexToRemove !== -1) {
      graphData.links.splice(indexToRemove, 1)
      updateGraph()
    }
    
    ElMessage.success('关系删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除关系失败:', error)
      ElMessage.error('删除关系失败')
      // 如果删除失败,重新加载数据以保持一致性
      await loadGraphData()
    }
  } finally {
    deleting.value = false
  }
}

// 重置表单
const resetNodeForm = () => {
  nodeForm.value = {
    name: '',
    label: '',
    properties: []
  }
  // 也清空节点位置（如果对话框被取消）
  newNodePosition.value = null
  // 重置更新标记
  updatingNode.value = false
}

const resetRelationForm = () => {
  relationForm.value = {
    fromNode: { label: '', name: '' },
    toNode: { label: '', name: '' },
    relationshipType: '',
    properties: []
  }
  fromNodeOptions.value = []
  toNodeOptions.value = []
  // 重置更新标记
  updatingRelationship.value = false
}

const resetCanvasForm = () => {
  canvasForm.value = {
    name: '',
    description: ''
  }
}

// 刷新图谱
const refreshGraph = () => {
  loadGraphData()
}

// 适应屏幕
const fitToScreen = () => {
  if (!svg) return
  
  const bounds = svg.select('.graph-group').node()?.getBBox()
  if (!bounds) return

  const width = graphContainer.value!.clientWidth
  const height = graphContainer.value!.clientHeight
  const midX = bounds.x + bounds.width / 2
  const midY = bounds.y + bounds.height / 2
  
  const scale = 0.9 / Math.max(bounds.width / width, bounds.height / height)
  const translate = [width / 2 - scale * midX, height / 2 - scale * midY]

  svg.transition().duration(750).call(
    d3.zoom<SVGSVGElement, unknown>().transform,
    d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
  )
}

// 重置节点位置
const resetNodePositions = async () => {
  await clearNodePositions()
  ElMessage.success('节点位置已重置')
  // 重新加载图谱数据，让节点重新布局
  await loadGraphData()
}

// ==================== 画布管理方法 ====================

// 加载数据库列表
const loadDatabases = async () => {
  try {
    databases.value = await neo4jStore.getDatabases()
  } catch (error) {
    console.error('加载数据库列表失败:', error)
    ElMessage.error('加载画布列表失败')
  }
}

// 画布切换
const onCanvasChange = async (value: string) => {
  // 使用 'default' 作为默认画布
  neo4jStore.switchDatabase(value || 'default')
  await loadGraphData()
  ElMessage.success(`已切换到${value || 'default'}画布`)
}

// 创建画布
const createCanvas = async () => {
  if (!canvasFormRef.value) return

  try {
    await canvasFormRef.value.validate()
    creating.value = true

    await neo4jStore.createDatabase({
      name: canvasForm.value.name,
      description: canvasForm.value.description || undefined
    })

    ElMessage.success('画布创建成功')
    showCreateCanvasDialog.value = false
    resetCanvasForm()
    await loadDatabases()
    
    // 自动切换到新创建的画布
    currentCanvas.value = canvasForm.value.name
    neo4jStore.switchDatabase(canvasForm.value.name)
    await loadGraphData()
  } catch (error) {
    console.error('创建画布失败:', error)
    ElMessage.error('创建画布失败')
  } finally {
    creating.value = false
  }
}

// 确认删除画布
const confirmDeleteCanvas = async () => {
  if (!currentCanvas.value || currentCanvas.value === 'default') {
    ElMessage.warning('无法删除 default 画布')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除画布 "${currentCanvas.value}" 吗？删除前请确保该画布中没有数据。`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deleting.value = true
    await neo4jStore.deleteDatabase(currentCanvas.value)
    
    ElMessage.success('画布删除成功')
    currentCanvas.value = 'default' // 切换回 default
    await loadDatabases()
    await loadGraphData()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除画布失败:', error)
      ElMessage.error(error.message || '删除画布失败')
    }
  } finally {
    deleting.value = false
  }
}

// 组件挂载
onMounted(async () => {
  await nextTick()
  initGraph()
  await loadDatabases()
  await loadExistingData()
  await loadGraphData()
  
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeyDown)
})

// 监听键盘事件（ESC 取消连线创建）
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && linkCreationMode.value) {
    cancelLinkCreation()
    ElMessage.info('已取消创建关系')
  }
}

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

// 监听当前画布变化
watch(() => neo4jStore.currentDatabase, (newVal) => {
  currentCanvas.value = newVal || 'default'
})
</script>

<style scoped>
.knowledge-graph-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.toolbar {
  background: white;
  padding: 16px 20px;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.canvas-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.graph-canvas {
  flex: 1;
  background: #fafafa;
  position: relative;
  overflow: hidden;
}

.graph-canvas.link-creation-mode {
  cursor: crosshair;
}

.link-creation-hint {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(64, 158, 255, 0.9);
  color: white;
  padding: 12px 24px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 1000;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  animation: hint-fade-in 0.3s ease-out;
}

@keyframes hint-fade-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.link-creation-hint .el-icon {
  font-size: 18px;
}

.property-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.property-item:last-child {
  margin-bottom: 0;
}

:deep(.el-dialog__body) {
  max-height: 60vh;
  overflow-y: auto;
}

.context-menu {
  position: fixed;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  min-width: 160px;
}

.menu-content {
  padding: 8px 0;
}

.menu-header {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.label-tag {
  background: #ecf5ff;
  color: #409eff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.menu-item {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.menu-item:hover {
  background: #f5f7fa;
}

.menu-item .el-icon {
  font-size: 16px;
}

.node-detail {
  padding: 10px 0;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.mermaid-section {
  margin-top: 20px;
}

.mermaid-stats {
  margin: 10px 0;
}

.mermaid-container {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow: auto;
  margin: 10px 0;
}

.mermaid-code {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.mermaid-actions {
  display: flex;
  justify-content: flex-end;
}

.text-muted {
  color: #909399;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.loading-container p {
  margin-top: 16px;
  color: #606266;
  font-size: 14px;
}

.mermaid-preview {
  padding: 10px 0;
}

.node-detail {
  padding: 10px 0;
}

.properties-section {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0;
}

.property-tag {
  margin: 0 !important;
  padding: 6px 12px;
  font-size: 13px;
}

.empty-state {
  text-align: center;
  padding: 20px 0;
}

.json-plan-preview {
  padding: 10px 0;
}

.plan-stats {
  margin: 10px 0;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.nodes-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.node-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  background: #f5f7fa;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.node-content {
  background: white;
  border-radius: 4px;
  padding: 8px;
}

.edges-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edge-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  background: #f5f7fa;
}

.edge-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.edge-condition {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #dcdfe6;
}
</style>