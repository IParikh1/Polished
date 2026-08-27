import axios from 'axios'

// Use environment variable for API base, fallback to relative path for proxy
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

// Shared authenticated client - other API modules (e.g. consultClient) reuse
// this instance so they pick up the Clerk Bearer token interceptor below.
export const api = axios.create({
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

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear it
      // The ProtectedRoute component will handle redirecting to sign-in
      authToken = null
      // Don't redirect here - let the app's auth flow handle it
      // This avoids redirect loops when auth is still initializing
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
  target_role?: SalesRole
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

export interface FileWithRole {
  file: File
  targetRole?: SalesRole
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

export async function uploadMultipleResumesWithRoles(
  batchId: string,
  filesWithRoles: FileWithRole[]
): Promise<{ batch_id: string; uploaded: number; failed: number; results: Array<{ resume_id?: string; filename: string; status: string; error?: string; target_role?: string }> }> {
  const formData = new FormData()
  const roleMapping: Record<string, string> = {}

  filesWithRoles.forEach(({ file, targetRole }) => {
    formData.append('files', file)
    if (targetRole) {
      roleMapping[file.name] = targetRole
    }
  })

  // Send role mapping as JSON
  if (Object.keys(roleMapping).length > 0) {
    formData.append('role_mapping', JSON.stringify(roleMapping))
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

// ==================== Subscription API ====================

export type SubscriptionTier = 'free' | 'pro' | 'enterprise'
export type SubscriptionStatus = 'active' | 'canceled' | 'past_due' | 'incomplete' | 'trialing'

export interface SubscriptionResponse {
  tier: SubscriptionTier
  status: SubscriptionStatus | null
  is_pro: boolean
  features: string[]
  limits: {
    batches_per_month: number
    resumes_per_batch: number
    total_resumes_per_month: number
    exports_per_month: number
  }
  upgrade_url: string | null
  manage_url: string | null
}

export interface FeatureAccessResponse {
  feature: string
  has_access: boolean
  required_tier: SubscriptionTier
  current_tier: SubscriptionTier
  upgrade_required: boolean
  feature_info?: {
    name: string
    description: string
    icon: string
  }
}

export interface StripeConfig {
  publishable_key: string
  pro_price_id: string
  stripe_configured: boolean
  prices: {
    pro: {
      monthly: number
      price_id: string
    }
  }
}

export interface CheckoutSessionResponse {
  checkout_url: string
  session_id: string
}

export interface PortalSessionResponse {
  portal_url: string
}

export interface PricingTier {
  id: string
  name: string
  price: number | null
  billing: string
  description: string
  features: string[]
  limitations: string[]
  cta: string
  highlighted: boolean
  price_id?: string
}

export interface PricingInfo {
  tiers: PricingTier[]
  faq: Array<{ question: string; answer: string }>
}

export async function getSubscriptionStatus(): Promise<SubscriptionResponse> {
  const response = await api.get<SubscriptionResponse>('/subscription/status')
  return response.data
}

export async function checkFeatureAccess(feature: string): Promise<FeatureAccessResponse> {
  const response = await api.get<FeatureAccessResponse>(`/subscription/features/${feature}`)
  return response.data
}

export async function getAllFeaturesStatus(): Promise<{
  features: FeatureAccessResponse[]
  user_tier: SubscriptionTier
}> {
  const response = await api.get('/subscription/features')
  return response.data
}

export async function getStripeConfig(): Promise<StripeConfig> {
  const response = await api.get<StripeConfig>('/subscription/config')
  return response.data
}

export async function createCheckoutSession(
  priceId: string,
  successUrl: string,
  cancelUrl: string
): Promise<CheckoutSessionResponse> {
  const response = await api.post<CheckoutSessionResponse>('/subscription/checkout', {
    price_id: priceId,
    success_url: successUrl,
    cancel_url: cancelUrl,
  })
  return response.data
}

export async function createPortalSession(returnUrl: string): Promise<PortalSessionResponse> {
  const response = await api.post<PortalSessionResponse>('/subscription/portal', {
    return_url: returnUrl,
  })
  return response.data
}

export async function getPricingInfo(): Promise<PricingInfo> {
  const response = await api.get<PricingInfo>('/subscription/pricing')
  return response.data
}

// ==================== Admin API ====================

export interface UserUsage {
  user_id: string
  period: string
  batches_created: number
  resumes_processed: number
  exports_count: number
  jd_matches: number
  resume_writes: number
  deep_analyses: number
  updated_at: string
}

export interface UserCost {
  batches_cost: number
  resumes_cost: number
  exports_cost: number
  jd_matches_cost: number
  resume_writes_cost: number
  deep_analyses_cost: number
  total_cost: number
}

export interface AdminUser {
  user_id: string
  email: string
  name?: string
  subscription_tier: SubscriptionTier
  subscription_status?: SubscriptionStatus
  is_admin: boolean
  stripe_customer_id?: string
  created_at: string
  updated_at: string
  usage?: UserUsage
  cost?: UserCost
}

export interface AdminUserListResponse {
  users: AdminUser[]
  total: number
  limit: number
  offset: number
}

export interface AdminStatsResponse {
  total_users: number
  users_by_tier: Record<string, number>
  users_by_status: Record<string, number>
  total_batches: number
  total_resumes: number
  total_revenue: number
  period: string
}

export interface ServiceCosts {
  costs_per_unit: Record<string, number>
  description: Record<string, string>
}

export async function getAdminStats(): Promise<AdminStatsResponse> {
  const response = await api.get<AdminStatsResponse>('/admin/stats')
  return response.data
}

export async function getAdminUsers(
  limit = 50,
  offset = 0,
  tier?: string
): Promise<AdminUserListResponse> {
  const response = await api.get<AdminUserListResponse>('/admin/users', {
    params: { limit, offset, tier },
  })
  return response.data
}

export async function getAdminUser(userId: string): Promise<AdminUser> {
  const response = await api.get<AdminUser>(`/admin/users/${userId}`)
  return response.data
}

export async function setUserAdminStatus(
  userId: string,
  isAdmin: boolean
): Promise<{ message: string; user_id: string; is_admin: boolean }> {
  const response = await api.post(`/admin/users/${userId}/admin`, null, {
    params: { is_admin: isAdmin },
  })
  return response.data
}

export async function setUserTier(
  userId: string,
  tier: string
): Promise<{ message: string; user_id: string; tier: string }> {
  const response = await api.post(`/admin/users/${userId}/tier`, null, {
    params: { tier },
  })
  return response.data
}

export async function getAdminUsage(
  period?: string
): Promise<{
  period: string
  user_count: number
  usage_by_user: UserUsage[]
  totals: Record<string, number>
  total_cost: UserCost
}> {
  const response = await api.get('/admin/usage', {
    params: { period },
  })
  return response.data
}

export async function getServiceCosts(): Promise<ServiceCosts> {
  const response = await api.get<ServiceCosts>('/admin/service-costs')
  return response.data
}

// ==================== User Self-Service ====================

export interface CurrentUserResponse {
  user_id: string
  email: string | null
  name: string | null
  is_admin: boolean
  subscription_tier: string
  created: boolean
}

export async function getCurrentUser(email?: string, name?: string): Promise<CurrentUserResponse> {
  const response = await api.get<CurrentUserResponse>('/user/me', {
    params: { email, name },
  })
  return response.data
}

export async function syncUserInfo(): Promise<{ synced: boolean; updates: string[] }> {
  const response = await api.post('/user/me/sync')
  return response.data
}

export default api
