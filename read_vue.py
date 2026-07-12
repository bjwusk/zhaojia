<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>文件功能点标注</span>
          <div>
            <el-tag size="small" type="info" style="margin-right:8px;">
              {{ fpMethod === "estimated" ? "预估功能点法" : "预算功能点法" }}
            </el-tag>
            <el-button v-if="hasApiKey && !aiDone" type="success" size="default" @click="aiExtractContent" :loading="extracting" style="margin-right:8px;">
              <el-icon><Filter /></el-icon> AI提取建设内容
            </el-button>
            <el-button v-if="hasApiKey && !aiDone" type="warning" size="default" @click="confirmAndAnalyze" :loading="aiLoading" style="margin-right:8px;">
              <el-icon><Select /></el-icon> 确认并AI标注
            </el-button>
            <el-tag v-if="aiDone" type="success" size="default" style="margin-right:8px;">✓ 已标注 {{ fpItems.length }} 个功能点</el-tag>
            <el-button type="primary" size="default" @click="saveAndNext" :disabled="fpItems.length === 0">
              保存并查看清单 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <el-alert v-if="!hasApiKey" title="请先在设置中配置DeepSeek API Key，AI标注功能需要API Key" type="info" show-icon :closable="false" style="margin-bottom:12px;">
        <template #action><el-button size="small" text @click="$router.push('/settings')">去设置</el-button></template>
      </el-alert>
      <el-alert v-if="aiDone" title="AI标注完成！文档中的功能点已自动着色高亮" type="success" show-icon :closable="true" style="margin-bottom:12px;" />

      <div v-loading="loading">
        <el-row :gutter="12">
          <!-- 左侧 -->
          <el-col :span="14">
            <el-card shadow="never">
              <template #header>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span>文档内容 <span style="font-size:12px;color:#909399;">{{ aiDone ? "（已标注）" : "（可编辑）" }}</span></span>
                  <div style="display:flex;gap:4px;">
                    <el-tag size="small" v-for="item in legend" :key="item.key"
                      :style="{ background: item.color+'22', color: item.color, borderColor: item.color+'44' }">
                      {{ item.label }}
                    </el-tag>
                  </div>
                </div>
              </template>

              <!-- 编辑模式：textarea -->
              <div v-if="!aiDone">
                <el-input
                  ref="editorRef"
                  v-model="editText"
                  type="textarea"
                  :rows="20"
                  style="font-size:13px;line-height:1.8;font-family:'Microsoft YaHei',sans-serif;"
                  placeholder="暂无文档内容，请确认文档已正确上传..."
                />
                <div style="margin-top:4px;font-size:11px;color:#909399;display:flex;justify-content:space-between;">
                  <span>{{ editText.length }} 字符</span>
                  <el-button v-if="hasApiKey" text size="small" @click="aiExtractContent" :loading="extracting">AI提取建设内容</el-button>
                  <el-button text size="small" @click="resetToOriginal" :disabled="!rawText">恢复原文</el-button>
                </div>
              </div>

              <!-- 标注模式：高亮显示 -->
              <div v-else>
                <div style="max-height:600px;overflow-y:auto;white-space:pre-wrap;font-size:13px;line-height:1.8;padding:12px;background:#fafafa;border:1px solid #dcdfe6;border-radius:4px;font-family:'Microsoft YaHei',sans-serif;">
                  <span v-if="!displayHtml" style="color:#909399;">暂无内容</span>
                  <span v-else v-html="displayHtml"></span>
                </div>
                <div style="margin-top:4px;font-size:11px;color:#909399;">
                  {{ editText.length }} 字符 | {{ matchCount }} 处功能点匹配
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 右侧：功能点清单 -->
          <el-col :span="10">
            <el-card shadow="never">
              <template #header>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span>功能点清单（{{ fpItems.length }} 条）</span>
                  <div>
                    <el-button size="small" type="primary" plain @click="addFpRow" :disabled="!aiDone">添加</el-button>
                    <el-button size="small" @click="clearFpList" :disabled="!aiDone">清空</el-button>
                  </div>
                </div>
              </template>

              <!-- 提示 -->
              <div v-if="!aiDone && !loading" style="padding:30px;text-align:center;color:#909399;font-size:14px;">
                <el-icon :size="32" color="#dcdfe6"><Edit /></el-icon>
                <p style="margin-top:8px;">1. 点击「AI提取建设内容」提取核心建设方案</p>
                <p>2. 编辑左侧文本</p>
                <p>3. 点击「确认并AI标注」自动识别功能点</p>
              </div>

              <!-- 功能点表格 -->
              <el-table v-if="aiDone" :data="fpItems" border size="small" max-height="520" style="width:100%">
                <el-table-column label="#" width="32" type="index" />
                <el-table-column label="类别" width="60">
                  <template #default="s">
                    <el-select v-model="s.row.category" size="small" @change="()=>updateFpRow(s.row)">
                      <el-option v-for="c in fpCategories" :key="c" :label="c" :value="c" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="功能描述" min-width="110">
                  <template #default="s"><el-input v-model="s.row.description" size="small" /></template>
                </el-table-column>
                <el-table-column label="名称" width="70">
                  <template #default="s"><el-input v-model="s.row.fp_name" size="small" /></template>
                </el-table-column>
                <el-table-column label="UFP" width="45">
                  <template #default="s">{{ s.row.ufp }}</template>
                </el-table-column>
                <el-table-column label="操作" width="36">
                  <template #default="s"><el-button text size="small" type="danger" @click="deleteFpRow(s.$index)">×</el-button></template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import axios from "axios"

const props = defineProps({ projectId: { type: [String, Number], default: null } })
const route = useRoute()
const router = useRouter()
const api = axios.create({ baseURL: "/api", timeout: 120000 })

const editText = ref("")
const rawText = ref("")
const loading = ref(true)
const aiLoading = ref(false)
const extracting = ref(false)
const aiDone = ref(false)
const hasApiKey = ref(false)
const fpMethod = ref("estimated")
const matchCount = ref(0)
const fpItems = ref([])
const fpCategories = ["ILF","EIF","EI","EO","EQ"]
const highlightData = ref({})

const defaultColors = { ILF: "#E74C3C", EIF: "#E67E22", EI: "#3498DB", EO: "#2ECC71", EQ: "#9B59B6" }
const colorMap = ref({ ...defaultColors })

const legend = computed(() => [
  { key: "ILF", label: "ILF 内部逻辑文件", color: colorMap.value.ILF },
  { key: "EIF", label: "EIF 外部接口文件", color: colorMap.value.EIF },
  { key: "EI", label: "EI 外部输入", color: colorMap.value.EI },
  { key: "EO", label: "EO 外部输出", color: colorMap.value.EO },
  { key: "EQ", label: "EQ 外部查询", color: colorMap.value.EQ },
])

const displayHtml = computed(() => {
  const text = editText.value
  if (!text) return ""
  if (!aiDone.value || !fpItems.value.length) {
    return escapeHtml(text).replace(/\n/g, "<br>")
  }
  // Build highlight patterns from fpItems
  const patterns = []
  for (const fp of fpItems.value) {
    const cat = fp.category
    const color = colorMap.value[cat] || "#999"
    // Add description and name as highlight keywords
    const kws = [fp.fp_name, fp.description].filter(k => k && k.length >= 2)
    for (const kw of kws) {
      patterns.push({ cat, kw, color })
    }
  }
  if (!patterns.length) return escapeHtml(text).replace(/\n/g, "<br>")
  // Sort by keyword length descending
  patterns.sort((a, b) => b.kw.length - a.kw.length)
  let result = ""
  let remaining = text
  let count = 0
  while (remaining.length > 0) {
    let earliest = remaining.length, earliestMatch = null
    for (const p of patterns) {
      const idx = remaining.indexOf(p.kw)
      if (idx >= 0 && idx < earliest) { earliest = idx; earliestMatch = p }
    }
    if (earliestMatch && earliest < remaining.length) {
      if (earliest > 0) result += escapeHtml(remaining.substring(0, earliest))
      result += `<span style="color:${earliestMatch.color};font-weight:bold;background:${earliestMatch.color}18;">${escapeHtml(earliestMatch.kw)}</span>`
      count++
      remaining = remaining.substring(earliest + earliestMatch.kw.length)
    } else {
      result += escapeHtml(remaining)
      remaining = ""
    }
  }
  matchCount.value = count
  return result
})

function escapeHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
}

function resetToOriginal() { editText.value = rawText.value }

function addFpRow() { fpItems.value.push({ category: "ILF", description: "", fp_name: "", ufp: 35, subsystem: "", module_l1: "", complexity: "medium", reuse_level: "low", modify_type: "new" }) }
function deleteFpRow(idx) { fpItems.value.splice(idx, 1) }
function clearFpList() { fpItems.value = [] }
function updateFpRow(row) { row.ufp = ({ ILF: 35, EIF: 15, EI: 4, EO: 5, EQ: 4 })[row.category] || 4 }

async function aiExtractContent() {
  const pid = props.projectId || route.params.projectId
  const apiKey = localStorage.getItem("zhaojia_deepseek_key")
  if (!apiKey) { ElMessage.warning("请先在设置中配置DeepSeek API Key"); return }
  const text = editText.value || rawText.value
  if (!text || text.length < 30) { ElMessage.warning("文档内容过短"); return }
  extracting.value = true
  try {
    const res = await api.post("/fp/extract-content", {
      text: text.slice(0, 60000), api_key: apiKey
    }, { timeout: 120000 })
    if (res.data.code === 0 && res.data.data?.text) {
      editText.value = res.data.data.text
      ElMessage.success("建设内容提取完成，剩余 " + editText.value.length + " 字符")
    }
  } catch (e) {
    ElMessage.error("提取失败: " + (e.response?.data?.message || e.message))
  } finally { extracting.value = false }
}

async function confirmAndAnalyze() {
  const pid = props.projectId || route.params.projectId
  const apiKey = localStorage.getItem("zhaojia_deepseek_key")
  if (!apiKey) { ElMessage.warning("请先在设置中配置DeepSeek API Key"); return }
  const textToAnalyze = editText.value || rawText.value
  if (!textToAnalyze || textToAnalyze.length < 20) { ElMessage.warning("文档内容过短"); return }

  aiLoading.value = true
  try {
    // Save edited text
    try { await api.post("/project/" + pid + "/document", { text: textToAnalyze }) } catch {}

    // AI analyze
    const res = await api.post("/fp/analyze-highlight", {
      text: textToAnalyze.slice(0, 60000),
      api_key: apiKey,
      fp_method: fpMethod.value,
    }, { timeout: 120000 })

    if (res.data.code === 0) {
      const d = res.data.data
      fpItems.value = (d.items || []).map((item, idx) => ({ ...item, seq: idx + 1 }))
      highlightData.value = { ...(d.highlight_map || {}) }
      aiDone.value = true
      sessionStorage.setItem("zhaojia_fp_" + pid, JSON.stringify(fpItems.value))
      ElMessage.success("确认并标注完成！共识别 " + d.total + " 个功能点")
    } else {
      ElMessage.warning(res.data.message || "AI分析返回为空")
    }
  } catch (e) {
    ElMessage.error("AI分析失败: " + (e.response?.data?.message || e.message))
  } finally { aiLoading.value = false }
}

function saveAndNext() {
  const pid = props.projectId || route.params.projectId
  sessionStorage.setItem("zhaojia_fp_" + pid, JSON.stringify(fpItems.value))
  router.push("/step3/" + pid)
}

onMounted(async () => {
  const pid = props.projectId || route.params.projectId
  if (!pid) { router.push("/"); return }
  hasApiKey.value = !!localStorage.getItem("zhaojia_deepseek_key")
  try {
    const saved = localStorage.getItem("zhaojia_fp_colors")
    if (saved) colorMap.value = { ...defaultColors, ...JSON.parse(saved) }
  } catch {}
  const paramsStr = sessionStorage.getItem("zhaojia_params_" + pid)
  if (paramsStr) {
    try { const p = JSON.parse(paramsStr); if (p.form && p.form.fp_method) fpMethod.value = p.form.fp_method } catch {}
  }

  // Load full document text
  let text = ""
  try {
    const res = await api.get("/project/" + pid + "/document", { timeout: 30000 })
    if (res.data.code === 0 && res.data.data?.text) text = res.data.data.text
  } catch {}
  if (!text) text = sessionStorage.getItem("zhaojia_file_text_" + pid) || ""
  if (text) { rawText.value = text; editText.value = text }

  // Load stored FPs
  const stored = sessionStorage.getItem("zhaojia_fp_" + pid)
  if (stored) {
    try { const p = JSON.parse(stored); if (p.length) { fpItems.value = p; aiDone.value = true } } catch {}
  }
  loading.value = false
})
</script>