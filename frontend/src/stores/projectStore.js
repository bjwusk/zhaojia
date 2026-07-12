import { defineStore } from "pinia"
import { projectApi } from "../api/projectApi"

export const useProjectStore = defineStore("project", {
  state: () => ({
    projects: [],
    current: null,
    total: 0,
    loading: false,
  }),
  actions: {
    async fetchProjects(params = {}) {
      this.loading = true
      try {
        const res = await projectApi.list(params)
        this.projects = res.data.data
        this.total = res.data.total
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },
    async fetchProject(id) {
      try {
        const res = await projectApi.get(id)
        this.current = res.data.data
        return res.data.data
      } catch (e) {
        console.error(e)
        return null
      }
    },
    async createProject(data) {
      const res = await projectApi.create(data)
      return res.data
    },
    async updateProject(id, data) {
      const res = await projectApi.update(id, data)
      return res.data
    },
    async deleteProject(id) {
      const res = await projectApi.remove(id)
      return res.data
    },
  },
})
