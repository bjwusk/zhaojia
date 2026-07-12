<template>
  <div style="display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #304156 0%, #1f2d3d 100%);">
    <el-card style="width: 420px; padding: 20px;">
      <template #header>
        <div style="text-align: center;">
          <h2 style="margin: 0;">软件造价自动生成器</h2>
          <p style="color: #909399; margin: 8px 0 0 0; font-size: 13px;">北京软件造价评估技术创新联盟标准</p>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form ref="formRef" :model="form" label-width="0">
            <el-form-item><el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" /></el-form-item>
            <el-form-item><el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password /></el-form-item>
            <el-form-item><el-button type="primary" size="large" style="width:100%" @click="handleLogin" :loading="loading">登录</el-button></el-form-item>
          </el-form>
          <div style="text-align: right;">
            <el-button text type="primary" @click="activeTab='register'">没有账号？去注册</el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form ref="formRef" :model="form" label-width="0">
            <el-form-item><el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" /></el-form-item>
            <el-form-item><el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password /></el-form-item>
            <el-form-item><el-input v-model="form.display_name" placeholder="显示名称" prefix-icon="Edit" size="large" /></el-form-item>
            <el-form-item><el-input v-model="form.company" placeholder="所属单位" prefix-icon="OfficeBuilding" size="large" /></el-form-item>
            <el-form-item><el-button type="primary" size="large" style="width:100%" @click="handleRegister" :loading="loading">注册</el-button></el-form-item>
          </el-form>
          <div style="text-align: right;">
            <el-button text type="primary" @click="activeTab='login'">已有账号？去登录</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import axios from "axios"

const router = useRouter()
const api = axios.create({ baseURL: "/api" })
const activeTab = ref("login")
const loading = ref(false)
const form = ref({ username: "", password: "", display_name: "", company: "" })

async function handleLogin() {
  if (!form.value.username || !form.value.password) { ElMessage.warning("请输入用户名和密码"); return }
  loading.value = true
  try {
    const res = await api.post("/auth/login", { username: form.value.username, password: form.value.password })
    const data = res.data
    if (data.code === 0) {
      localStorage.setItem("zhaojia_token", data.token)
      localStorage.setItem("zhaojia_user", JSON.stringify(data.data))
      ElMessage.success("登录成功")
      router.push("/")
    } else {
      ElMessage.error(data.message || "登录失败")
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.message || "登录失败")
  } finally { loading.value = false }
}

async function handleRegister() {
  if (!form.value.username || !form.value.password) { ElMessage.warning("请输入用户名和密码"); return }
  loading.value = true
  try {
    const res = await api.post("/auth/register", {
      username: form.value.username, password: form.value.password,
      display_name: form.value.display_name || form.value.username,
      company: form.value.company || ""
    })
    if (res.data.code === 0) {
      ElMessage.success("注册成功，请登录")
      activeTab.value = "login"
    } else {
      ElMessage.error(res.data.message || "注册失败")
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.message || "注册失败")
  } finally { loading.value = false }
}
</script>