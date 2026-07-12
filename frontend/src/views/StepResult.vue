<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>第四步：造价结果</span>
          <div>
            <el-button type="primary" size="default" @click="calculateCost" :loading="calculating" style="margin-right:8px;">
              <el-icon><DataAnalysis /></el-icon> 重新测算
            </el-button>
            <el-button type="success" size="default" @click="generateAndDownload" :loading="generating" :icon="Document">
              一键下载造价报告
            </el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading">
        <!-- 项目信息 -->
        <el-card shadow="never" style="margin-bottom:12px;">
          <el-descriptions :column="4" border size="small">
            <el-descriptions-item label="项目名称">{{ project?.name }}</el-descriptions-item>
            <el-descriptions-item label="行业">{{ project?.industry || params?.form?.industry }}</el-descriptions-item>
            <el-descriptions-item label="城市">{{ params?.form?.city }}</el-descriptions-item>
            <el-descriptions-item label="类型">
              <el-tag :type="project?.estimate_type==='dev'?'primary':'success'" size="small">
                {{ project?.estimate_type==="dev"?"开发项目":"运维项目" }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 造价摘要卡片 -->
        <el-row :gutter="12" style="margin-bottom:12px;">
          <el-col :span="6">
            <el-card shadow="never">
              <div style="text-align:center;">
                <div style="font-size:12px;color:#909399;">调整后功能点</div>
                <div style="font-size:28px;font-weight:bold;color:#409EFF;">{{ calc?.adjusted_fp || 0 }}</div>
                <div style="font-size:11px;color:#909399;">FP</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never">
              <div style="text-align:center;">
                <div style="font-size:12px;color:#909399;">人月数</div>
                <div style="font-size:28px;font-weight:bold;color:#67C23A;">{{ calc?.person_months || 0 }}</div>
                <div style="font-size:11px;color:#909399;">人月</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never">
              <div style="text-align:center;">
                <div style="font-size:12px;color:#909399;">人工费</div>
                <div style="font-size:28px;font-weight:bold;color:#E6A23C;">{{ calc?.labor_cost || 0 }}</div>
                <div style="font-size:11px;color:#909399;">万元</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="never" style="background:#fef0f0;">
              <div style="text-align:center;">
                <div style="font-size:12px;color:#909399;">总造价</div>
                <div style="font-size:28px;font-weight:bold;color:#F56C6C;">{{ totalCost }}</div>
                <div style="font-size:11px;color:#909399;">万元</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 指标分析 -->
        <el-card shadow="never" style="margin-bottom:12px;">
          <template #header><span>关键指标</span></template>
          <el-descriptions :column="4" border size="small">
            <el-descriptions-item label="万元/FP">{{ kpi.costPerFp }}</el-descriptions-item>
            <el-descriptions-item label="人月/FP">{{ kpi.pmPerFp }}</el-descriptions-item>
            <el-descriptions-item label="人均产出(万元/人月)">{{ kpi.outputPerPm }}</el-descriptions-item>
            <el-descriptions-item label="PDR">{{ calc?.pdr }} 人时/FP</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- BSCEA费用明细表 -->
        <el-card shadow="never" style="margin-bottom:12px;">
          <template #header><span>BSCEA费用测算明细表（与官方模板一致）</span></template>
          <el-table :data="feeRows" border size="small" style="max-width:920px;">
            <el-table-column label="费用项" width="250">
              <template #default="s">
                <span :style="s.row.isHeader ? 'font-weight:bold;font-size:14px;color:#303133;' : (s.row.bold ? 'font-weight:bold;color:#F56C6C;' : '')">{{ s.row.label }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额（万元）" width="140">
              <template #default="s">
                <span :style="s.row.bold ? 'font-weight:bold;color:#F56C6C;' : ''">{{ s.row.amount }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="说明" min-width="200" />
          </el-table>
          <div style="margin-top:8px;font-size:12px;color:#909399;">
            * Excel测算底稿和Word造价报告已自动保存，点击右上角"一键下载造价报告"下载完整压缩包
          </div>
        </el-card>

        <!-- 功能点清单 -->
        <el-card shadow="never">
          <template #header><span>功能点清单 ({{ items.length }} 条)</span></template>
          <el-table :data="items" border size="small" max-height="250">
            <el-table-column prop="seq" label="#" width="35" />
            <el-table-column prop="description" label="功能描述" min-width="140" />
            <el-table-column prop="category" label="类别" width="55" />
            <el-table-column prop="ufp" label="UFP" width="50" />
            <el-table-column prop="reuse_level" label="重用" width="55" />
            <el-table-column prop="modify_type" label="修改" width="50" />
            <el-table-column prop="us" label="US" width="50" />
          </el-table>
        </el-card>
      </div>
    </el-card>
  </div>
</template>


﻿<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { Document, DataAnalysis, ArrowRight } from "@element-plus/icons-vue"
import axios from "axios"

const props = defineProps({ projectId: { type: [String, Number], default: null } })
const route = useRoute()
const router = useRouter()
const api = axios.create({ baseURL: "/api" })

const loading = ref(true)
const generating = ref(false)
const project = ref(null)
const items = ref([])
const calc = ref(null)
const params = ref(null)
const zipPath = ref("")
const calculating = ref(false)

const totalCost = computed(() => {
  return calc.value?.cost_chain?.total || calc.value?.total_cost || calc.value?.labor_cost_median || 0
})

const kpi = computed(() => {
  const fp = calc.value?.adjusted_fp || 1
  const pm = calc.value?.person_months_median || 1
  const tc = totalCost.value
  return {
    costPerFp: fp > 0 ? (tc / fp).toFixed(4) : "0",
    pmPerFp: fp > 0 ? (pm / fp).toFixed(4) : "0",
    outputPerPm: pm > 0 ? (tc / pm).toFixed(4) : "0",
  }
})

const feeRows = computed(() => {
  const c = calc.value
  if (!c) return []
  const rows = [
    { label: "一、规模估算", isHeader: true, amount: "" },
    { label: "未调整功能点(UFP)", amount: (c.unadjusted_fp || 0).toFixed(2), note: "FP" },
    { label: "规模变更调整因子", amount: (c.scale_factor || 1).toFixed(4), note: "根据估算时机" },
    { label: "调整后功能点", amount: (c.adjusted_fp || 0).toFixed(2), note: "FP" },
    { label: "二、基准生产率", isHeader: true, amount: "" },
    { label: "基准生产率(PDR)", amount: (c.pdr_median || 0).toFixed(2), note: "人时/FP" },
    { label: "未调整工作量", amount: (c.workload_median || 0).toFixed(2), note: "人天" },
    { label: "三、调整因子", isHeader: true, amount: "" },
    { label: "应用类型", amount: (c.app_factor || 1).toFixed(4), note: "" },
    { label: "非功能性特征", amount: (c.nf_factor || 1).toFixed(4), note: "1+Sigma*0.025" },
    { label: "完整性级别", amount: (c.integrity_factor || 1).toFixed(4), note: "" },
    { label: "开发语言", amount: (c.language_factor || 1).toFixed(4), note: "" },
    { label: "团队背景", amount: (c.team_factor || 1).toFixed(4), note: "" },
    { label: "调整因子乘积", bold: true, amount: (c.adj_factor_product || 1).toFixed(4), note: "" },
    { label: "四、调整后工作量与报价", isHeader: true, amount: "" },
    { label: "调整后工作量", amount: (c.adj_workload_median || 0).toFixed(2), note: "人月" },
    { label: "人月数", amount: (c.person_months_median || 0).toFixed(2), note: "人月" },
    { label: "人月基准单价", amount: (c.unit_price || 0).toFixed(4), note: "万元/人月" },
    { label: "基准报价(人工费)", bold: true, amount: (c.labor_cost_median || 0).toFixed(2), note: "万元" },
  ]
  return rows
})

async function calculateCost() {
  const pid = props.projectId || route.params.projectId
  if (!items.value.length) { ElMessage.warning("请先录入功能点"); return }
  calculating.value = true
  try {
    const p = params.value?.form || {}
    const feeP = params.value?.feeForm || {}
    const docText = sessionStorage.getItem("zhaojia_file_text_" + pid) || ""
    const docFilename = sessionStorage.getItem("zhaojia_upload_name") || ""
    const reqData = {
      project_id: pid,
      project_name: project.value?.name || "软件项目",
      fp_items: items.value.map((r, i) => ({ ...r, seq: i + 1 })),
      doc_text: docText.slice(0, 2000),
      doc_filename: docFilename,
      params: { ...p, fp_method: p.fp_method || "estimated", fee_params: feeP }
    }
    const res = await api.post("/export/generate", reqData, { timeout: 60000 })
    if (res.data.code === 0) {
      const d = res.data.data
      calc.value = d.calculation
      zipPath.value = d.zip_path || ""
      ElMessage.success("测算完成，总造价 " + totalCost.value + " 万元")
    } else {
      ElMessage.warning(res.data.message || "测算失败")
    }
  } catch (e) {
    ElMessage.error("测算失败: " + (e.response?.data?.message || e.message))
  } finally { calculating.value = false }
}

async function generateAndDownload() {
  if (!zipPath.value && !calc.value) { await calculateCost() }
  if (!zipPath.value) { ElMessage.warning("请先完成测算"); return }
  generating.value = true
  try {
    const a = document.createElement("a")
    a.href = "/api/export/download/" + encodeURIComponent(zipPath.value)
    a.download = ""
    a.click()
    ElMessage.success("下载已开始")
  } catch (e) {
    ElMessage.error("下载失败: " + (e.message || "未知错误"))
  } finally { generating.value = false }
}

onMounted(async () => {
  const pid = props.projectId || route.params.projectId
  if (!pid) { router.push("/"); return }
  try {
    const res = await api.get("/project/" + pid)
    project.value = res.data.data
    const pStr = sessionStorage.getItem("zhaojia_params_" + pid)
    params.value = pStr ? JSON.parse(pStr) : null
    const fpStr = sessionStorage.getItem("zhaojia_fp_" + pid)
    if (fpStr) items.value = JSON.parse(fpStr)
  } catch (e) {
    ElMessage.error("加载失败: " + (e.message || "未知错误"))
  } finally { loading.value = false }
  if (items.value.length > 0) await calculateCost()
})
</script>

