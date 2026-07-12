import axios from "axios"

const api = axios.create({ baseURL: "/api" })

export const projectApi = {
  list(params) {
    return api.get("/project", { params })
  },
  get(id) {
    return api.get(`/project/${id}`)
  },
  create(data) {
    return api.post("/project", data)
  },
  update(id, data) {
    return api.put(`/project/${id}`, data)
  },
  remove(id) {
    return api.delete(`/project/${id}`)
  },
}
