<template>
  <el-card>
    <template #header><span>{{ isEdit ? "编辑项目" : "项目信息" }}</span></template>
    <el-form :model="form" label-width="100px" style="max-width:600px;">
      <el-form-item label="项目名称"><el-input v-model="form.name" /></el-form-item>
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="行业"><el-select v-model="form.industry" style="width:100%"><el-option v-for="ind in industries" :key="ind" :label="ind" :value="ind" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="类型"><el-radio-group v-model="form.estimate_type"><el-radio value="dev">开发</el-radio><el-radio value="ops">运维</el-radio></el-radio-group></el-form-item></el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="地域"><el-select v-model="form.region" style="width:100%"><el-option v-for="c in cities" :key="c" :label="c" :value="c" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="阶段"><el-select v-model="form.stage" style="width:100%"><el-option label="可行性研究" value="可行性研究" /><el-option label="招标控制价" value="招标控制价" /><el-option label="施工图预算" value="施工图预算" /><el-option label="竣工结算" value="竣工结算" /><el-option label="评审复核" value="评审复核" /></el-select></el-form-item></el-col>
      </el-row>
      <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
        <el-button @click="$router.push('/')">返回</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import axios from "axios"

const props = defineProps({ id: { type: [String, Number], default: null } })
const route = useRoute()
const router = useRouter()
const api = axios.create({ baseURL: "/api" })

const industries = ["政务","金融","交通","能源","工业软件","通信","医疗","教育","嵌入式","AI/大模型","通用"]
const cities = ["北京","上海","广州","深圳","杭州","成都","武汉","南京","西安","长沙","郑州","济南","合肥","重庆","天津","其他"]
const isEdit = computed(() => !!(props.id || route.params.id))
const saving = ref(false)
const form = ref({ name: "", industry: "通用", estimate_type: "dev", region: "北京", stage: "可行性研究", description: "" })

onMounted(async () => {
  const pid = props.id || route.params.id
  if (pid) {
    const res = await api.get(`/project/${pid}`)
    if (res.data.data) form.value = { ...form.value, ...res.data.data }
  }
})

async function handleSave() {
  if (!form.value.name) { ElMessage.warning("请输入项目名称"); return }
  saving.value = true
  try {
    if (isEdit.value) { await api.put(`/project/${props.id || route.params.id}`, form.value) }
    else { await api.post("/project", form.value) }
    ElMessage.success("保存成功"); router.push("/")
  } finally { saving.value = false }
}
</script>
