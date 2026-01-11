<template>
  <div id="app">
    <el-container style="height: 100vh">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-content">
          <div class="logo">
            <el-icon size="28"><Connection /></el-icon>
            <span class="logo-text">AIOps 网络运维平台</span>
          </div>
          <el-menu
            mode="horizontal"
            :default-active="activeMenu"
            class="nav-menu"
            @select="handleMenuSelect"
          >
            <el-menu-item index="/home">
              <el-icon><House /></el-icon>
              <span>主页</span>
            </el-menu-item>
            <el-menu-item index="/knowledge-graph">
              <el-icon><Share /></el-icon>
              <span>排障知识图谱</span>
            </el-menu-item>
            <el-menu-item index="/controllers">
              <el-icon><Monitor /></el-icon>
              <span>SDN控制器</span>
            </el-menu-item>
            <el-menu-item index="/mcp">
              <el-icon><Setting /></el-icon>
              <span>MCP 服务器</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-header>
      
      <!-- 主内容区域 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.path)

const handleMenuSelect = (index: string) => {
  router.push(index)
}
</script>

<style scoped>
.header {
  background: #ffffff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  margin-right: 40px;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  margin-left: 10px;
}

.nav-menu {
  border-bottom: none;
  flex: 1;
}

.main-content {
  padding: 0;
  background: #f5f5f5;
}

#app {
  font-family: 'Microsoft YaHei', sans-serif;
}
</style>