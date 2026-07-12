<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>第三步：功能点清单<span style="font-size:12px;color:#909399;">(共{{ items.length }} 条)</span></span>
          <div>
            <el-tag size="small" type="info" style="margin-right:4px;">
              {{ fpMethod === "estimated" ? "预估功能点法" : "预算功能点法" }}
            </el-tag>
            <el-button size="small" :icon="Plus" style="margin-left:8px;" @click="addRow">添加行</el-button>
            <el-button size="small" :icon="Delete" @click="removeSelected" :disabled="!selectedRows.length">删除</el-button>
            <el-button type="primary" size="small" @click="saveAndNext" style="margin-left:8px;">
              保存并查看造价 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="items" border size="small" max-height="520" @selection-change="r=>selectedRows=r">
        <el-table-column type="selection" width="32" />
        <el-table-column label="#" width="32"><template #default="s">{{ s.$index + 1 }}</template></el-table-column>
        <el-table-column label="子系统" width="80"><template #default="s"><el-input v-model="s.row.subsystem" size="small" /></template></el-table-column>
        <el-table-column label="一级模块" width="90"><template #default="s"><el-input v-model="s.row.module_l1" size="small" /></template></el-table-column>
        <el-table-column label="功能项描述" min-width="130"><template #default="s"><el-input v-model="s.row.description" size="small" /></template></el-table-column>
        <el-table-column label="计数项名称" width="110"><template #default="s"><el-input v-model="s.row.fp_name" size="small" /></template></el-table-column>
        <el-table-column label="类别" width="60">
          <template #default="s">
            <el-select v-model="s.row.category" size="small" @change="()=>recalcRow(s.row)">
              <el-option v-for="c in ['ILF','EIF','EI','EO','EQ']" :key="c" :label="c" :value="c" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="UFP" width="55">
          <template #default="s"><el-input-number v-model="s.row.ufp" :min="1" :max="100" size="small" style="width:55px;" controls-position="right" @change="()=>recalcRow(s.row)" /></template>
        </el-table-column>
        <el-table-column label="复杂度" width="70">
          <template #default="s">
            <el-select v-model="s.row.complexity" size="small" @change="()=>recalcRow(s.row)">
              <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="重用程度" width="80">
          <template #default="s">
            <el-select v-model="s.row.reuse_level" size="small" @change="()=>recalcRow(s.row)">
              <el-option label="高(0.33)" value="high" /><el-option label="中(0.67)" value="medium" /><el-option label="低(1.0)" value="low" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="修改类型" width="70">
          <template #default="s">
            <el-select v-model="s.row.modify_type" size="small">
              <el-option label="新建" value="new" /><el-option label="修改" value="modify" /><el-option label="复用" value="reuse" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="US" width="50"><template #default="s">{{ calcUs(s.row) }}</template></el-table-column>
      </el-table>

      <div style="margin-top:8px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <span style="font-size:13px;">UFP合计: <b>{{ totalUfp }}</b> | 总US: <b>{{ totalUs }}</b> | 共 <b>{{ items.length }}</b> 条</span>
          </div>
          <div>
            <span style="font-size:12px;color:#909399;">最终功能点数将乘以调整因子计算造价</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { Plus, Delete } from "@element-plus/icons-vue"

const props = defineProps({ projectId: { type: [String, Number], default: null } })
const route = useRoute()
const router = useRouter()

const items = ref([])
const selectedRows = ref([])
const fpMethod = ref("estimated")

const weights = { ILF: 35, EIF: 15, EI: 4, EO: 5, EQ: 4 }
const complexityFactors = { low: 0.8, medium: 1.0, high: 1.2 }
const reuseFactors = { high: 0.33, medium: 0.67, low: 1.0 }

function calcUs(row) {
  const reuse = reuseFactors[row.reuse_level || "low"] || 1
  const complexity = complexityFactors[row.complexity || "medium"] || 1
  return Math.round((row.ufp || 0) * reuse * complexity * 100) / 100
}

const totalUfp = computed(() => items.value.reduce((s, r) => s + (Number(r.ufp) || 0), 0))
const totalUs = computed(() => items.value.reduce((s, r) => s + calcUs(r), 0))

function newRow() {
  return { category: "EI", description: "", fp_name: "", ufp: 4, subsystem: "系统", module_l1: "数据管理", complexity: "medium", reuse_level: "low", modify_type: "new" }
}

function addRow() { items.value.push(newRow()) }

function removeSelected() {
  const toRemove = new Set(selectedRows.value)
  items.value = items.value.filter(item => !toRemove.has(item))
  selectedRows.value = []
}

function recalcRow(row) {
  if (row.category && weights[row.category]) {
    row.ufp = weights[row.category]
  }
}

function saveAndNext() {
  const pid = props.projectId || route.params.projectId
  // Validate subsystem and module_l1
  for (let i = 0; i < items.value.length; i++) {
    const row = items.value[i];
    if (!row.subsystem || !row.subsystem.trim()) {
      ElMessage.warning("第" + (i+1) + " 行：子系统不能为空");
      return;
    }
    if (!row.module_l1 || !row.module_l1.trim()) {
      ElMessage.warning("第" + (i+1) + " 行：一级模块不能为空");
      return;
    }
  }
  sessionStorage.setItem("zhaojia_fp_" + pid, JSON.stringify(items.value))
  router.push("/step4/" + pid)
}

function autoFillFields(items) {
  // 自动填充空的子系统和一级模块
  for (const row of items) {
    if (!row.subsystem || !row.subsystem.trim()) {
      // 从描述中提取子系统名称
      const desc = row.description || row.fp_name || '';
      // 找“XX系统”模式
      const sysMatch = desc.match(/([一-龥·a-zA-Z0-9]{2,20})系统/);
      if (sysMatch) {
        row.subsystem = sysMatch[0];
      } else {
        // 从描述中取第一个有意义的名称段
        const nameMatch = desc.match(/^([一-龥a-zA-Z]{4,20})/);
        if (nameMatch) {
          row.subsystem = nameMatch[1];
        } else {
          row.subsystem = '系统';
        }
      }
    }
    if (!row.module_l1 || !row.module_l1.trim()) {
      // 从描述或fp_name中提取一级模块
      const name = row.fp_name || row.description || '';
      if (name && name.length > 1) {
        const nameClean = name.replace(/[（〈(].*?[）〉)]/g, '').trim();
        if (nameClean.length > 1) {
          row.module_l1 = nameClean.substring(0, 10);
        } else {
          row.module_l1 = '数据管理';
        }
      } else {
        row.module_l1 = '数据管理';
      }
    }
  }
  return items;
}

onMounted(() => {
  const pid = props.projectId || route.params.projectId
  if (!pid) { router.push("/"); return }

  const stored = sessionStorage.getItem("zhaojia_fp_" + pid)
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      if (parsed && parsed.length) { 
        items.value = autoFillFields(parsed);
        // Save back to sessionStorage with filled fields
        sessionStorage.setItem("zhaojia_fp_" + pid, JSON.stringify(items.value));
      }
    } catch {}
  }
  const paramsStr = sessionStorage.getItem("zhaojia_params_" + pid)
  if (paramsStr) {
    try {
      const p = JSON.parse(paramsStr)
      if (p.form && p.form.fp_method) fpMethod.value = p.form.fp_method
    } catch {}
  }
})
</script>