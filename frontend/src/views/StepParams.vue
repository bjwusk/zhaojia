<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>第二步：参数调整</span>
          <el-button type="primary" @click="saveAndNext">
            保存并标注文件<el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>

      <el-alert v-if="isFromUpload && !uploadHasText" title="上传的文档内容为空，请确认文件格式是否正确（支持PDF/DOCX/TXT）" type="warning" show-icon :closable="false" style="margin-bottom:12px;" />

      <el-form :model="form" label-width="140px">

        <el-divider content-position="left">项目基本信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目名称">
              <el-input v-model="form.project_name" size="large" placeholder="输入项目名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-tag type="success" v-if="isFromUpload" style="margin-top:4px;">推荐：{{ suggestedName }}</el-tag>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="行业">
              <el-select v-model="form.industry" style="width:100%" @change="updateProject">
                <el-option v-for="ind in industries" :key="ind" :label="ind" :value="ind" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="城市">
              <el-select v-model="form.city" style="width:100%" @change="updateProject">
                <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="估算时机">
              <el-select v-model="form.scale_timing" style="width:100%">
                <el-option label="估算早期 (×1.39)" value="early_stage" />
                <el-option label="估算中期 (×1.21)" value="mid_stage" />
                <el-option label="估算晚期 (×1.10)" value="late_stage" />
                <el-option label="交付后/运维 (×1.00)" value="post_delivery" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="PDR百分位">
              <el-select v-model="form.pdr_percentile" style="width:100%">
                <el-option label="下限" value="lower" />
                <el-option label="中值" value="median" />
                <el-option label="上限" value="upper" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="建设模式">
              <el-select v-model="form.build_mode" style="width:100%">
                <el-option label="自研" value="自研" />
                <el-option label="外包" value="外包" />
                <el-option label="定制开发" value="定制开发" />
                <el-option label="成套采购" value="成套采购" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">功能点测算方法</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="功能点法">
              <el-select v-model="form.fp_method" style="width:100%">
                <el-option label="预估功能点法（仅ILF/EIF）" value="estimated" />
                <el-option label="预算功能点法（全5类）" value="detailed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-tag type="info" style="margin-top:4px;">
              {{ form.fp_method === "estimated" ? "UFP=35×ILF+15×EIF" : "UFP=10×ILF+7×EIF+4×EI+5×EO+4×EQ" }}
            </el-tag>
          </el-col>
        </el-row>

        <template v-if="isDev">
          <el-divider content-position="left">开发特征调整因子</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="应用类型">
                <el-select v-model="form.application_type" style="width:100%">
                  <el-option v-for="at in appTypes" :key="at.name" :label="at.label" :value="at.name" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="开发语言">
                <el-select v-model="form.dev_language" style="width:100%">
                  <el-option label="JAVA/C++/C# (×1.0)" value="JAVA、C++、C#及其他同级别语言/平台" />
                  <el-option label="Python/JS/其他脚本 (×1.2)" value="Python、JS及其他脚本/动态语言/低代码/快速开发平台" />
                  <el-option label="汇编/C语言 (×0.8)" value="汇编、C语言等面向过程/底层语言" />
                  <el-option label="其他" value="其他" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="团队背景">
                <el-select v-model="form.team_background" style="width:100%">
                  <el-option label="为其他行业开发过类似项目" value="为其他行业开发过类似的项目，或为本行业开发过不同但相关的项目" />
                  <el-option label="有部分相关经验" value="虽有相关开发经验，但开发团队中约半数以上属于新手/未参与过类似项目" />
                  <el-option label="全新领域" value="全新的开发团队，且未曾涉足过该领域" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="完整性级别">
                <el-select v-model="form.integrity_level" style="width:100%">
                  <el-option label="C/D级别或无明确完整性级别" value="C/D级别或无明确完整性级别" />
                  <el-option label="B级别" value="B级别" />
                  <el-option label="A级别" value="A级别" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="16">
              <el-form-item label="非功能性特征分（点击修改）">
                <div style="display:flex;gap:12px;flex-wrap:wrap;">
                  <label style="font-size:12px;">分布式: <el-input-number v-model="form.distributed_score" :min="0" :max="5" size="small" style="width:70px;" /></label>
                  <label style="font-size:12px;">性能: <el-input-number v-model="form.performance_score" :min="0" :max="5" size="small" style="width:70px;" /></label>
                  <label style="font-size:12px;">可靠性: <el-input-number v-model="form.reliability_score" :min="0" :max="5" size="small" style="width:70px;" /></label>
                  <label style="font-size:12px;">多场地: <el-input-number v-model="form.multi_site_score" :min="0" :max="5" size="small" style="width:70px;" /></label>
                  <span style="font-size:12px;color:#909399;">系数=1+Σ分×0.025 = {{ nfFactor }}</span>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <template v-else>
          <el-divider content-position="left">运维特征调整因子</el-divider>
          <el-row :gutter="20">
            <el-col :span="8"><el-form-item label="业务重要性"><el-select v-model="form.business_importance" style="width:100%"><el-option label="一般" value="一般" /><el-option label="重要" value="重要" /><el-option label="核心" value="核心" /></el-select></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="更新频率"><el-select v-model="form.update_frequency" style="width:100%"><el-option label="平均每月1次或以下" value="平均每月1次或以下" /><el-option label="平均每月2-4次" value="平均每月2-4次" /><el-option label="平均每月5次以上" value="平均每月5次以上" /></el-select></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="支持方式"><el-select v-model="form.support_mode" style="width:100%"><el-option label="现场支持为主" value="现场支持为主" /><el-option label="远程支持为主" value="远程支持为主" /><el-option label="混合支持" value="混合支持" /></el-select></el-form-item></el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8"><el-form-item label="安全等级"><el-select v-model="form.security_level" style="width:100%"><el-option label="第三级" value="第三级" /><el-option label="第二级" value="第二级" /><el-option label="第一级" value="第一级" /></el-select></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="响应时效"><el-select v-model="form.response_time" style="width:100%"><el-option label="一级故障处理时间小于8h" value="一级故障处理时间小于8h" /><el-option label="一级故障处理时间8-24h" value="一级故障处理时间8-24h" /><el-option label="一级故障处理时间大于24h" value="一级故障处理时间大于24h" /></el-select></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="部署方式"><el-select v-model="form.deploy_mode" style="width:100%"><el-option label="集中部署" value="集中部署" /><el-option label="分布式部署" value="分布式部署" /><el-option label="混合部署" value="混合部署" /></el-select></el-form-item></el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8"><el-form-item label="用户规模"><el-select v-model="form.user_scale" style="width:100%"><el-option label="小于等于10000" value="小于等于10000" /><el-option label="10001-100000" value="10001-100000" /><el-option label="大于100000" value="大于100000" /></el-select></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="涉密等级"><el-select v-model="form.confidential" style="width:100%"><el-option label="非涉密" value="非涉密" /><el-option label="涉密一般" value="涉密一般" /><el-option label="涉密较高" value="涉密较高" /></el-select></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="团队经验"><el-select v-model="form.team_experience" style="width:100%"><el-option label="为其他行业做过类似项目" value="为其他行业做过类似的项目，或为本行业做过不同但相关的项目" /><el-option label="有部分相关经验" value="虽有相关运维经验，但团队中约半数以上属于新手" /><el-option label="全新领域" value="全新的运维团队，且未曾涉足过该领域" /></el-select></el-form-item></el-col>
          </el-row>
        </template>

      </el-form>
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
const api = axios.create({ baseURL: "/api" })

const isDev = ref(true)
const isFromUpload = ref(false)
const uploadHasText = ref(true)
const suggestedName = ref("")

const industries = ["通用","政务","交通","能源","煤炭","金融","工业软件","嵌入式","AI大模型","教育","医疗","农业","水利","环保","军工"]
const cities = ["北京","上海","广州","深圳","成都","杭州","南京","武汉","西安","长沙","郑州","济南","合肥","重庆","天津","其他"]
const appTypes = [
  { name: "业务处理", label: "业务处理 (×1.0)" }, { name: "科技", label: "科技 (×1.2)" },
  { name: "多媒体", label: "多媒体 (×1.3)" }, { name: "智能信息", label: "智能信息 (×1.5)" },
  { name: "基础软件/支撑软件", label: "基础软件/支撑 (×1.7)" },
  { name: "通信控制", label: "通信控制 (×1.9)" }, { name: "流程控制", label: "流程控制 (×2.0)" },
]

const form = ref({
  project_name: "", fp_method: "estimated", industry: "通用", city: "北京",
  scale_timing: "post_delivery", pdr_percentile: "median", build_mode: "自研",
  application_type: "业务处理", dev_language: "JAVA、C++、C#及其他同级别语言/平台",
  team_background: "为其他行业开发过类似的项目，或为本行业开发过不同但相关的项目",
  integrity_level: "C/D级别或无明确完整性级别",
  distributed_score: 0, performance_score: 0, reliability_score: 0, multi_site_score: 0,
  business_importance: "一般", update_frequency: "平均每月1次或以下",
  support_mode: "现场支持为主", security_level: "第三级",
  response_time: "一级故障处理时间小于8h", deploy_mode: "集中部署",
  user_scale: "小于等于10000", system_correlation: "1-5个系统",
  confidential: "非涉密", team_experience: "为其他行业做过类似的项目，或为本行业做过不同但相关的项目",
})


const nfFactor = computed(() => {
  const s = (form.value.distributed_score||0) + (form.value.performance_score||0) + (form.value.reliability_score||0) + (form.value.multi_site_score||0)
  return (1 + s * 0.025).toFixed(4)
})

onMounted(async () => {
  const pid = props.projectId || route.params.projectId
  if (!pid) { router.push("/"); return }
  if (pid === "new") {
    const uploadName = sessionStorage.getItem("zhaojia_upload_name") || ""
    const uploadType = sessionStorage.getItem("zhaojia_upload_type") || "dev"
    let uploadText = sessionStorage.getItem("zhaojia_upload_text") || ""
    suggestedName.value = uploadName
    isFromUpload.value = true
    uploadHasText.value = uploadText.length > 10
    form.value.project_name = uploadName
    isDev.value = uploadType === "dev"
    return
  }
  try {
    const res = await api.get("/project/" + pid)
    const p = res.data.data
    form.value.project_name = p.name || ""
    if (p.industry) form.value.industry = p.industry
    if (p.region) form.value.city = p.region
    isDev.value = p.estimate_type === "dev"
    sessionStorage.setItem("proj_" + pid, p.name)
    sessionStorage.setItem("zhaojia_params_" + pid, JSON.stringify({ form: form.value }))
  } catch { router.push("/") }
})

async function saveAndNext() {
  const pid = props.projectId || route.params.projectId
  let targetPid = pid
  if (pid === "new") {
    if (!form.value.project_name) { ElMessage.warning("请输入项目名称"); return }
    try {
      const fileText = sessionStorage.getItem("zhaojia_upload_text") || ""
      const uploadFilePath = sessionStorage.getItem("zhaojia_upload_filepath") || ""
      const estType = isDev.value ? "dev" : "ops"
      const res = await api.post("/project", {
        name: form.value.project_name,
        industry: form.value.industry,
        region: form.value.city,
        estimate_type: estType,
        stage: "可行性研究",
        build_mode: form.value.build_mode,
      })
      targetPid = res.data.data.id

      // Save document text via document API (server-side)
      if (fileText) {
        try {
          await api.post("/project/" + targetPid + "/document", {
            text: fileText,
            file_path: uploadFilePath || undefined,
          })
        } catch (e2) {
          console.warn("保存文档到服务器失败，将全部文本保存到sessionStorage", e2)
        }
      }
      sessionStorage.setItem("proj_" + targetPid, form.value.project_name)
      // Keep backup in sessionStorage for StepHighlight
      if (fileText) {
        sessionStorage.setItem("zhaojia_file_text_" + targetPid, fileText)
      }
    } catch (e) {
      ElMessage.error("创建项目失败: " + (e.response?.data?.message || e.message))
      return
    }
  }
  sessionStorage.setItem("zhaojia_params_" + targetPid, JSON.stringify({ form: form.value }))
  router.push("/step2/" + targetPid)
}

function updateProject() {
  const pid = props.projectId || route.params.projectId
  if (pid && pid !== "new") {
    api.put("/project/" + pid, { name: form.value.project_name, industry: form.value.industry, region: form.value.city }).catch(() => {})
  }
}
</script>