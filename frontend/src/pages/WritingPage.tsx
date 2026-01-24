import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Sparkles,
  FileText,
  BarChart3,
  PenLine,
  ArrowLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  Lock,
} from 'lucide-react'
import clsx from 'clsx'
import { useBatches } from '../hooks/useBatches'
import { useBatchResumes } from '../hooks/useRankings'
import { useWritingStatus } from '../hooks/useResumeWriting'
import { useSubscription } from '../hooks/useSubscription'
import {
  ResumeWriter,
  MetricsExtractor,
  SectionRewriter,
} from '../components/writing'
import { SalesRoleSelector, type SalesRole } from '../components/batch/SalesRoleSelector'
import { FeatureGate } from '../components/paywall'

type WritingMode = 'select' | 'full' | 'metrics' | 'sections'

interface ModeOption {
  id: WritingMode
  title: string
  description: string
  icon: typeof Sparkles
  color: string
}

const modeOptions: ModeOption[] = [
  {
    id: 'full',
    title: 'Full Resume Generation',
    description: 'Generate a complete optimized resume for your target role',
    icon: Sparkles,
    color: 'bg-primary-100 text-primary-600',
  },
  {
    id: 'metrics',
    title: 'Metrics Extraction',
    description: 'Extract and enhance sales metrics from your resume',
    icon: BarChart3,
    color: 'bg-blue-100 text-blue-600',
  },
  {
    id: 'sections',
    title: 'Section Rewriter',
    description: 'Rewrite specific sections of your resume',
    icon: PenLine,
    color: 'bg-purple-100 text-purple-600',
  },
]

export default function WritingPage() {
  const { batchId: urlBatchId, resumeId: urlResumeId } = useParams()
  const navigate = useNavigate()

  const [selectedBatchId, setSelectedBatchId] = useState<string>(urlBatchId || '')
  const [selectedResumeId, setSelectedResumeId] = useState<string>(urlResumeId || '')
  const [targetRole, setTargetRole] = useState<SalesRole | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [mode, setMode] = useState<WritingMode>('select')
  const [showJdInput, setShowJdInput] = useState(false)

  const { data: batchesData, isLoading: batchesLoading } = useBatches()
  const { data: resumesData, isLoading: resumesLoading } = useBatchResumes(selectedBatchId || undefined)
  const { data: writingStatus, isLoading: statusLoading } = useWritingStatus()
  const { data: subscription } = useSubscription()

  const hasResumeWriting = subscription?.features?.includes('resume_writing') ?? false

  const selectedResume = resumesData?.resumes?.find(r => r.resume_id === selectedResumeId)

  const isReady = selectedBatchId && selectedResumeId && targetRole

  // Handle back navigation
  const handleBack = () => {
    if (mode !== 'select') {
      setMode('select')
    } else {
      navigate('/writing')
    }
  }

  // Reset state when batch changes
  const handleBatchChange = (batchId: string) => {
    setSelectedBatchId(batchId)
    setSelectedResumeId('')
    setTargetRole(null)
  }

  // Loading state
  if (statusLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    )
  }

  // Service unavailable
  if (!writingStatus?.available) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Resume Writing</h1>
          <p className="text-gray-600">AI-powered resume optimization for tech sales professionals</p>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 text-amber-600 mb-4">
            <AlertCircle className="w-6 h-6" />
            <span className="font-semibold">Service Temporarily Unavailable</span>
          </div>
          <p className="text-gray-600">
            The AI-powered resume writing service is currently unavailable.
            Please try again later or contact support if this persists.
          </p>
        </div>
      </div>
    )
  }

  // Selection view - choose batch/resume
  if (!urlBatchId || !urlResumeId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Resume Writing</h1>
          <p className="text-gray-600">AI-powered resume optimization for tech sales professionals</p>
        </div>

        <div className="max-w-2xl">
          <div className="card p-6 space-y-6">
            <div className="flex items-center gap-3 text-primary-600">
              <Sparkles className="w-6 h-6" />
              <h2 className="text-lg font-semibold">Select a Resume to Optimize</h2>
            </div>

            <div className="space-y-4">
              {/* Batch Selection */}
              <div>
                <label className="label">Select Batch</label>
                <select
                  value={selectedBatchId}
                  onChange={(e) => handleBatchChange(e.target.value)}
                  className="input"
                  disabled={batchesLoading}
                >
                  <option value="">Choose a batch...</option>
                  {batchesData?.batches.map((batch) => (
                    <option key={batch.batch_id} value={batch.batch_id}>
                      {batch.name} ({batch.total_resumes} resumes)
                    </option>
                  ))}
                </select>
              </div>

              {/* Resume Selection */}
              {selectedBatchId && (
                <div>
                  <label className="label">Select Resume</label>
                  <select
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    className="input"
                    disabled={resumesLoading}
                  >
                    <option value="">Choose a resume...</option>
                    {resumesData?.resumes?.map((resume) => (
                      <option key={resume.resume_id} value={resume.resume_id}>
                        {resume.filename}
                        {resume.extracted_data?.name && ` - ${resume.extracted_data.name}`}
                        {resume.scores?.overall !== undefined && ` (Score: ${resume.scores.overall})`}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Role Selection */}
              {selectedResumeId && (
                <div className="pt-2">
                  <SalesRoleSelector
                    value={targetRole}
                    onChange={setTargetRole}
                  />
                </div>
              )}

              {/* Job Description Toggle */}
              {targetRole && (
                <div>
                  <button
                    onClick={() => setShowJdInput(!showJdInput)}
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    <ChevronRight className={clsx('w-4 h-4 transition-transform', showJdInput && 'rotate-90')} />
                    {showJdInput ? 'Hide' : 'Add'} Job Description (Optional)
                  </button>

                  {showJdInput && (
                    <textarea
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="Paste a job description to tailor your resume..."
                      className="input mt-2 min-h-[100px] resize-y"
                    />
                  )}
                </div>
              )}

              {/* Continue Button */}
              <button
                onClick={() => navigate(`/writing/${selectedBatchId}/${selectedResumeId}`)}
                disabled={!isReady}
                className="w-full btn-primary gap-2 py-3"
              >
                <FileText className="w-5 h-5" />
                Continue to Writing Tools
              </button>

              {/* Features List */}
              <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Available Tools</h3>
                <div className="grid gap-3">
                  {modeOptions.map((option) => (
                    <div key={option.id} className="flex items-start gap-3">
                      <div className={clsx('p-2 rounded-lg', option.color)}>
                        <option.icon className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">{option.title}</h4>
                        <p className="text-xs text-gray-500">{option.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Mode selection view - choose what to do
  if (mode === 'select') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/writing')} className="btn-secondary p-2">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Resume Writing</h1>
            <p className="text-gray-600">
              {selectedResume?.extracted_data?.name || selectedResume?.filename || 'Selected Resume'}
              {targetRole && ` - Targeting ${targetRole.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`}
            </p>
          </div>
        </div>

        {/* Role Selection if not set */}
        {!targetRole && (
          <div className="card p-6 max-w-xl">
            <h2 className="font-semibold text-gray-900 mb-4">First, select your target role:</h2>
            <SalesRoleSelector
              value={targetRole}
              onChange={setTargetRole}
            />
          </div>
        )}

        {/* Mode Selection */}
        {targetRole && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {modeOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => setMode(option.id)}
                className="card p-6 text-left hover:shadow-lg transition-shadow group"
              >
                <div className={clsx('p-3 rounded-lg w-fit mb-4', option.color)}>
                  <option.icon className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
                  {option.title}
                </h3>
                <p className="text-sm text-gray-600">{option.description}</p>
                <div className="mt-4 flex items-center text-primary-600 text-sm font-medium">
                  Get Started
                  <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Quick Stats */}
        {selectedResume && (
          <div className="card p-4">
            <h3 className="font-medium text-gray-900 mb-3">Resume Overview</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {selectedResume.scores?.overall || 'N/A'}
                </p>
                <p className="text-xs text-gray-500">Overall Score</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {selectedResume.extracted_data?.skills?.length || 0}
                </p>
                <p className="text-xs text-gray-500">Skills Found</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {selectedResume.extracted_data?.years_of_experience || 'N/A'}
                </p>
                <p className="text-xs text-gray-500">Years Experience</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {selectedResume.jd_match?.match_score || 'N/A'}
                </p>
                <p className="text-xs text-gray-500">JD Match</p>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Full Resume Generation Mode
  if (mode === 'full') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={handleBack} className="btn-secondary p-2">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Full Resume Generation</h1>
            <p className="text-gray-600">Create an optimized resume for your target role</p>
          </div>
        </div>

        <FeatureGate feature="resume_writing">
          <ResumeWriter
            batchId={urlBatchId}
            resumeId={urlResumeId}
            initialRole={targetRole || undefined}
            extractedData={selectedResume?.extracted_data}
          />
        </FeatureGate>
      </div>
    )
  }

  // Metrics Extraction Mode
  if (mode === 'metrics') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={handleBack} className="btn-secondary p-2">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Metrics Extraction</h1>
            <p className="text-gray-600">Extract and enhance sales metrics from your resume</p>
          </div>
        </div>

        <div className="max-w-2xl">
          <FeatureGate feature="resume_writing">
            <MetricsExtractor
              batchId={urlBatchId}
              resumeId={urlResumeId}
              targetRole={targetRole!}
              onMetricsCollected={(metrics) => {
                console.log('Collected metrics:', metrics)
              }}
            />
          </FeatureGate>
        </div>

        {/* Tips */}
        <div className="max-w-2xl card p-4 bg-blue-50 border-blue-100">
          <h4 className="font-medium text-blue-900 mb-2">Why Metrics Matter</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>- Hiring managers spend 7 seconds scanning your resume</li>
            <li>- Quantified achievements are 40% more memorable</li>
            <li>- Sales resumes with metrics get 2x more interviews</li>
            <li>- ATS systems rank metric-rich resumes higher</li>
          </ul>
        </div>
      </div>
    )
  }

  // Section Rewriter Mode
  if (mode === 'sections') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={handleBack} className="btn-secondary p-2">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Section Rewriter</h1>
            <p className="text-gray-600">Improve specific sections of your resume</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FeatureGate feature="resume_writing">
            <SectionRewriter
              batchId={urlBatchId}
              resumeId={urlResumeId}
              targetRole={targetRole!}
              jobDescription={jobDescription || undefined}
            />
          </FeatureGate>

          {/* Tips Panel */}
          <div className="space-y-4">
            <div className="card p-4">
              <h3 className="font-medium text-gray-900 mb-3">Section Guidelines</h3>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Professional Summary</h4>
                  <p className="text-sm text-gray-600">
                    3-4 sentences highlighting your sales achievements, years of experience, and target role.
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-700">Experience</h4>
                  <p className="text-sm text-gray-600">
                    Use bullet points starting with action verbs. Include metrics for every role.
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-700">Skills</h4>
                  <p className="text-sm text-gray-600">
                    Include sales tools (Salesforce, HubSpot), methodologies (MEDDIC, SPIN), and soft skills.
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-700">Education</h4>
                  <p className="text-sm text-gray-600">
                    Include relevant certifications and training (Sandler, Challenger, etc.).
                  </p>
                </div>
              </div>
            </div>

            {/* Power Words */}
            <div className="card p-4 bg-purple-50 border-purple-100">
              <h4 className="font-medium text-purple-900 mb-2">Power Words for Sales</h4>
              <div className="flex flex-wrap gap-2">
                {['Exceeded', 'Generated', 'Closed', 'Negotiated', 'Prospected', 'Accelerated', 'Developed', 'Expanded'].map((word) => (
                  <span
                    key={word}
                    className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full"
                  >
                    {word}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return null
}
