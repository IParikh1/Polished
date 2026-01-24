import axios from 'axios'

// Use environment variable for API base, fallback to relative path for proxy
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Auth token management
let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
}

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    if (authToken) {
      config.headers.Authorization = `Bearer ${authToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - redirect to sign-in
      window.location.href = '/sign-in'
    }
    return Promise.reject(error)
  }
)

// Types
export interface Batch {
  batch_id: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_resumes: number
  processed_resumes: number
  created_at: string
  updated_at: string
  job_description?: string
  premium_features: string[]
  settings: Record<string, unknown>
  progress_percent: number
}

export interface Resume {
  resume_id: string
  batch_id: string
  filename: string
  status: 'pending' | 'processing' | 'scored' | 'failed'
  created_at: string
  updated_at: string
  rank?: number
  scores?: {
    overall: number
    experience?: number
    skills?: number
    education?: number
    formatting?: number
    keywords?: number
  }
  extracted_data?: {
    name?: string
    email?: string
    phone?: string
    skills?: string[]
    years_of_experience?: number
    summary?: string
  }
  jd_match?: {
    match_score: number
    matched_skills: string[]
    missing_skills: string[]
    recommendation?: string
  }
  deep_analysis?: {
    strengths: string[]
    weaknesses: string[]
    recommendations: string[]
    overall_assessment?: string
    red_flags?: string[]
    interview_questions?: string[]
    growth_potential?: string
  }
  download_url?: string
}

export interface BatchListResponse {
  batches: Batch[]
  total: number
  limit: number
  offset: number
}

export interface RankingResponse {
  batch_id: string
  resumes: Resume[]
  total: number
}

export interface CreateBatchRequest {
  name?: string
  job_description?: string
  premium_features?: string[]
  settings?: Record<string, unknown>
}

export interface ExportRequest {
  format: 'json' | 'csv'
  include_scores?: boolean
  include_extracted_data?: boolean
  include_jd_match?: boolean
  include_deep_analysis?: boolean
}

export interface ExportResponse {
  export_id: string
  batch_id: string
  format: string
  download_url: string
  created_at: string
  record_count: number
}

export interface UploadUrlResponse {
  resume_id: string
  upload_url: string
  s3_key: string
  content_type: string
}

// API Functions
export async function listBatches(limit = 50, offset = 0): Promise<BatchListResponse> {
  const response = await api.get<BatchListResponse>('/batches', {
    params: { limit, offset },
  })
  return response.data
}

export async function getBatch(batchId: string): Promise<Batch> {
  const response = await api.get<Batch>(`/batches/${batchId}`)
  return response.data
}

export async function createBatch(data: CreateBatchRequest): Promise<Batch> {
  const response = await api.post<Batch>('/batches', data)
  return response.data
}

export async function updateBatch(batchId: string, data: Partial<CreateBatchRequest>): Promise<Batch> {
  const response = await api.patch<Batch>(`/batches/${batchId}`, data)
  return response.data
}

export async function deleteBatch(batchId: string): Promise<void> {
  await api.delete(`/batches/${batchId}`)
}

export async function reopenBatch(batchId: string): Promise<Batch> {
  const response = await api.post<Batch>(`/batches/${batchId}/reopen`)
  return response.data
}

export async function closeBatch(batchId: string): Promise<Batch> {
  const response = await api.post<Batch>(`/batches/${batchId}/close`)
  return response.data
}

export type SalesRole = 'entry_sdr' | 'sdr' | 'account_executive' | 'senior_ae' | 'account_manager' | 'sales_manager'

export async function uploadResume(
  batchId: string,
  file: File,
  targetRole?: SalesRole
): Promise<{ resume_id: string }> {
  const formData = new FormData()
  formData.append('file', file)
  if (targetRole) {
    formData.append('target_role', targetRole)
  }

  const response = await api.post(`/batches/${batchId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export async function uploadMultipleResumes(
  batchId: string,
  files: File[],
  targetRole?: SalesRole
): Promise<{ batch_id: string; uploaded: number; failed: number; results: Array<{ resume_id?: string; filename: string; status: string; error?: string }> }> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })
  if (targetRole) {
    formData.append('target_role', targetRole)
  }

  const response = await api.post(`/batches/${batchId}/upload-multiple`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export async function processBatch(batchId: string): Promise<{ message: string; batch_id: string; status: string }> {
  const response = await api.post(`/batches/${batchId}/process`)
  return response.data
}

export async function getProcessingStatus(batchId: string): Promise<{
  batch_id: string
  status: string
  total_resumes: number
  processed_resumes: number
  progress_percent: number
}> {
  const response = await api.get(`/batches/${batchId}/processing-status`)
  return response.data
}

export async function getBatchResumes(
  batchId: string,
  includeDownloadUrls = false
): Promise<{ batch_id: string; total: number; resumes: Resume[] }> {
  const response = await api.get(`/batches/${batchId}/resumes`, {
    params: { include_download_urls: includeDownloadUrls },
  })
  return response.data
}

export async function getResume(
  batchId: string,
  resumeId: string,
  includeDownloadUrl = true
): Promise<Resume> {
  const response = await api.get(`/batches/${batchId}/resumes/${resumeId}`, {
    params: { include_download_url: includeDownloadUrl },
  })
  return response.data
}

export async function getRankings(
  batchId: string,
  options?: {
    min_score?: number
    max_score?: number
    limit?: number
    offset?: number
  }
): Promise<RankingResponse> {
  const response = await api.get<RankingResponse>(`/batches/${batchId}/rankings`, {
    params: options,
  })
  return response.data
}

export async function exportBatch(batchId: string, options: ExportRequest): Promise<ExportResponse> {
  const response = await api.post<ExportResponse>(`/batches/${batchId}/export`, options)
  return response.data
}

export async function listExports(batchId: string): Promise<{ batch_id: string; exports: Array<{ key: string; export_id: string; format: string; download_url: string }> }> {
  const response = await api.get(`/batches/${batchId}/exports`)
  return response.data
}

// ==================== JD Matching API (Tech Sales) ====================

export interface JDMatchRequest {
  batch_id?: string
  resume_id?: string
  session_id?: string
  job_description: string
  job_url?: string
  job_title?: string
  company?: string
  target_role?: SalesRole
}

export interface JDMatchResult {
  match_score: number
  matching_requirements: string[]
  gaps: string[]
  keywords_to_add: string[]
  keywords_present: string[]
  tailored_suggestions: string[]
  experience_match: boolean
  skills_alignment?: Record<string, Record<string, string[]>>
}

export interface TailoredResumeRequest {
  batch_id?: string
  resume_id?: string
  session_id?: string
  job_description: string
  target_role?: SalesRole
  prioritize_gaps?: boolean
  include_metrics_prompts?: boolean
}

export interface TailoredResumeResponse {
  tailored_resume: string
  changes_made: string[]
  metrics_needed: Array<{
    company: string
    role: string
    questions: string[]
  }>
  match_improvement?: number
}

export interface SetRoleRequest {
  batch_id?: string
  resume_id?: string
  session_id?: string
  role: SalesRole
}

export interface SetRoleResponse {
  message: string
  role: SalesRole
  role_display_name: string
}

export async function matchJobDescription(request: JDMatchRequest): Promise<JDMatchResult> {
  const response = await api.post<JDMatchResult>('/batches/match-jd', request)
  return response.data
}

export async function matchResumeToJD(
  batchId: string,
  resumeId: string,
  jobDescription: string,
  jobTitle?: string,
  targetRole?: SalesRole
): Promise<JDMatchResult> {
  const response = await api.post<JDMatchResult>(
    `/batches/${batchId}/resumes/${resumeId}/match-jd`,
    null,
    {
      params: {
        job_description: jobDescription,
        job_title: jobTitle,
        target_role: targetRole,
      },
    }
  )
  return response.data
}

export async function tailorResume(request: TailoredResumeRequest): Promise<TailoredResumeResponse> {
  const response = await api.post<TailoredResumeResponse>('/batches/tailor-resume', request)
  return response.data
}

export async function setResumeRole(
  batchId: string,
  resumeId: string,
  role: SalesRole
): Promise<SetRoleResponse> {
  const response = await api.post<SetRoleResponse>(
    `/batches/${batchId}/resumes/${resumeId}/set-role`,
    { role }
  )
  return response.data
}

export async function parseJobDescription(jobDescription: string): Promise<{
  required_skills: string[]
  experience_requirements: { min_years?: number; max_years?: number; areas?: string[] }
  education_requirements: { degree_level?: string; fields?: string[]; required?: boolean }
  keywords: string[]
  nice_to_haves: string[]
  sales_methodologies?: string[]
  sales_tools?: Record<string, string[]>
  detected_role?: string
  quota_requirements?: { requires_quota_achievement: boolean; quota_percentage?: number }
}> {
  const response = await api.get('/batches/parse-jd', {
    params: { job_description: jobDescription },
  })
  return response.data
}

// ==================== Resume Writing API ====================

export type ResumeTemplate = 'modern' | 'classic' | 'ats_friendly' | 'executive' | 'minimal'
export type DocumentFormat = 'pdf' | 'docx' | 'txt' | 'html'

export interface ExperienceEntry {
  company: string
  title: string
  dates?: string
  location?: string
  bullets: string[]
}

export interface EducationEntry {
  school: string
  degree?: string
  field?: string
  year?: string
  gpa?: string
}

export interface ResumeGenerateRequest {
  resume_id?: string
  batch_id?: string
  session_id?: string
  target_role: SalesRole
  job_description?: string
  metrics?: Record<string, Record<string, string>>
  template?: ResumeTemplate
}

export interface ResumeGenerateResponse {
  resume_text: string
  sections: Record<string, string>
  changes_made: string[]
  keywords_added: string[]
  suggestions: string[]
  template: ResumeTemplate
  estimated_match_improvement?: number
}

export interface RewriteSectionRequest {
  resume_id?: string
  batch_id?: string
  session_id?: string
  section_name: string
  section_content: string
  target_role: SalesRole
  context?: string
  job_description?: string
}

export interface RewriteSectionResponse {
  section_name: string
  original: string
  rewritten: string
  changes: string[]
  improvement_score: number
}

export interface GenerateSummaryRequest {
  resume_id?: string
  batch_id?: string
  session_id?: string
  target_role: SalesRole
  job_description?: string
  tone?: 'professional' | 'confident' | 'dynamic'
}

export interface GenerateSummaryResponse {
  standard: string
  confident: string
  dynamic: string
}

export interface EnhanceBulletsRequest {
  resume_id?: string
  batch_id?: string
  bullets: string[]
  target_role: SalesRole
  company_context?: string
}

export interface EnhancedBullet {
  original: string
  enhanced: string
  needs_metrics: boolean
}

export interface EnhanceBulletsResponse {
  bullets: EnhancedBullet[]
  metrics_questions: string[]
}

export interface ExportResumeRequest {
  resume_id?: string
  batch_id?: string
  session_id?: string
  resume_text?: string
  format?: DocumentFormat
  template?: ResumeTemplate
  name?: string
  email?: string
  phone?: string
  location?: string
  linkedin?: string
  summary?: string
  experience?: ExperienceEntry[]
  education?: EducationEntry[]
  skills?: string[]
  certifications?: string[]
}

export interface ExportResumeResponse {
  download_url: string
  format: DocumentFormat
  filename: string
  expires_at: string
  file_size_bytes?: number
}

export interface ResumeTemplateInfo {
  id: string
  name: string
  description: string
  recommended_for: string[]
}

export interface RoleInfo {
  id: string
  name: string
  experience_range: string
  key_metrics: string[]
}

export interface WritingStatus {
  available: boolean
  llm_enabled: boolean
  supported_formats: string[]
  supported_templates: string[]
  features: {
    full_resume_generation: boolean
    section_rewriting: boolean
    summary_generation: boolean
    bullet_enhancement: boolean
    document_export: boolean
  }
}

export async function generateResume(request: ResumeGenerateRequest): Promise<ResumeGenerateResponse> {
  const response = await api.post<ResumeGenerateResponse>('/resume/generate', request)
  return response.data
}

export async function rewriteSection(request: RewriteSectionRequest): Promise<RewriteSectionResponse> {
  const response = await api.post<RewriteSectionResponse>('/resume/rewrite-section', request)
  return response.data
}

export async function generateSummary(request: GenerateSummaryRequest): Promise<GenerateSummaryResponse> {
  const response = await api.post<GenerateSummaryResponse>('/resume/generate-summary', request)
  return response.data
}

export async function enhanceBullets(request: EnhanceBulletsRequest): Promise<EnhanceBulletsResponse> {
  const response = await api.post<EnhanceBulletsResponse>('/resume/enhance-bullets', request)
  return response.data
}

export async function exportResume(request: ExportResumeRequest): Promise<ExportResumeResponse> {
  const response = await api.post<ExportResumeResponse>('/resume/export', request)
  return response.data
}

export async function listResumeTemplates(): Promise<{ templates: ResumeTemplateInfo[] }> {
  const response = await api.get('/resume/templates')
  return response.data
}

export async function listSalesRoles(): Promise<{ roles: RoleInfo[] }> {
  const response = await api.get('/resume/roles')
  return response.data
}

export async function getWritingStatus(): Promise<WritingStatus> {
  const response = await api.get<WritingStatus>('/resume/writing-status')
  return response.data
}

// ==================== Metrics Extraction API ====================

export interface ExtractedMetric {
  metric_type: string
  value: string
  context: string
}

export interface MissingMetric {
  metric_type: string
  question: string
  company: string
  role: string
  priority: number
}

export interface MetricsExtractionRequest {
  batch_id: string
  resume_id: string
  target_role: SalesRole
}

export interface MetricsExtractionResponse {
  metrics_found: ExtractedMetric[]
  metrics_missing: MissingMetric[]
  overall_score: number
  recommendations: string[]
}

export interface MetricsFormatRequest {
  metrics: Record<string, Record<string, string>>
  target_role: SalesRole
}

export interface MetricsFormatResponse {
  formatted_metrics: Record<string, string>
}

export async function extractMetrics(request: MetricsExtractionRequest): Promise<MetricsExtractionResponse> {
  const response = await api.post<MetricsExtractionResponse>('/resume/extract-metrics', null, {
    params: {
      batch_id: request.batch_id,
      resume_id: request.resume_id,
      target_role: request.target_role,
    },
  })
  return response.data
}

export async function formatMetrics(request: MetricsFormatRequest): Promise<MetricsFormatResponse> {
  const response = await api.post<MetricsFormatResponse>('/resume/format-metrics', request.metrics, {
    params: {
      target_role: request.target_role,
    },
  })
  return response.data
}

// ==================== LLM Configuration Status API ====================

export interface LLMServiceStatus {
  available: boolean
  features?: {
    full_resume_generation: boolean
    section_rewriting: boolean
    summary_generation: boolean
    bullet_enhancement: boolean
  }
  llm_enhanced?: boolean
}

export interface LLMConfigStatus {
  llm_configured: boolean
  api_key_set: boolean
  api_key_prefix: string | null
  anthropic_package_installed: boolean
  services: {
    resume_writer: LLMServiceStatus
    metrics_extraction: LLMServiceStatus
  }
  configuration_help: {
    railway: string
    local: string
    get_key_url: string
  }
}

export async function getLLMConfigStatus(): Promise<LLMConfigStatus> {
  const response = await api.get<LLMConfigStatus>('/config/llm-status')
  return response.data
}

export default api
