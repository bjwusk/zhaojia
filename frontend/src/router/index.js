import { createRouter, createWebHistory } from "vue-router"

const routes = [
  { path: "/login", name: "Login", component: () => import("../views/Login.vue") },
  { path: "/register", name: "Register", component: () => import("../views/Login.vue") },
  { path: "/", name: "Dashboard", component: () => import("../views/Dashboard.vue"), meta: { requiresAuth: true } },
  { path: "/settings", name: "Settings", component: () => import("../views/Settings.vue"), meta: { requiresAuth: true } },
  { path: "/step1/:projectId", name: "StepParams", component: () => import("../views/StepParams.vue"), props: true, meta: { requiresAuth: true, step: 1 } },
  { path: "/step2/:projectId", name: "StepHighlight", component: () => import("../views/StepHighlight.vue"), props: true, meta: { requiresAuth: true, step: 2 } },
  { path: "/step3/:projectId", name: "StepFP", component: () => import("../views/StepFP.vue"), props: true, meta: { requiresAuth: true, step: 3 } },
  { path: "/step4/:projectId", name: "StepResult", component: () => import("../views/StepResult.vue"), props: true, meta: { requiresAuth: true, step: 4 } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("zhaojia_token")
  if (to.meta.requiresAuth && !token) { next("/login") }
  else { next() }
})

export default router
