import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface ConsultingSession {
  session_id: string
  resume_id: string
  batch_id: string
  target_role?: string
  status: string
  created_at: string
}

export interface AnalysisResponse {
  session_id: string
  analysis_type: string
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  section_feedback: Record<string, string>
  overall_assessment: string
  improvement_priority: string[]
}

export interface RewriteResponse {
  session_id: string
  section: string
  original_text: string
  rewritten_text: string
  changes_made: string[]
  improvement_score: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  session_id: string
  messages: ChatMessage[]
  suggestions: string[]
}

export interface CreateSessionRequest {
  resume_id: string
  batch_id: string
  target_role?: string
  job_description?: string
}

// API Functions
export async function createSession(data: CreateSessionRequest): Promise<ConsultingSession> {
  const response = await api.post<ConsultingSession>('/consulting/sessions', data)
  return response.data
}

export async function getSession(sessionId: string): Promise<ConsultingSession & { message_count: number }> {
  const response = await api.get(`/consulting/sessions/${sessionId}`)
  return response.data
}

export async function analyzeResume(
  sessionId: string,
  analysisType: 'comprehensive' | 'quick' | 'targeted' = 'comprehensive'
): Promise<AnalysisResponse> {
  const response = await api.post<AnalysisResponse>('/consulting/analyze', {
    session_id: sessionId,
    analysis_type: analysisType,
  })
  return response.data
}

export async function rewriteSection(
  sessionId: string,
  section: 'summary' | 'experience' | 'skills',
  options?: {
    context?: string
    tone?: 'professional' | 'creative' | 'technical'
  }
): Promise<RewriteResponse> {
  const response = await api.post<RewriteResponse>('/consulting/rewrite', {
    session_id: sessionId,
    section,
    ...options,
  })
  return response.data
}

export async function sendChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/consulting/chat', {
    session_id: sessionId,
    message,
  })
  return response.data
}

export async function getChatHistory(sessionId: string): Promise<{ session_id: string; messages: ChatMessage[]; message_count: number }> {
  const response = await api.get(`/consulting/chat/${sessionId}/history`)
  return response.data
}

export default api
