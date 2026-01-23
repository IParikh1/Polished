import { useState } from 'react'
import { Target, Sparkles, Loader2, ChevronDown, ChevronUp, FileText } from 'lucide-react'
import { useMatchJD } from '../../hooks/useJDMatching'
import MatchResults from './MatchResults'
import type { SalesRole } from '../../api/batchClient'

interface JDMatcherProps {
  batchId: string
  resumeId: string
  resumeFilename?: string
  currentRole?: SalesRole
  onMatchComplete?: (result: JDMatchResult) => void
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

export default function JDMatcher({
  batchId,
  resumeId,
  resumeFilename,
  currentRole,
  onMatchComplete,
}: JDMatcherProps) {
  const [jobDescription, setJobDescription] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)
  const [matchResult, setMatchResult] = useState<JDMatchResult | null>(null)

  const matchJD = useMatchJD()

  const handleAnalyze = async () => {
    if (!jobDescription.trim() || jobDescription.length < 50) return

    try {
      const result = await matchJD.mutateAsync({
        batch_id: batchId,
        resume_id: resumeId,
        job_description: jobDescription,
        job_title: jobTitle || undefined,
        target_role: currentRole,
      })

      setMatchResult(result)
      onMatchComplete?.(result)
    } catch (error) {
      console.error('Failed to match JD:', error)
    }
  }

  const handleClear = () => {
    setMatchResult(null)
    setJobDescription('')
    setJobTitle('')
  }

  // Collapsed state - show button to expand
  if (!isExpanded && !matchResult) {
    return (
      <div className="card p-4 border border-dashed border-gray-300 bg-gray-50/50">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Target className="w-5 h-5 text-primary-600" />
          </div>
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 text-sm">Match Against Job Description</h4>
            <p className="text-xs text-gray-500">
              See how well this resume fits a specific role
            </p>
          </div>
          <button
            onClick={() => setIsExpanded(true)}
            className="btn-secondary btn-sm gap-1"
          >
            <Sparkles className="w-3 h-3" />
            Analyze
          </button>
        </div>
      </div>
    )
  }

  // Show results if we have them
  if (matchResult) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary-600" />
            <h4 className="font-semibold text-gray-900">JD Match Analysis</h4>
            {resumeFilename && (
              <span className="text-sm text-gray-500">
                for {resumeFilename}
              </span>
            )}
          </div>
          <button
            onClick={handleClear}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Try Another JD
          </button>
        </div>

        <MatchResults result={matchResult} />

        {jobTitle && (
          <p className="text-sm text-gray-500">
            Matched against: <span className="font-medium">{jobTitle}</span>
          </p>
        )}
      </div>
    )
  }

  // Expanded input state
  return (
    <div className="card p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-primary-600" />
          <h4 className="font-semibold text-gray-900">Match Against Job Description</h4>
          <span className="badge-primary text-xs">Premium</span>
        </div>
        <button
          onClick={() => setIsExpanded(false)}
          className="p-1 text-gray-400 hover:text-gray-600 rounded"
        >
          <ChevronUp className="w-4 h-4" />
        </button>
      </div>

      <p className="text-sm text-gray-600">
        Paste a job description to see how well{' '}
        {resumeFilename ? (
          <span className="font-medium">{resumeFilename}</span>
        ) : (
          'this resume'
        )}{' '}
        matches the requirements.
      </p>

      <div className="space-y-3">
        <div>
          <label className="label text-sm">Job Title (optional)</label>
          <input
            type="text"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g., Account Executive, SDR, Enterprise AE"
            className="input text-sm"
          />
        </div>

        <div>
          <label className="label text-sm">Job Description *</label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the full job description here...

Example:
We are looking for an Account Executive with 3+ years of SaaS sales experience. The ideal candidate should have:
- Track record of exceeding quota
- Experience with MEDDIC or similar sales methodology
- Proficiency with Salesforce
- Strong presentation and negotiation skills
..."
            className="input min-h-[180px] text-sm font-mono"
          />
          <p className="text-xs text-gray-500 mt-1">
            {jobDescription.length < 50 ? (
              <span className="text-amber-600">
                Need at least 50 characters ({50 - jobDescription.length} more)
              </span>
            ) : (
              <span className="text-green-600">
                {jobDescription.length} characters
              </span>
            )}
          </p>
        </div>
      </div>

      <div className="flex justify-end gap-3">
        <button
          onClick={() => {
            setIsExpanded(false)
            setJobDescription('')
            setJobTitle('')
          }}
          className="btn-secondary btn-sm"
        >
          Cancel
        </button>
        <button
          onClick={handleAnalyze}
          disabled={jobDescription.length < 50 || matchJD.isPending}
          className="btn-primary btn-sm gap-2"
        >
          {matchJD.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Target className="w-4 h-4" />
              Analyze Match
            </>
          )}
        </button>
      </div>

      {matchJD.isError && (
        <div className="p-3 bg-danger-50 text-danger-700 rounded-lg text-sm">
          Failed to analyze match. Please try again.
        </div>
      )}
    </div>
  )
}
