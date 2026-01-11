<template>
  <div class="mcp-container">
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div class="title-section">
          <h2><el-icon><Setting /></el-icon> MCP 服务器管理</h2>
          <p>管理 Model Context Protocol 服务器配置</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加服务器
          </el-button>
          <el-button @click="refreshList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 服务器列表 -->
    <el-card class="list-card" shadow="never" v-loading="store.loading">
      <el-table :data="store.servers" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="服务器名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.id)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="服务器地址" min-width="250" />
        <el-table-column prop="transport" label="传输方式" width="120">
          <template #default="{ row }">
            <el-tag :type="getTransportType(row.transport)">
              {{ getTransportLabel(row.transport) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="goToDetail(row.id)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button size="small" @click="showEditDialog(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="store.servers.length === 0 && !store.loading" description="暂无服务器数据" />
    </el-card>

    <!-- 创建/编辑服务器对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑 MCP 服务器' : '添加 MCP 服务器'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="服务器名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入服务器名称" />
        </el-form-item>
        
        <el-form-item label="服务器地址" prop="url">
          <el-input v-model="form.url" placeholder="例如: http://localhost:8000/mcp" />
        </el-form-item>

        <el-form-item label="传输方式" prop="transport">
          <el-select v-model="form.transport" placeholder="请选择传输方式" style="width: 100%">
            <el-option label="HTTP Stream" value="streamable_http" />
            <el-option label="Standard IO" value="stdio" />
            <el-option label="Server-Sent Events" value="sse" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入服务器描述（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="store.loading">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useMCPStore, type MCPServerCreate, type MCPServerUpdate, type MCPServer } from '@/stores/mcp'

const router = useRouter()
const store = useMCPStore()

const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number | null>(null)

const form = reactive<MCPServerCreate & Partial<MCPServerUpdate>>({
  name: '',
  url: '',
  transport: 'streamable_http',
  description: ''
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入服务器名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' },
    { type: 'url', message: '请输入正确的 URL', trigger: 'blur' }
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

const showCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, {
    name: '',
    url: '',
    transport: 'streamable_http',
    description: ''
  })
  dialogVisible.value = true
}

const showEditDialog = (row: MCPServer) => {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    url: row.url,
    transport: row.transport,
    description: row.description || ''
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEdit.value && editingId.value) {
          await store.updateServer(editingId.value, form as MCPServerUpdate)
          ElMessage.success('更新成功')
        } else {
          await store.createServer(form as MCPServerCreate)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
      } catch (error: any) {
        ElMessage.error(error.message || '操作失败')
      }
    }
  })
}

const handleDelete = async (row: MCPServer) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除服务器 "${row.name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await store.deleteServer(row.id)
    ElMessage.success('删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const goToDetail = (id: number) => {
  router.push(`/mcp/${id}`)
}

const refreshList = async () => {
  try {
    await store.fetchServers()
    ElMessage.success('刷新成功')
  } catch (error: any) {
    ElMessage.error(error.message || '刷新失败')
  }
}

onMounted(async () => {
  await store.fetchServers()
})
</script>

<style scoped>
.mcp-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h2 {
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
}

.title-section p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.action-section {
  display: flex;
  gap: 10px;
}

.list-card {
  min-height: 400px;
}
</style>
