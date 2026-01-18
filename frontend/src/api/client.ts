import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

// Extend axios config to include retry count
interface RetryConfig extends InternalAxiosRequestConfig {
  __retryCount?: number
}

// @ts-ignore - Vite injects this at build time
const API_URL: string = import.meta.env?.VITE_API_URL || ''

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes for Claude responses
})

// Retry logic for timeout and network errors
client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig | undefined
    if (!config) return Promise.reject(error)

    config.__retryCount = config.__retryCount || 0

    // Retry on timeout or network errors (max 2 retries)
    const shouldRetry =
      (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK' || !error.response) &&
      config.__retryCount < 2

    if (shouldRetry) {
      const retryCount = (config.__retryCount || 0) + 1
      config.__retryCount = retryCount
      console.log(`Retrying request (attempt ${retryCount})...`)

      // Wait before retry (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, 1000 * retryCount))
      return client(config)
    }

    return Promise.reject(error)
  }
)

// Keep-alive: ping server every 5 minutes to prevent cold starts
let keepAliveInterval: NodeJS.Timeout | null = null

export function startKeepAlive() {
  if (keepAliveInterval) return

  keepAliveInterval = setInterval(async () => {
    try {
      await client.get('/api/health')
    } catch (e) {
      // Silent fail - just trying to keep server warm
    }
  }, 5 * 60 * 1000) // 5 minutes
}

export function stopKeepAlive() {
  if (keepAliveInterval) {
    clearInterval(keepAliveInterval)
    keepAliveInterval = null
  }
}

export default client
