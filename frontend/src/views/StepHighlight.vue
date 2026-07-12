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
            <el-button v-if="hasApiKey && !aiDone" type="warning" size="default" @click="confirmAndAnalyze" :loading="aiLoading" :disabled="!extracted" style="margin-right:8px;">
              <el-icon><Select /></el-icon> AI标注
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
                  <span>文档内容</span>
                  <div style="display:flex;gap:4px;">
                    <el-tag size="small" v-if="aiDone" v-for="item in legend" :key="item.key"
                      style="cursor:pointer;"
                      :style="{ background: item.color+'22', color: item.color, borderColor: item.color+'44' }"
                      @click="scrollToCategory(item.key)">
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
                <div ref="contentDivRef" @contextmenu.prevent="handleContextMenu" style="max-height:600px;overflow-y:auto;white-space:pre-wrap;font-size:13px;line-height:1.8;padding:12px;background:#fafafa;border:1px solid #dcdfe6;border-radius:4px;font-family:'Microsoft YaHei',sans-serif;">
                  <span v-if="!displayHtml" style="color:#909399;">暂无内容</span>
                  <span v-else v-html="displayHtml"></span>
                </div>
                <div style="margin-top:4px;font-size:11px;color:#909399;">
                  {{ editText.length }} 字符 | {{ matchCount }} 处功能点匹配
                </div>
                <!-- 各分类上下导航 -->
                <div v-if="aiDone" style="margin-top:6px;display:flex;flex-wrap:wrap;gap:6px;">
                  <div v-for="item in legend" :key="item.key" style="display:flex;align-items:center;gap:3px;background:item.color+'11';padding:2px 6px;border-radius:4px;border:1px solid item.color+'33';">
                    <el-tag size="small" :style="{background:item.color+'33',color:item.color,border:'none',cursor:'pointer'}" @click="scrollToCategory(item.key)">{{ item.label }}</el-tag>
                    <el-button size="small" text :disabled="navCatItems(item.key).length === 0" @click="navCategoryPrev(item.key)">
                      <el-icon><ArrowLeft /></el-icon> 上一个
                    </el-button>
                    <span style="font-size:11px;color:#909399;min-width:28px;text-align:center;">{{ navCatIndex(item.key) + 1 }}/{{ navCatItems(item.key).length }}</span>
                    <el-button size="small" text :disabled="navCatItems(item.key).length === 0" @click="navCategoryNext(item.key)">
                      下一个 <el-icon><ArrowRight /></el-icon>
                    </el-button>
                  </div>
                </div>
            <!-- Context Menu -->
            <div v-if="ctxMenuVisible" class="ctx-menu-overlay" @click="handleCtxOutsideClick" @contextmenu.prevent="handleCtxOutsideClick"></div>
            <div v-if="ctxMenuVisible" class="ctx-menu-dropdown" :style="{ left: ctxMenuPos.x + 'px', top: ctxMenuPos.y + 'px' }">
              <div v-if="!ctxIsOnSpan" style="font-size:11px;color:#909399;padding:4px 8px;border-bottom:1px solid #eee;">添加为功能点:</div>
              <div v-if="!ctxIsOnSpan" v-for="cat in availableCtxCategories" :key="cat" class="ctx-menu-item" @click="addFromContext(cat)">
                <span :style="{ display:'inline-block', width:'8px', height:'8px', borderRadius:'50%', background: colorMap[cat] || '#999', marginRight:'6px' }"></span>
                {{ cat }}
              </div>
              <div v-if="ctxIsOnSpan" style="font-size:11px;color:#e6a23c;padding:4px 8px;border-bottom:1px solid #eee;">已标注功能点</div>
              <div v-if="ctxIsOnSpan" class="ctx-menu-item" style="color:#F56C6C;" @click="deleteFromContext">
                <span style="margin-right:6px;">🗑</span> 删除功能点
              </div>
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
                <p>3. 点击「AI标注」自动识别功能点</p>
              </div>

              <!-- 功能点表格 -->
              <el-table v-if="aiDone" :data="fpItems" border size="small" max-height="520" style="width:100%" @row-click="scrollToFpItem">
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
const extracted = ref(false)
const aiDone = ref(false)
const hasApiKey = ref(false)
const fpMethod = ref("estimated")
const matchCount = ref(0)
const fpItems = ref([])
const fpCategories = computed(() => fpMethod.value === "estimated" ? ["ILF","EIF"] : ["ILF","EIF","EI","EO","EQ"])
const highlightData = ref({})
const contentDivRef = ref(null)
const ctxMenuVisible = ref(false)
const ctxMenuPos = ref({ x: 0, y: 0 })
const ctxSelectedText = ref("")
const ctxTargetFp = ref(null)
const ctxIsOnSpan = ref(false)
const navCategory = ref(null)
const navIndex = ref(-1)
const navTotal = ref(0)

const defaultColors = { ILF: "#E74C3C", EIF: "#E67E22", EI: "#3498DB", EO: "#2ECC71", EQ: "#9B59B6" }
const colorMap = ref({ ...defaultColors })

const ilfEifOnly = [
  { key: "ILF", label: "ILF 内部逻辑文件", color: colorMap.value.ILF },
  { key: "EIF", label: "EIF 外部接口文件", color: colorMap.value.EIF },
]
const allFpTypes = [
  ...ilfEifOnly,
  { key: "EI", label: "EI 外部输入", color: colorMap.value.EI },
  { key: "EO", label: "EO 外部输出", color: colorMap.value.EO },
  { key: "EQ", label: "EQ 外部查询", color: colorMap.value.EQ },
]
const legend = computed(() => fpMethod.value === "estimated" ? ilfEifOnly : allFpTypes)

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
      result += `<span data-cat="${earliestMatch.cat}" data-fp="${escapeHtml(earliestMatch.kw)}" style="color:${earliestMatch.color};font-weight:bold;background:${earliestMatch.color}18;">${escapeHtml(earliestMatch.kw)}</span>`
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

const availableCtxCategories = computed(() => {
  return fpMethod.value === "estimated" ? ["ILF","EIF"] : ["ILF","EIF","EI","EO","EQ"];
})

function handleContextMenu(e) {
  // Check if clicking on a highlight span
  const target = e.target;
  if (target && target.tagName === 'SPAN' && target.hasAttribute('data-fp')) {
    // Find the fp item that matches this span
    const fpName = target.getAttribute('data-fp');
    const fpCat = target.getAttribute('data-cat');
    const match = fpItems.value.find(function(it) { return it.fp_name === fpName || it.description === fpName; });
    if (match) {
      ctxTargetFp.value = match;
      ctxIsOnSpan.value = true;
      ctxMenuPos.value = { x: e.clientX, y: e.clientY };
      ctxMenuVisible.value = true;
      return;
    }
  }
  // Otherwise, handle as new selection for adding FP
  const sel = window.getSelection();
  if (!sel || !sel.toString().trim()) {
    ElMessage.info("请先选中文档中的文字");
    return;
  }
  ctxSelectedText.value = sel.toString().trim();
  ctxMenuPos.value = { x: e.clientX, y: e.clientY };
  ctxIsOnSpan.value = false;
  ctxMenuVisible.value = true;
}

function addFromContext(cat) {
  ctxMenuVisible.value = false;
  const text = ctxSelectedText.value;
  if (!text) { ElMessage.warning("未选中文字"); return; }
  const ufpMap = { ILF: 35, EIF: 15, EI: 4, EO: 5, EQ: 4 };
  fpItems.value.push({
    category: cat,
    description: text,
    fp_name: text.substring(0, 20),
    ufp: ufpMap[cat] || 4,
    subsystem: "",
    module_l1: "",
    complexity: "medium",
    reuse_level: "low",
    modify_type: "new"
  });
  ElMessage.success("已添加 " + cat + ": " + text.substring(0, 30));
}

function deleteFromContext() {
  ctxMenuVisible.value = false;
  const fp = ctxTargetFp.value;
  if (!fp) return;
  const idx = fpItems.value.indexOf(fp);
  if (idx >= 0) {
    fpItems.value.splice(idx, 1);
    ElMessage.success("已删除功能点：" + (fp.fp_name || fp.description || "").substring(0, 30));
  }
}

function handleCtxOutsideClick() {
  ctxMenuVisible.value = false;
}

function scrollToFpItem(row) {
  const text = row.fp_name || row.description;
  if (!text) return;
  const div = contentDivRef.value;
  if (!div) return;
  const spans = div.querySelectorAll("span[data-fp='" + text.replace(/'/g, "") + "']");
  if (spans.length > 0) {
    spans[0].scrollIntoView({behavior: "smooth", block: "center"});
    const cat = row.category;
    spans[0].style.background = (colorMap.value[cat] || "#999") + "44";
    setTimeout(() => { spans[0].style.background = (colorMap.value[cat] || "#999") + "18"; }, 1000);
  } else {
    // Fallback: search by text content
    const bodyText = div.innerText || div.textContent;
    const idx = bodyText.indexOf(text);
    if (idx >= 0) {
      const range = document.createRange();
      const sel = window.getSelection();
      sel.removeAllRanges();
      const textNode = div.childNodes[0];
      if (textNode && textNode.length > idx) {
        range.setStart(textNode, idx);
        range.setEnd(textNode, idx + text.length);
        sel.addRange(range);
        textNode.parentElement.scrollIntoView({behavior: "smooth", block: "center"});
      }
    }
  }
}


function navPrev() {
  if (navIndex.value > 0) {
    navIndex.value--;
    scrollToNavItem(navIndex.value);
  }
}
function navNext() {
  if (navIndex.value < navTotal.value - 1) {
    navIndex.value++;
    scrollToNavItem(navIndex.value);
  }
}
function scrollToNavItem(idx) {
  const cat = navCategory.value;
  if (!cat) return;
  const div = contentDivRef.value;
  if (!div) return;
  const spans = div.querySelectorAll("span[data-cat='" + cat + "']");
  if (spans.length > 0 && idx >= 0 && idx < spans.length) {
    // Clear previous highlights
    spans.forEach(function(s) { 
      s.style.outline = "none";
      s.style.background = (colorMap.value[cat] || "#999") + "18";
    });
    // Highlight current
    const span = spans[idx];
    span.style.outline = "2px solid " + (colorMap.value[cat] || "#999");
    span.style.background = (colorMap.value[cat] || "#999") + "44";
    span.scrollIntoView({behavior: "smooth", block: "center"});
    navTotal.value = spans.length;
  }
}
function scrollToCategory(cat) {
  const div = contentDivRef.value;
  if (!div) return;
  const spans = div.querySelectorAll("span[data-cat='" + cat + "']");
  if (spans.length > 0) {
    spans[0].scrollIntoView({behavior: "smooth", block: "center"});
    spans[0].style.background = (colorMap.value[cat] || "#999") + "44";
    setTimeout(() => { spans[0].style.background = (colorMap.value[cat] || "#999") + "18"; }, 1000);
  }
}

function escapeHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
}

function resetToOriginal() { editText.value = rawText.value }

function addFpRow() { fpItems.value.push({ category: "ILF", description: "", fp_name: "", ufp: 35, subsystem: "系统", module_l1: "数据管理", complexity: "medium", reuse_level: "low", modify_type: "new" }) }
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
      extracted.value = true
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

function navCatItems(cat) {
  if (!cat || !fpItems.value.length) return [];
  return fpItems.value.filter(function(it) { return it.category === cat; });
}
function navCatIndex(cat) {
  const items = navCatItems(cat);
  if (!items.length) return -1;
  const div = contentDivRef.value;
  if (!div) return 0;
  const spans = div.querySelectorAll("span[data-cat='" + cat + "']");
  if (!spans.length) return 0;
  // Find which span is currently visible (closest to top)
  let bestIdx = 0, bestDist = Infinity;
  spans.forEach(function(s, i) {
    var rect = s.getBoundingClientRect();
    var dist = Math.abs(rect.top - 100);
    if (dist < bestDist) { bestDist = dist; bestIdx = i; }
  });
  return bestIdx;
}
function navCategoryPrev(cat) {
  const items = navCatItems(cat);
  if (!items.length) return;
  const div = contentDivRef.value;
  if (!div) return;
  const spans = div.querySelectorAll("span[data-cat='" + cat + "']");
  if (!spans.length) return;
  var curIdx = navCatIndex(cat);
  var newIdx = (curIdx - 1 + spans.length) % spans.length;
  spans.forEach(function(s) { s.style.outline = "none"; s.style.background = (colorMap.value[cat] || "#999") + "18"; });
  spans[newIdx].style.outline = "2px solid " + (colorMap.value[cat] || "#999");
  spans[newIdx].style.background = (colorMap.value[cat] || "#999") + "44";
  spans[newIdx].scrollIntoView({behavior: "smooth", block: "center"});
}
function navCategoryNext(cat) {
  const items = navCatItems(cat);
  if (!items.length) return;
  const div = contentDivRef.value;
  if (!div) return;
  const spans = div.querySelectorAll("span[data-cat='" + cat + "']");
  if (!spans.length) return;
  var curIdx = navCatIndex(cat);
  var newIdx = (curIdx + 1) % spans.length;
  spans.forEach(function(s) { s.style.outline = "none"; s.style.background = (colorMap.value[cat] || "#999") + "18"; });
  spans[newIdx].style.outline = "2px solid " + (colorMap.value[cat] || "#999");
  spans[newIdx].style.background = (colorMap.value[cat] || "#999") + "44";
  spans[newIdx].scrollIntoView({behavior: "smooth", block: "center"});
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

  // 自动填充空的子系统/一级模块
  function autoFillFields(items) {
    for (const row of items) {
      if (!row.subsystem || !row.subsystem.trim()) {
        const desc = row.description || row.fp_name || '';
        const m = desc.match(/([一-龥0-9a-zA-Z]{2,20})系统/);
        row.subsystem = m ? m[0] : '系统';
      }
      if (!row.module_l1 || !row.module_l1.trim()) {
        const name = row.fp_name || row.description || '';
        const c = name.replace(/[（〈(].*?[）〉)]/g, '').trim();
        row.module_l1 = c && c.length > 1 ? c.substring(0, 10) : '数据管理';
      }
    }
    return items;
  }
  // Load stored FPs
  const stored = sessionStorage.getItem("zhaojia_fp_" + pid)
  if (stored) {
    try { const p = JSON.parse(stored); if (p.length) { fpItems.value = autoFillFields(p); aiDone.value = true; sessionStorage.setItem('zhaojia_fp_' + pid, JSON.stringify(fpItems.value)); } } catch {}
  }
  loading.value = false
})
</script>
<style scoped>
.ctx-menu-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 999;
  background: transparent;
}
.ctx-menu-dropdown {
  position: fixed;
  z-index: 1000;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.12);
  padding: 4px 0;
  min-width: 160px;
}
.ctx-menu-item {
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  transition: background 0.2s;
}
.ctx-menu-item:hover {
  background: #f0f5ff;
  color: #409eff;
}

/* Nav highlight outline */
span[style*="outline: 2px solid"] {
  border-radius: 2px;
}</style>