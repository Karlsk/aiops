<template>
  <div class="controller-detail-container">
    <!-- 返回按钮 -->
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="header-title">控制器详情</span>
      </template>
    </el-page-header>

    <!-- 控制器基本信息 -->
    <el-card class="info-card" shadow="never" v-loading="store.loading">
      <template #header>
        <div class="card-header">
          <span><el-icon><InfoFilled /></el-icon> 基本信息</span>
          <el-button-group>
            <el-button size="small" @click="testConnection">
              <el-icon><Connection /></el-icon>
              测试连接
            </el-button>
            <el-button size="small" @click="showEditDialog">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </el-button-group>
        </div>
      </template>

      <el-descriptions :column="2" border v-if="controller">
        <el-descriptions-item label="ID">{{ controller.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ controller.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag>{{ getControllerTypeLabel(controller.type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(controller.status)">
            {{ getStatusLabel(controller.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="主机地址">
          {{ controller.host }}:{{ controller.port }}
        </el-descriptions-item>
        <el-descriptions-item label="用户名">
          {{ controller.username || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatTime(controller.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatTime(controller.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 快照管理 -->
    <el-card class="snapshot-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span><el-icon><Camera /></el-icon> 拓扑快照</span>
          <el-button type="primary" size="small" @click="syncSnapshot" :loading="syncing">
            <el-icon><RefreshRight /></el-icon>
            同步快照
          </el-button>
        </div>
      </template>

      <el-table :data="store.snapshots" v-loading="loadingSnapshots">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="snapshot_time" label="快照时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.snapshot_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="database_name" label="数据库名称" width="150" />
        <el-table-column prop="node_count" label="节点数" width="100" />
        <el-table-column prop="link_count" label="连接数" width="100" />
        <el-table-column label="拓扑信息" min-width="200">
          <template #default="{ row }">
            <span>{{ row.node_count }} 个节点，{{ row.link_count }} 条连接</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="viewSnapshot(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button size="small" type="danger" @click="deleteSnapshot(row.id)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="store.snapshots.length === 0 && !loadingSnapshots" description="暂无快照数据" />
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑控制器"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
      >
        <el-form-item label="控制器名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入控制器名称" />
        </el-form-item>

        <el-form-item label="主机地址" prop="host">
          <el-input v-model="editForm.host" placeholder="IP地址或域名" />
        </el-form-item>

        <el-form-item label="端口" prop="port">
          <el-input-number v-model="editForm.port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>

        <el-divider>更新认证信息（可选）</el-divider>

        <el-form-item label="认证方式">
          <el-radio-group v-model="editAuthType">
            <el-radio label="password">用户名密码</el-radio>
            <el-radio label="token">API令牌</el-radio>
            <el-radio label="none">不修改</el-radio>
          </el-radio-group>
        </el-form-item>

        <template v-if="editAuthType === 'password'">
          <el-form-item label="用户名">
            <el-input v-model="editForm.username" placeholder="请输入用户名" />
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="editForm.password"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>
        </template>

        <template v-if="editAuthType === 'token'">
          <el-form-item label="API令牌">
            <el-input
              v-model="editForm.api_token"
              type="textarea"
              :rows="3"
              placeholder="请输入新的API令牌"
            />
          </el-form-item>
        </template>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="store.loading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看快照对话框 -->
    <el-dialog
      v-model="snapshotDialogVisible"
      title="查看快照"
      width="80%"
      top="5vh"
    >
      <div v-if="currentSnapshot" class="snapshot-content">
        <el-descriptions :column="3" border class="snapshot-info">
          <el-descriptions-item label="快照时间">
            {{ formatTime(currentSnapshot.snapshot_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="节点数">
            {{ currentSnapshot.node_count }}
          </el-descriptions-item>
          <el-descriptions-item label="连接数">
            {{ currentSnapshot.link_count }}
          </el-descriptions-item>
          <el-descriptions-item label="数据库名称" :span="3">
            {{ currentSnapshot.database_name }}
          </el-descriptions-item>
        </el-descriptions>

        <el-tabs v-model="activeTab" class="snapshot-tabs">
          <el-tab-pane label="拓扑可视化" name="visual">
            <div class="topology-container">
              <div v-if="snapshotGraphData" class="graph-toolbar">
                <el-tag>节点: {{ snapshotGraphData.nodes.length }}</el-tag>
                <el-tag style="margin-left: 10px">关系: {{ snapshotGraphData.relationships.length }}</el-tag>
                <el-button size="small" @click="fitToScreen" style="margin-left: 10px">
                  <el-icon><FullScreen /></el-icon>
                  适应屏幕
                </el-button>
                <el-button size="small" @click="resetVisualization">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
              </div>
              <div ref="topologyCanvas" class="topology-canvas" v-loading="loadingGraphData">
                <div v-if="!snapshotGraphData" class="empty-state">
                  <el-empty description="正在加载拓扑数据..." />
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="节点列表" name="nodes">
            <el-table :data="snapshotGraphData?.nodes || []" max-height="400" v-loading="loadingGraphData">
              <el-table-column prop="name" label="节点名称" width="200" />
              <el-table-column prop="label" label="标签" width="120" />
              <el-table-column label="属性" min-width="300">
                <template #default="{ row }">
                  <el-tag v-for="(value, key) in row.properties" :key="key" class="property-tag">
                    {{ key }}: {{ value }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!snapshotGraphData?.nodes || snapshotGraphData.nodes.length === 0" description="暂无节点数据" />
          </el-tab-pane>

          <el-tab-pane label="关系列表" name="relationships">
            <el-table :data="snapshotGraphData?.relationships || []" max-height="400" v-loading="loadingGraphData">
              <el-table-column label="源节点" width="200">
                <template #default="{ row }">
                  {{ row.from_node.label }}:{{ row.from_node.name }}
                </template>
              </el-table-column>
              <el-table-column prop="relationship_type" label="关系类型" width="150" />
              <el-table-column label="目标节点" width="200">
                <template #default="{ row }">
                  {{ row.to_node.label }}:{{ row.to_node.name }}
                </template>
              </el-table-column>
              <el-table-column label="属性" min-width="300">
                <template #default="{ row }">
                  <el-tag v-for="(value, key) in row.relationship_properties" :key="key" class="property-tag">
                    {{ key }}: {{ value }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!snapshotGraphData?.relationships || snapshotGraphData.relationships.length === 0" description="暂无关系数据" />
          </el-tab-pane>

          <el-tab-pane label="JSON数据" name="json">
            <pre class="json-view">{{ JSON.stringify(snapshotGraphData || {}, null, 2) }}</pre>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useControllerStore, type ControllerUpdate, type TopologySnapshot } from '@/stores/controller'
import { useNeo4jStore } from '@/stores/neo4j'
import * as d3 from 'd3'

const route = useRoute()
const router = useRouter()
const store = useControllerStore()
const neo4jStore = useNeo4jStore()

const controllerId = computed(() => parseInt(route.params.id as string))
const controller = computed(() => store.currentController)

const editDialogVisible = ref(false)
const snapshotDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editAuthType = ref<'password' | 'token' | 'none'>('none')
const syncing = ref(false)
const loadingSnapshots = ref(false)
const currentSnapshot = ref<TopologySnapshot | null>(null)
const activeTab = ref('visual')
const snapshotGraphData = ref<any>(null)
const loadingGraphData = ref(false)
const topologyCanvas = ref<HTMLElement | null>(null)

// D3.js 相关变量
let svg: any = null
let simulation: any = null
let graphData: any = { nodes: [], links: [] }

const editForm = reactive<ControllerUpdate>({
  name: '',
  host: '',
  port: 8181,
  username: '',
  password: '',
  api_token: ''
})

const editRules: FormRules = {
  name: [
    { required: true, message: '请输入控制器名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' }
  ]
}

const getControllerTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    opendaylight: 'OpenDaylight',
    onos: 'ONOS',
    floodlight: 'Floodlight',
    ryu: 'Ryu',
    terra: 'Terra',
    custom: '自定义'
  }
  return labels[type] || type
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    active: 'success',
    inactive: 'info',
    error: 'danger',
    unknown: 'warning'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    active: '活跃',
    inactive: '非活跃',
    error: '错误',
    unknown: '未知'
  }
  return labels[status] || status
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const goBack = () => {
  router.push('/controllers')
}

const testConnection = async () => {
  try {
    const result = await store.testConnection(controllerId.value)
    if (result.status === 'success') {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(result.message || '连接测试失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '连接测试失败')
  }
}

const showEditDialog = () => {
  if (!controller.value) return
  
  Object.assign(editForm, {
    name: controller.value.name,
    host: controller.value.host,
    port: controller.value.port,
    username: controller.value.username || '',
    password: '',
    api_token: ''
  })
  editAuthType.value = 'none'
  editDialogVisible.value = true
}

const handleEdit = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const data: ControllerUpdate = {
          name: editForm.name,
          host: editForm.host,
          port: editForm.port
        }

        if (editAuthType.value === 'password') {
          data.username = editForm.username
          data.password = editForm.password
        } else if (editAuthType.value === 'token') {
          data.api_token = editForm.api_token
        }

        await store.updateController(controllerId.value, data)
        await store.fetchController(controllerId.value)
        ElMessage.success('更新成功')
        editDialogVisible.value = false
      } catch (error: any) {
        ElMessage.error(error.message || '更新失败')
      }
    }
  })
}

const syncSnapshot = async () => {
  try {
    syncing.value = true
    await store.syncSnapshot(controllerId.value)
    ElMessage.success('快照同步成功')
  } catch (error: any) {
    ElMessage.error(error.message || '同步快照失败')
  } finally {
    syncing.value = false
  }
}

const viewSnapshot = async (snapshot: TopologySnapshot) => {
  try {
    // 获取快照详情
    const fullSnapshot = await store.fetchSnapshot(controllerId.value, snapshot.id)
    currentSnapshot.value = fullSnapshot
    
    // 从 Neo4j 加载快照对应的数据
    loadingGraphData.value = true
    snapshotGraphData.value = null
    
    // 切换到快照数据库
    const previousDatabase = neo4jStore.currentDatabase
    neo4jStore.switchDatabase(fullSnapshot.database_name)
    
    try {
      // 获取节点和关系
      const [nodes, relationships] = await Promise.all([
        neo4jStore.getAllNodes(),
        neo4jStore.getAllRelationships()
      ])
      
      snapshotGraphData.value = {
        nodes,
        relationships
      }
      
      // 打开对话框
      activeTab.value = 'visual'
      snapshotDialogVisible.value = true
      
      // 等待DOM更新后初始化可视化
      await nextTick()
      initVisualization()
      
    } finally {
      // 恢复原来的数据库
      neo4jStore.switchDatabase(previousDatabase)
      loadingGraphData.value = false
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取快照详情失败')
  }
}

// 初始化可视化
const initVisualization = () => {
  if (!topologyCanvas.value || !snapshotGraphData.value) return
  
  // 清空画布
  d3.select(topologyCanvas.value).selectAll('*').remove()
  
  const width = topologyCanvas.value.clientWidth
  const height = 500
  
  // 创建SVG
  svg = d3.select(topologyCanvas.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
  
  // 添加缩放和拖动
  const g = svg.append('g')
  
  const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event: any) => {
      g.attr('transform', event.transform)
    })
  
  svg.call(zoom)
  
  // 定义箭头
  svg.append('defs').selectAll('marker')
    .data(['arrow'])
    .enter().append('marker')
    .attr('id', 'arrow')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('markerWidth', 12)
    .attr('markerHeight', 12)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5L3,0Z')
    .attr('fill', '#999')
  
  // 准备数据
  prepareGraphData()
  
  // 创建力导向图
  simulation = d3.forceSimulation(graphData.nodes)
    .force('link', d3.forceLink(graphData.links).id((d: any) => d.id).distance(150))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
  
  // 绘制连线
  const link = g.append('g')
    .selectAll('line')
    .data(graphData.links)
    .enter().append('line')
    .attr('stroke', '#999')
    .attr('stroke-width', 2)
    .attr('marker-end', 'url(#arrow)')
  
  // 绘制连线标签
  const linkLabel = g.append('g')
    .selectAll('text')
    .data(graphData.links)
    .enter().append('text')
    .attr('class', 'link-label')
    .attr('text-anchor', 'middle')
    .attr('font-size', '12px')
    .attr('fill', '#666')
    .text((d: any) => d.type)
  
  // 绘制节点
  const node = g.append('g')
    .selectAll('circle')
    .data(graphData.nodes)
    .enter().append('circle')
    .attr('r', 15)
    .attr('fill', (d: any) => getNodeColor(d.label))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended) as any
    )
  
  // 绘制节点标签
  const nodeLabel = g.append('g')
    .selectAll('text')
    .data(graphData.nodes)
    .enter().append('text')
    .attr('class', 'node-label')
    .attr('text-anchor', 'middle')
    .attr('dy', 25)
    .attr('font-size', '14px')
    .attr('fill', '#333')
    .text((d: any) => d.name)
  
  // 更新位置
  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)
    
    linkLabel
      .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
      .attr('y', (d: any) => (d.source.y + d.target.y) / 2)
    
    node
      .attr('cx', (d: any) => d.x)
      .attr('cy', (d: any) => d.y)
    
    nodeLabel
      .attr('x', (d: any) => d.x)
      .attr('y', (d: any) => d.y)
  })
}

// 准备图表数据
const prepareGraphData = () => {
  if (!snapshotGraphData.value) return
  
  // 转换节点
  graphData.nodes = snapshotGraphData.value.nodes.map((node: any) => ({
    id: `${node.label}:${node.name}`,
    name: node.name,
    label: node.label,
    properties: node.properties || {}
  }))
  
  // 转换连线
  graphData.links = snapshotGraphData.value.relationships.map((rel: any) => ({
    source: `${rel.from_node.label}:${rel.from_node.name}`,
    target: `${rel.to_node.label}:${rel.to_node.name}`,
    type: rel.relationship_type,
    properties: rel.relationship_properties || {}
  }))
}

// 获取节点颜色
const getNodeColor = (label: string) => {
  const colors: Record<string, string> = {
    'Event': '#67c23a',
    'Action': '#409eff',
    'Resource': '#e6a23c',
    'Person': '#f56c6c',
    'Location': '#909399',
    'default': '#909399'
  }
  return colors[label] || colors.default
}

// 拖动事件
const dragstarted = (event: any) => {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  event.subject.fx = event.subject.x
  event.subject.fy = event.subject.y
}

const dragged = (event: any) => {
  event.subject.fx = event.x
  event.subject.fy = event.y
}

const dragended = (event: any) => {
  if (!event.active) simulation.alphaTarget(0)
  event.subject.fx = null
  event.subject.fy = null
}

// 适应屏幕
const fitToScreen = () => {
  if (!svg || !graphData.nodes.length) return
  
  const bounds = svg.node().getBBox()
  const fullWidth = topologyCanvas.value?.clientWidth || 800
  const fullHeight = 500
  const width = bounds.width
  const height = bounds.height
  const midX = bounds.x + width / 2
  const midY = bounds.y + height / 2
  
  const scale = 0.9 / Math.max(width / fullWidth, height / fullHeight)
  const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY]
  
  svg.transition().duration(750).call(
    d3.zoom().transform as any,
    d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
  )
}

// 重置可视化
const resetVisualization = () => {
  if (simulation) {
    simulation.alpha(1).restart()
  }
}

const deleteSnapshot = async (snapshotId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除此快照吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await store.deleteSnapshot(controllerId.value, snapshotId)
    ElMessage.success('删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const loadData = async () => {
  try {
    await store.fetchController(controllerId.value)
    
    loadingSnapshots.value = true
    await store.fetchSnapshots(controllerId.value)
  } catch (error: any) {
    ElMessage.error(error.message || '加载数据失败')
  } finally {
    loadingSnapshots.value = false
  }
}

onMounted(async () => {
  await loadData()
})
</script>

<style scoped>
.controller-detail-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.header-title {
  font-size: 20px;
  font-weight: bold;
}

.info-card, .snapshot-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.snapshot-content {
  min-height: 500px;
}

.snapshot-info {
  margin-bottom: 20px;
}

.snapshot-tabs {
  margin-top: 20px;
}

.topology-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.graph-toolbar {
  display: flex;
  align-items: center;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 10px;
}

.topology-canvas {
  width: 100%;
  height: 500px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  position: relative;
  overflow: hidden;
}

.topology-canvas :deep(svg) {
  width: 100%;
  height: 100%;
}

.topology-canvas .empty-state {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.topology-canvas :deep(.node-label) {
  pointer-events: none;
  user-select: none;
  font-weight: 500;
}

.topology-canvas :deep(.link-label) {
  pointer-events: none;
  user-select: none;
}

.property-tag {
  margin-right: 8px;
  margin-bottom: 4px;
}

.json-view {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.5;
}
</style>
