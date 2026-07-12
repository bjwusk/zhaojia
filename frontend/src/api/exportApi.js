import axios from "axios"

const api = axios.create({ baseURL: "/api" })

export const exportApi = {
  exportExcel(versionId) {
    return api.get(`/export/excel/${versionId}`, { responseType: "blob" })
  },
  exportWord(versionId) {
    return api.get(`/export/word/${versionId}`, { responseType: "blob" })
  },
  exportAll(versionId) {
    return api.get(`/export/version/${versionId}/export-all`)
  },
}
