<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>测算结果 - {{ version?.version_name || "..." }}</span>
        <div>
          <el-button @click="downloadWord" :icon="Document">下载Word报告</el-button>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </div>
    </template>

    <div v-loading="loading">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="项目">{{ project?.name }}</el-descriptions-item>
        <el-descriptions-item label="调整后FP">{{ version?.adjusted_fp }}</el-descriptions-item>
        <el-descriptions-item label="人月数">{{ version?.person_months }}</el-descriptions-item>
        <el-descriptions-item label="人工费(万元)">{{ version?.labor_cost }}</el-descriptions-item>
        <el-descriptions-item label="总造价(万元)" :content-style="{color:'#f56c6c','font-size':'16px','font-weight':'bold'}">{{ version?.total_cost }}</el-descriptions-item>
      </el-descriptions>

      <el-table :data="costDetails" border size="small" style="margin-top:16px;">
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column prop="item_name" label="费用项" min-width="140" />
        <el-table-column prop="base_amount" label="基数" width="100"><template #default="s">{{ s.row.base_amount || "-" }}</template></el-table-column>
        <el-table-column prop="rate" label="费率%" width="70"><template #default="s">{{ s.row.rate || "-" }}</template></el-table-column>
        <el-table-column prop="amount" label="金额(万元)" width="110"><template #default="s"><b>{{ s.row.amount }}</b></template></el-table-column>
      </el-table>

      <el-table :data="items" border size="small" style="margin-top:16px;" max-height="300">
        <el-table-column prop="seq" label="#" width="40" />
        <el-table-column prop="description" label="功能描述" min-width="140" />
        <el-table-column prop="category" label="类别" width="60" />
        <el-table-column prop="ufp" label="UFP" width="55" />
        <el-table-column prop="us" label="US" width="55" />
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useEstimateStore } from "../stores/estimateStore"
import { useProjectStore } from "../stores/projectStore"

const props = defineProps({ versionId: { type: [String, Number], default: null } })
const route = useRoute()
const router = useRouter()
const eStore = useEstimateStore()
const pStore = useProjectStore()

const loading = ref(true)
const version = ref(null)
const project = ref(null)
const items = ref([])
const costDetails = ref([])

onMounted(async () => {
  const vid = props.versionId || route.params.versionId
  if (!vid) return
  const data = await eStore.loadVersion(vid)
  if (data) {
    version.value = data.version
    items.value = data.items || []
    costDetails.value = data.cost_details || []
    if (data.version?.project_id) project.value = await pStore.fetchProject(data.version.project_id)
  }
  loading.value = false
})

function downloadWord() {
  const vid = version.value?.id
  if (vid) eStore.exportWord(vid)
}
</script>
