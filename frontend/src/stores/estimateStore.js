import { defineStore } from "pinia"
import { estimateApi } from "../api/estimateApi"
import { exportApi } from "../api/exportApi"

export const useEstimateStore = defineStore("estimate", {
  state: () => ({
    versions: [],
    currentVersion: null,
    currentItems: [],
    currentDetails: [],
    calcResult: null,
    loading: false,
  }),
  actions: {
    async createVersion(data) {
      const api = data.estimate_type === "ops" ? estimateApi.createOpsVersion : estimateApi.createDevVersion
      const res = await api(data)
      return res.data.data
    },
    async loadVersion(id, type = "dev") {
      this.loading = true
      try {
        const api = type === "ops" ? estimateApi.getOpsVersion : estimateApi.getDevVersion
        const res = await api(id)
        this.currentVersion = res.data.data.version
        this.currentItems = res.data.data.items
        this.currentDetails = res.data.data.cost_details
        return res.data.data
      } finally {
        this.loading = false
      }
    },
    async saveItems(versionId, items, type = "dev") {
      const api = type === "ops" ? estimateApi.saveOpsItems : estimateApi.saveDevItems
      await api(versionId, { items })
    },
    async calculate(versionId, params, type = "dev") {
      this.loading = true
      try {
        const api = type === "ops" ? estimateApi.calculateOps : estimateApi.calculateDev
        const res = await api(versionId, params)
        this.calcResult = res.data.data
        return res.data.data
      } finally {
        this.loading = false
      }
    },
    async listVersions(projectId, type = "dev") {
      const api = type === "ops" ? estimateApi.listOpsVersions : estimateApi.listDevVersions
      const res = await api(projectId)
      this.versions = res.data.data
      return res.data.data
    },
    async exportExcel(versionId) {
      const res = await exportApi.exportExcel(versionId)
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement("a")
      link.href = url
      const disp = res.headers["content-disposition"]
      const fn = disp ? disp.split("filename=")[1] : "export.xlsx"
      link.setAttribute("download", fn)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
    async exportWord(versionId) {
      const res = await exportApi.exportWord(versionId)
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement("a")
      link.href = url
      const disp = res.headers["content-disposition"]
      const fn = disp ? disp.split("filename=")[1] : "export.docx"
      link.setAttribute("download", fn)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
  },
})
