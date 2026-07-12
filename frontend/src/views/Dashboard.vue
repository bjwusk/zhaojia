<template>
  <div>
    <el-card>
      <template #header><span>上传需求文档</span><el-button v-if="totalProjects > 3" size="small" text @click="toggleShowAll">{{ showAllProjects ? '??' : '????' }}</el-button></template>
      <div style="text-align:center;padding:30px 0;">
        <input ref="fileInputRef" type="file" accept=".pdf,.docx,.doc,.txt" style="display:none" @change="onFileSelected" @click="this.value=null" />
        <div style="border:2px dashed #d9d9d9;border-radius:8px;padding:50px 20px;cursor:pointer;background:#fafafa;" @click="triggerFileInput" @dragover.prevent @drop.prevent="onFileDropped">
          <el-icon :size="48" color="#409EFF"><UploadFilled /></el-icon>
          <div style="margin-top:12px;font-size:14px;color:#606266;">
            将可行性研究报告、设计文档等拖拽到此，或<em style="color:#409EFF;font-style:normal;">点击选择文件</em>
          </div>
          <div style="font-size:12px;color:#909399;margin-top:8px;">支持 PDF、DOCX、DOC、TXT 格式</div>
        </div>
        <div v-if="uploading" style="margin-top:16px;">
          <el-progress :percentage="uploadProgress" :stroke-width="6" striped />
          <span style="font-size:13px;color:#909399;">正在分析文档...</span>
        </div>
        <div v-if="uploadError" style="margin-top:12px;">
          <el-alert :title="uploadError" type="error" show-icon :closable="false" />
        </div>
      </div>
      <div v-if="analyzeResult" style="margin-top:8px;text-align:center;">
        <el-result icon="success" title="文档分析完成">
          <template #sub-title>
            <span>已识别文件名：<b>{{ analyzeResult.filename }}</b></span><br />
            <span>推荐项目名：<b>{{ analyzeResult.project_name || "(待填写)" }}</b></span><br />
            <span>识别类型：<el-tag size="small" :type="analyzeResult.estimate_type==='dev'?'primary':'success'">{{ analyzeResult.estimate_type==='dev'?'开发项目':'运维项目' }}</el-tag></span>
          </template>
          <template #extra>
            <el-button type="primary" size="large" @click="goToParams">继续到参数调整</el-button>
            <el-button text @click="resetUpload">重新选择文件</el-button>
          </template>
        </el-result>
        <div v-if="generatedFps && generatedFps.length" style="margin-top:4px;">
          <el-tag size="small" type="success" style="margin-bottom:4px;">已自动生成 {{ generatedFps.length }} 个功能点</el-tag>
          <div style="display:flex;gap:4px;justify-content:center;flex-wrap:wrap;">
            <el-tag v-for="fp in generatedFps.slice(0,8)" :key="fp.category+fp.description" size="small" hit>{{ fp.category }}:{{ fp.fp_name }}</el-tag>
            <el-tag v-if="generatedFps.length>8" size="small">+{{ generatedFps.length-8 }}</el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <el-card style="margin-top:16px;">
      <template #header><span>已有项目</span></template>
      <el-table :data="projects" v-loading="loading" stripe @row-click="goProject">
        <el-table-column prop="name" label="项目名称" min-width="160" />
        <el-table-column prop="industry" label="行业" width="80" />
        <el-table-column prop="estimate_type" label="类型" width="70">
          <template #default="s">
            <el-tag :type="s.row.estimate_type==='dev'?'primary':'success'" size="small">{{ s.row.estimate_type==='dev'?'开发':'运维' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region" label="地域" width="60" />
        <el-table-column prop="created_at" label="创建时间" width="140" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="s">
            <el-button text size="small" type="primary" @click.stop="$router.push('/step1/'+s.row.id)">参数</el-button>
            <el-button text size="small" type="primary" @click.stop="$router.push('/step2/'+s.row.id)">标注</el-button>
            <el-button text size="small" type="primary" @click.stop="$router.push('/step3/'+s.row.id)">清单</el-button>
            <el-button text size="small" type="success" @click.stop="$router.push('/step4/'+s.row.id)">造价</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import axios from "axios"

const router = useRouter()
const api = axios.create({ baseURL: "/api", timeout: 180000 })
const loading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref("")
const projects = ref([])
const totalProjects = ref(0)
const showAllProjects = ref(false)
const analyzeResult = ref(null)
const generatedFps = ref([])
const fileInputRef = ref(null)

onMounted(() => { loadProjects() })

async function loadProjects() {
  loading.value = true
  try {
    const res = await api.get("/project")
    totalProjects.value = (res.data.data || []).length
  projects.value = showAllProjects.value ? (res.data.data || []) : (res.data.data || []).slice(0, 3)
  } catch {} finally { loading.value = false }
}

function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (file) uploadFile(file)
}
function onFileDropped(e) {
  const file = e.dataTransfer?.files?.[0]
  if (file) uploadFile(file)
}
function resetUpload() {
  analyzeResult.value = null; uploadError.value = ""
  generatedFps.value = []
}

async function uploadFile(file) {
  uploading.value = true; uploadError.value = ""; analyzeResult.value = null
  uploadProgress.value = 30
  const formData = new FormData()
  formData.append("file", file)
  const savedKey = localStorage.getItem("zhaojia_deepseek_key") || ""
  if (savedKey) formData.append("api_key", savedKey)
  try {
    const res = await api.post("/upload/analyze", formData, {
      timeout: 300000,
      onUploadProgress: (p) => { uploadProgress.value = Math.round(30 + (p.loaded / (p.total || 1)) * 40) }
    })
    uploadProgress.value = 100
    const data = res.data
    if (data.code === 0) {
      analyzeResult.value = data.data
      sessionStorage.setItem("zhaojia_upload_name", data.data.project_name || "")
      sessionStorage.setItem("zhaojia_upload_type", data.data.estimate_type || "dev")
      sessionStorage.setItem("zhaojia_upload_text", data.data.text_content || "")
      sessionStorage.setItem("zhaojia_upload_filepath", data.data.saved_path || "")
      if (data.data.fp_items && data.data.fp_items.length) {
        generatedFps.value = data.data.fp_items
        sessionStorage.setItem("zhaojia_upload_fps", JSON.stringify(data.data.fp_items))
      }
    } else {
      uploadError.value = data.message || "文件分析失败"
    }
  } catch (e) {
    if (e.code === "ECONNABORTED") {
      uploadError.value = "上传超时，文件过大或服务器响应慢"
    } else if (e.response) {
      uploadError.value = "服务器错误：" + (e.response.data?.message || e.response.statusText)
    } else if (e.message === "Network Error") {
      uploadError.value = "网络连接失败，请确认后端已启动"
    } else {
      uploadError.value = "上传失败：" + e.message
    }
  } finally { uploading.value = false; uploadProgress.value = 0 }
}

function toggleShowAll() {
  showAllProjects.value = !showAllProjects.value
  loadProjects()
}

function goToParams() {
  router.push("/step1/new")
}

function triggerFileInput() { fileInputRef.value?.click() }
function goProject(row) { router.push("/step1/" + row.id) }
</script>

