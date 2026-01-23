import { useState } from 'react'
import {
  Sparkles,
  Download,
  RefreshCw,
  AlertCircle,
  FileText,
  Loader2,
} from 'lucide-react'
import { SalesRoleSelector, type SalesRole } from '../batch/SalesRoleSelector'
import TemplateSelector, { type ResumeTemplate } from './TemplateSelector'
import ResumePreview from './ResumePreview'
import ExportModal from './ExportModal'
import {
  useGenerateResume,
  useWritingStatus,
} from '../../hooks/useResumeWriting'

interface ResumeWriterProps {
  batchId: string
  resumeId: string
  initialRole?: SalesRole
  extractedData?: {
    name?: string
    email?: string
    phone?: string
    skills?: string[]
    summary?: string
  }
  onComplete?: () => void
}

export default function ResumeWriter({
  batchId,
  resumeId,
  initialRole,
  extractedData,
  onComplete: _onComplete,
}: ResumeWriterProps) {
  const [targetRole, setTargetRole] = useState<SalesRole | null>(initialRole || null)
  const [template, setTemplate] = useState<ResumeTemplate>('modern')
  const [jobDescription, setJobDescription] = useState('')
  const [showExport, setShowExport] = useState(false)

  const { data: status } = useWritingStatus()
  const generateMutation = useGenerateResume()

  const handleGenerate = async () => {
    if (!targetRole) return

    try {
      await generateMutation.mutateAsync({
        batch_id: batchId,
        resume_id: resumeId,
        target_role: targetRole,
        job_description: jobDescription || undefined,
        template,
      })
    } catch {
      // Error handled by mutation
    }
  }

  const isAvailable = status?.available ?? true

  if (!isAvailable) {
    return (
      <div className="card p-6">
        <div className="flex items-center gap-3 text-amber-600 mb-4">
          <AlertCircle className="w-5 h-5" />
          <span className="font-medium">Resume Writing Unavailable</span>
        </div>
        <p className="text-gray-600 text-sm">
          The AI-powered resume writing service is currently unavailable.
          Please try again later or contact support.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Sparkles className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">AI Resume Writer</h2>
            <p className="text-sm text-gray-500">
              Generate an optimized resume tailored for your target role
            </p>
          </div>
        </div>
        {generateMutation.data && (
          <button
            onClick={() => setShowExport(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <div className="space-y-6">
          {/* Role Selection */}
          <div className="card p-4">
            <SalesRoleSelector
              value={targetRole}
              onChange={setTargetRole}
              disabled={generateMutation.isPending}
            />
          </div>

          {/* Template Selection */}
          <div className="card p-4">
            <TemplateSelector
              value={template}
              onChange={setTemplate}
              disabled={generateMutation.isPending}
            />
          </div>

          {/* Job Description (optional) */}
          <div className="card p-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Job Description (Optional)
            </label>
            <p className="text-sm text-gray-500 mb-3">
              Paste a job description to further tailor your resume
            </p>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste job description here..."
              className="input min-h-[120px] resize-y"
              disabled={generateMutation.isPending}
            />
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={!targetRole || generateMutation.isPending}
            className="btn-primary w-full flex items-center justify-center gap-2 py-3"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : generateMutation.data ? (
              <>
                <RefreshCw className="w-5 h-5" />
                Regenerate Resume
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Optimized Resume
              </>
            )}
          </button>

          {generateMutation.isError && (
            <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>
                {generateMutation.error?.message || 'Failed to generate resume'}
              </span>
            </div>
          )}

          {/* Tips */}
          {!generateMutation.data && (
            <div className="card p-4 bg-blue-50 border-blue-100">
              <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Tips for Best Results
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>- Select the specific role you are targeting</li>
                <li>- Include a job description for better keyword matching</li>
                <li>- Use ATS-Friendly template for online applications</li>
                <li>- Review and personalize the generated content</li>
              </ul>
            </div>
          )}
        </div>

        {/* Preview Panel */}
        <div>
          <ResumePreview
            resumeText={generateMutation.data?.resume_text || ''}
            sections={generateMutation.data?.sections}
            changesMode={generateMutation.data?.changes_made}
            keywordsAdded={generateMutation.data?.keywords_added}
            suggestions={generateMutation.data?.suggestions}
            matchImprovement={generateMutation.data?.estimated_match_improvement}
            isLoading={generateMutation.isPending}
          />
        </div>
      </div>

      {/* Export Modal */}
      <ExportModal
        isOpen={showExport}
        onClose={() => setShowExport(false)}
        batchId={batchId}
        resumeId={resumeId}
        resumeText={generateMutation.data?.resume_text}
        template={template}
        resumeData={extractedData}
      />
    </div>
  )
}
