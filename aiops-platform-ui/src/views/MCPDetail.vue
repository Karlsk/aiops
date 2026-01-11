<template>
  <div class="mcp-detail-container">
    <!-- 返回按钮 -->
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="header-title">服务器详情</span>
      </template>
    </el-page-header>

    <!-- 服务器基本信息 -->
    <el-card class="info-card" shadow="never" v-loading="store.loading">
      <template #header>
        <div class="card-header">
          <span><el-icon><InfoFilled /></el-icon> 基本信息</span>
          <el-button-group>
            <el-button size="small" @click="showEditDialog">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </el-button-group>
        </div>
      </template>

      <el-descriptions :column="2" border v-if="server">
        <el-descriptions-item label="ID">{{ server.id }}</el-descriptions-item>
        <el-descriptions-item label="服务器名称">{{ server.name }}</el-descriptions-item>
        <el-descriptions-item label="服务器地址" :span="2">
          {{ server.url }}
        </el-descriptions-item>
        <el-descriptions-item label="传输方式">
          <el-tag :type="getTransportType(server.transport)">
            {{ getTransportLabel(server.transport) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述">
          {{ server.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatTime(server.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatTime(server.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 工具列表 -->
    <el-card class="tools-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span><el-icon><Tools /></el-icon> 可用工具</span>
          <el-button type="primary" size="small" @click="loadTools" :loading="loadingTools">
            <el-icon><RefreshRight /></el-icon>
            刷新工具列表
          </el-button>
        </div>
      </template>

      <el-table :data="tools" v-loading="loadingTools">
        <el-table-column prop="name" label="工具名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="300" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showToolDialog(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="tools.length === 0 && !loadingTools" description="暂无工具数据" />
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑 MCP 服务器"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
      >
        <el-form-item label="服务器名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入服务器名称" />
        </el-form-item>

        <el-form-item label="服务器地址" prop="url">
          <el-input v-model="editForm.url" placeholder="例如: http://localhost:8000/mcp" />
        </el-form-item>

        <el-form-item label="传输方式" prop="transport">
          <el-select v-model="editForm.transport" placeholder="请选择传输方式" style="width: 100%">
            <el-option label="HTTP Stream" value="streamable_http" />
            <el-option label="Standard IO" value="stdio" />
            <el-option label="Server-Sent Events" value="sse" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入服务器描述（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="store.loading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 工具详情对话框 -->
    <el-dialog
      v-model="toolDialogVisible"
      title="工具详情"
      width="700px"
    >
      <div v-if="currentTool" class="tool-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="工具名称">
            {{ currentTool.name }}
          </el-descriptions-item>
          <el-descriptions-item label="描述">
            {{ currentTool.description }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentTool.args_schema" class="args-schema">
          <h4>参数定义</h4>
          <pre>{{ JSON.stringify(currentTool.args_schema, null, 2) }}</pre>
        </div>

        <el-form
          ref="callFormRef"
          :model="callForm"
          label-width="120px"
          class="tool-call-form"
        >
          <el-form-item label="工具参数">
            <el-input
              v-model="callForm.arguments"
              type="textarea"
              :rows="5"
              placeholder="请输入 JSON 格式的参数"
            />
          </el-form-item>
        </el-form>

        <el-button type="primary" @click="callTool" :loading="callingTool">
          <el-icon><Connection /></el-icon>
          调用工具
        </el-button>

        <div v-if="callResult" class="call-result">
          <h4>执行结果</h4>
          <pre>{{ JSON.stringify(callResult, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useMCPStore, type MCPServer, type Tool, type MCPServerUpdate } from '@/stores/mcp'

const route = useRoute()
const router = useRouter()
const store = useMCPStore()

const serverId = computed(() => parseInt(route.params.id as string))
const server = computed(() => store.currentServer)

const tools = ref<Tool[]>([])
const loadingTools = ref(false)
const editDialogVisible = ref(false)
const toolDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const callFormRef = ref<FormInstance>()
const currentTool = ref<Tool | null>(null)
const callResult = ref<any>(null)
const callingTool = ref(false)

const editForm = reactive<MCPServerUpdate>({
  name: '',
  url: '',
  transport: 'streamable_http',
  description: ''
})

const callForm = reactive({
  arguments: '{}'
})

const editRules: FormRules = {
  name: [
    { required: true, message: '请输入服务器名称', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' }
  ],
  transport: [
    { required: true, message: '请选择传输方式', trigger: 'change' }
  ]
}

const getTransportLabel = (transport: string) => {
  const labels: Record<string, string> = {
    'streamable_http': 'HTTP Stream',
    'stdio': 'Standard IO',
    'sse': 'Server-Sent Events'
  }
  return labels[transport] || transport
}

const getTransportType = (transport: string) => {
  const types: Record<string, any> = {
    'streamable_http': 'success',
    'stdio': 'info',
    'sse': 'warning'
  }
  return types[transport] || 'info'
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const goBack = () => {
  router.push('/mcp')
}

const showEditDialog = () => {
  if (!server.value) return
  
  Object.assign(editForm, {
    name: server.value.name,
    url: server.value.url,
    transport: server.value.transport,
    description: server.value.description || ''
  })
  editDialogVisible.value = true
}

const handleEdit = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await store.updateServer(serverId.value, editForm)
        await store.fetchServer(serverId.value)
        ElMessage.success('更新成功')
        editDialogVisible.value = false
      } catch (error: any) {
        ElMessage.error(error.message || '更新失败')
      }
    }
  })
}

const loadTools = async () => {
  try {
    loadingTools.value = true
    tools.value = await store.fetchTools(serverId.value)
    ElMessage.success('工具列表刷新成功')
  } catch (error: any) {
    ElMessage.error(error.message || '加载工具失败')
  } finally {
    loadingTools.value = false
  }
}

const showToolDialog = (tool: Tool) => {
  currentTool.value = tool
  callResult.value = null
  callForm.arguments = '{}'
  toolDialogVisible.value = true
}

const callTool = async () => {
  try {
    if (!currentTool.value) return

    // 验证 JSON 格式
    let args: Record<string, any> = {}
    try {
      args = JSON.parse(callForm.arguments)
    } catch {
      ElMessage.error('参数必须是有效的 JSON 格式')
      return
    }

    callingTool.value = true
    callResult.value = await store.callTool(serverId.value, currentTool.value.name, args)
    ElMessage.success('工具调用成功')
  } catch (error: any) {
    ElMessage.error(error.message || '调用工具失败')
  } finally {
    callingTool.value = false
  }
}

const loadData = async () => {
  try {
    await store.fetchServer(serverId.value)
    await loadTools()
  } catch (error: any) {
    ElMessage.error(error.message || '加载数据失败')
  }
}

onMounted(async () => {
  await loadData()
})
</script>

<style scoped>
.mcp-detail-container {
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

.info-card, .tools-card {
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

.tool-detail {
  min-height: 400px;
}

.args-schema {
  margin-top: 20px;
  margin-bottom: 20px;
}

.args-schema h4 {
  margin-bottom: 10px;
}

.args-schema pre {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.5;
}

.tool-call-form {
  margin-top: 20px;
  margin-bottom: 20px;
}

.call-result {
  margin-top: 20px;
}

.call-result h4 {
  margin-bottom: 10px;
}

.call-result pre {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.5;
}
</style>
