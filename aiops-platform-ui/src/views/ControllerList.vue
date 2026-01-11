<template>
  <div class="controller-container">
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div class="title-section">
          <h2><el-icon><Monitor /></el-icon> SDN控制器管理</h2>
          <p>管理和监控第三方SDN控制器</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加控制器
          </el-button>
          <el-button @click="refreshList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 控制器列表 -->
    <el-card class="list-card" shadow="never" v-loading="store.loading">
      <el-table :data="store.controllers" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.id)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ getControllerTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="host" label="地址" min-width="200">
          <template #default="{ row }">
            {{ row.host }}:{{ row.port }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="testConnection(row.id)">
                <el-icon><Connection /></el-icon>
                测试
              </el-button>
              <el-button size="small" @click="goToDetail(row.id)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="store.controllers.length === 0 && !store.loading" description="暂无控制器数据" />
    </el-card>

    <!-- 创建控制器对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="添加SDN控制器"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="120px"
      >
        <el-form-item label="控制器名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入控制器名称" />
        </el-form-item>
        
        <el-form-item label="控制器类型" prop="type">
          <el-select v-model="createForm.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="OpenDaylight" value="opendaylight" />
            <el-option label="ONOS" value="onos" />
            <el-option label="Floodlight" value="floodlight" />
            <el-option label="Ryu" value="ryu" />
            <el-option label="Terra" value="terra" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item label="主机地址" prop="host">
          <el-input v-model="createForm.host" placeholder="IP地址或域名" />
        </el-form-item>

        <el-form-item label="端口" prop="port">
          <el-input-number v-model="createForm.port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>

        <el-divider>认证方式（二选一）</el-divider>

        <el-form-item label="认证方式">
          <el-radio-group v-model="authType">
            <el-radio label="password">用户名密码</el-radio>
            <el-radio label="token">API令牌</el-radio>
          </el-radio-group>
        </el-form-item>

        <template v-if="authType === 'password'">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="createForm.username" placeholder="请输入用户名" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="createForm.password"
              type="password"
              placeholder="请输入密码"
              show-password
            />
          </el-form-item>
        </template>

        <template v-if="authType === 'token'">
          <el-form-item label="API令牌" prop="api_token">
            <el-input
              v-model="createForm.api_token"
              type="textarea"
              :rows="3"
              placeholder="请输入API令牌"
            />
          </el-form-item>
        </template>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="store.loading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useControllerStore, type ControllerCreate } from '@/stores/controller'

const router = useRouter()
const store = useControllerStore()

const createDialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const authType = ref<'password' | 'token'>('password')

const createForm = reactive<ControllerCreate>({
  name: '',
  type: 'opendaylight',
  host: '',
  port: 8181,
  username: '',
  password: '',
  api_token: ''
})

const createRules: FormRules = {
  name: [
    { required: true, message: '请输入控制器名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择控制器类型', trigger: 'change' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号必须在 1-65535 之间', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur', validator: validateAuth }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur', validator: validateAuth }
  ],
  api_token: [
    { required: true, message: '请输入API令牌', trigger: 'blur', validator: validateAuth }
  ]
}

// 自定义认证验证
function validateAuth(rule: any, value: any, callback: any) {
  if (authType.value === 'password') {
    if (!createForm.username || !createForm.password) {
      callback(new Error('请输入用户名和密码'))
    } else {
      callback()
    }
  } else if (authType.value === 'token') {
    if (!createForm.api_token) {
      callback(new Error('请输入API令牌'))
    } else {
      callback()
    }
  }
  callback()
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

const showCreateDialog = () => {
  // 重置表单
  Object.assign(createForm, {
    name: '',
    type: 'opendaylight',
    host: '',
    port: 8181,
    username: '',
    password: '',
    api_token: ''
  })
  authType.value = 'password'
  createDialogVisible.value = true
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 根据认证类型构建请求数据
        const data: ControllerCreate = {
          name: createForm.name,
          type: createForm.type,
          host: createForm.host,
          port: createForm.port
        }

        if (authType.value === 'password') {
          data.username = createForm.username
          data.password = createForm.password
        } else {
          data.api_token = createForm.api_token
        }

        await store.createController(data)
        ElMessage.success('创建控制器成功')
        createDialogVisible.value = false
      } catch (error: any) {
        ElMessage.error(error.message || '创建失败')
      }
    }
  })
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除控制器 "${row.name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await store.deleteController(row.id)
    ElMessage.success('删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const testConnection = async (id: number) => {
  try {
    const result = await store.testConnection(id)
    if (result.status === 'success') {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(result.message || '连接测试失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '连接测试失败')
  }
}

const goToDetail = (id: number) => {
  router.push(`/controllers/${id}`)
}

const refreshList = async () => {
  try {
    await store.fetchControllers()
    ElMessage.success('刷新成功')
  } catch (error: any) {
    ElMessage.error(error.message || '刷新失败')
  }
}

onMounted(async () => {
  await store.fetchControllers()
})
</script>

<style scoped>
.controller-container {
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
