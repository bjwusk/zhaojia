<template>
  <el-card>
    <template #header><span>用户设置</span></template>
    <el-tabs>
      <el-tab-pane label="个人信息">
        <el-form v-if="user" :model="user" label-width="100px" style="max-width:500px;">
          <el-form-item label="用户名"><el-input v-model="user.username" disabled /></el-form-item>
          <el-form-item label="显示名称"><el-input v-model="user.display_name" /></el-form-item>
          <el-form-item label="所属单位"><el-input v-model="user.company" /></el-form-item>
          <el-form-item label="资质编号"><el-input v-model="user.cert_no" /></el-form-item>
          <el-form-item label="新密码"><el-input v-model="newPassword" type="password" show-password placeholder="留空不修改" /></el-form-item>
          <el-form-item><el-button type="primary" @click="saveProfile" :loading="saving">保存</el-button></el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="功能点颜色">
        <p style="color:#909399;font-size:13px;margin-bottom:16px;">
          设置文件标注步骤中各类功能点的显示颜色
        </p>
        <el-form label-width="160px" style="max-width:500px;">
          <el-form-item v-for="item in fpColorItems" :key="item.key" :label="item.label">
            <div style="display:flex;align-items:center;gap:12px;">
              <div :style="{ width:'24px', height:'24px', borderRadius:'4px', background: fpColors[item.key], border:'1px solid #ddd' }"></div>
              <el-color-picker v-model="fpColors[item.key]" show-alpha />
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveColors">保存颜色设置</el-button>
            <el-button @click="resetColors">恢复默认</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="DeepSeek AI">
        <p style="color:#909399;font-size:13px;margin-bottom:16px;">
          配置 DeepSeek API Key 后，系统将使用 AI 自动识别需求文档中的功能点。
        </p>
        <el-form label-width="160px" style="max-width:600px;">
          <el-form-item label="API Key">
            <div style="display:flex;gap:8px;width:100%;">
              <el-input v-model="deepseekKey" type="password" show-password placeholder="sk-..." style="flex:1;" />
              <el-button type="primary" @click="saveDeepSeekKey">保存</el-button>
            </div>
          </el-form-item>
          <el-form-item label="模型名称">
            <el-select v-model="deepseekModel" style="width:200px;">
              <el-option label="deepseek-chat" value="deepseek-chat" />
              <el-option label="deepseek-reasoner" value="deepseek-reasoner" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button @click="testDeepSeek" :loading="testing">测试连接</el-button>
            <span v-if="testResult" :style="{ color: testResult.ok ? '#67C23A' : '#F56C6C', marginLeft: '12px', fontSize: '13px' }">
              {{ testResult.msg }}
            </span>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="关于">
        <h4>软件造价自动生成器 v1.0</h4>
        <p>基于北京软件造价评估技术创新联盟（BSCEA）官方标准</p>
        <p>数据来源：中国软件行业基准数据 CSBMK®-202510</p>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue"
import { ElMessage } from "element-plus"
import axios from "axios"

const api = axios.create({ baseURL: "/api" })
const user = ref(null)
const deepseekKey = ref(localStorage.getItem("zhaojia_deepseek_key") || "")
const deepseekModel = ref(localStorage.getItem("zhaojia_deepseek_model") || "deepseek-chat")
const testing = ref(false)
const testResult = ref(null)
const newPassword = ref("")
const saving = ref(false)

const defaultColors = {
  ILF: "#E74C3C", EIF: "#E67E22", EI: "#3498DB", EO: "#2ECC71", EQ: "#9B59B6"
}

const fpColors = reactive({ ...defaultColors })

const fpColorItems = [
  { key: "ILF", label: "ILF 内部逻辑文件" },
  { key: "EIF", label: "EIF 外部接口文件" },
  { key: "EI", label: "EI 外部输入" },
  { key: "EO", label: "EO 外部输出" },
  { key: "EQ", label: "EQ 外部查询" },
]

onMounted(() => {
  const u = JSON.parse(localStorage.getItem("zhaojia_user") || "null")
  if (u) user.value = { ...u }
  const saved = localStorage.getItem("zhaojia_fp_colors")
  if (saved) {
    const parsed = JSON.parse(saved)
    Object.keys(defaultColors).forEach(k => { if (parsed[k]) fpColors[k] = parsed[k] })
  }
})

async function saveProfile() {
  saving.value = true
  try {
    const data = { id: user.value.id, display_name: user.value.display_name, company: user.value.company, cert_no: user.value.cert_no }
    if (newPassword.value) data.password = newPassword.value
    const res = await api.put("/auth/profile", data)
    localStorage.setItem("zhaojia_user", JSON.stringify(res.data.data))
    ElMessage.success("保存成功")
  } catch (e) { ElMessage.error("保存失败") }
  finally { saving.value = false }
}

function saveColors() {
  localStorage.setItem("zhaojia_fp_colors", JSON.stringify({ ...fpColors }))
  ElMessage.success("颜色设置已保存")
}

function resetColors() {
  Object.assign(fpColors, defaultColors)
  localStorage.setItem("zhaojia_fp_colors", JSON.stringify({ ...defaultColors }))
  ElMessage.success("已恢复默认颜色")
}

function saveDeepSeekKey() {
  if (!deepseekKey.value || !deepseekKey.value.startsWith("sk-")) {
    ElMessage.warning("请输入有效的 DeepSeek API Key（以 sk- 开头）")
    return
  }
  localStorage.setItem("zhaojia_deepseek_key", deepseekKey.value)
  localStorage.setItem("zhaojia_deepseek_model", deepseekModel.value)
  ElMessage.success("DeepSeek 配置已保存")
}

async function testDeepSeek() {
  if (!deepseekKey.value) { ElMessage.warning("请先输入 API Key"); return }
  testing.value = true
  testResult.value = null
  try {
    const res = await api.post("/fp/ai-generate", {
      text: "测试：项目名称：测试项目。内部逻辑文件存储用户数据。",
      api_key: deepseekKey.value,
      fp_method: "estimated"
    })
    if (res.data.code === 0) {
      testResult.value = { ok: true, msg: "连接成功！已识别 " + (res.data.data?.total || 0) + " 个功能点" }
    } else {
      testResult.value = { ok: false, msg: res.data.message || "连接失败" }
    }
  } catch (e) {
    testResult.value = { ok: false, msg: e.response?.data?.message || e.message }
  } finally { testing.value = false }
}
</script>
