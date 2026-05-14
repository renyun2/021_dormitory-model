import axios from 'axios'

const base = import.meta.env.VITE_API_BASE || '/api'

export const http = axios.create({
  baseURL: base,
  timeout: 30000,
})
