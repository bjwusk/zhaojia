<template>
  <div v-if="!isLoginPage">
    <el-container style="min-height: 100vh;">
      <el-aside width="200px" style="background: #304156;">
        <div style="padding:16px;color:white;font-size:15px;font-weight:bold;text-align:center;border-bottom:1px solid #4a5a6a;line-height:1.4;">
          软件造价<br/>自动生成器
        </div>
        <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF" style="border-right:none;">
          <el-menu-item index="/">
            <el-icon><UploadFilled /></el-icon><span>上传文件</span>
          </el-menu-item>
          <el-menu-item :index="'/step1/'+pid" v-if="pid">
            <el-icon><Setting /></el-icon><span>参数调整</span>
          </el-menu-item>
          <el-menu-item :index="'/step2/'+pid" v-if="pid">
            <el-icon><Edit /></el-icon><span>文件标注</span>
          </el-menu-item>
          <el-menu-item :index="'/step3/'+pid" v-if="pid">
            <el-icon><List /></el-icon><span>功能点清单</span>
          </el-menu-item>
          <el-menu-item :index="'/step4/'+pid" v-if="pid">
            <el-icon><Money /></el-icon><span>造价结果</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><UserFilled /></el-icon><span>设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header style="background:white;border-bottom:1px solid #e6e6e6;display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:48px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <el-steps :active="currentStep" simple style="background:transparent;padding:0;">
              <el-step title="参数调整" :status="stepStatus(1)" />
              <el-step title="文件标注" :status="stepStatus(2)" />
              <el-step title="功能点清单" :status="stepStatus(3)" />
              <el-step title="造价结果" :status="stepStatus(4)" />
            </el-steps>
          </div>
          <span style="font-size:12px;color:#909399;">{{ projName }}</span>
        </el-header>
        <el-main style="background:#f0f2f5;padding:20px;">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
  <router-view v-else />
</template>

<script setup>
import { computed, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

const route = useRoute()
const router = useRouter()

const isLoginPage = computed(() => ["Login", "Register"].includes(route.name))
const pid = computed(() => (route.params.projectId && route.params.projectId !== "new") ? route.params.projectId : "")

const stepNames = { StepParams: 1, StepHighlight: 2, StepFP: 3, StepResult: 4 }
const currentStep = computed(() => stepNames[route.name] || 0)

const projName = ref("")
// Watch for route changes to get project name
import { watch } from "vue"
watch(() => route.params, (val) => {
  if (val.projectId) {
    try {
      const stored = sessionStorage.getItem("proj_" + val.projectId)
      if (stored) projName.value = stored
    } catch {}
  }
}, { immediate: true })

function stepStatus(step) {
  const cs = currentStep.value
  if (cs === 0) return "wait"
  if (step < cs) return "success"
  if (step === cs) return "process"
  return "wait"
}
</script>
