import axios from 'axios'

// @ts-ignore - Vite injects this at build time
const API_URL: string = import.meta.env?.VITE_API_URL || ''

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default client
