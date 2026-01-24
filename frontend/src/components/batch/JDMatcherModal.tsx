import { useState } from 'react'
import { X, Target, Loader2, Sparkles, FileText } from 'lucide-react'
import type { Resume, SalesRole } from '../../api/batchClient'
import { useMatchJD } from '../../hooks/useJDMatching'
import { useSubscription } from '../../hooks/useSubscription'
import MatchResults from './MatchResults'
import UpgradeModal from '../paywall/UpgradeModal'
import type { JDMatchResult } from './JDMatcher'

interface JDMatcherModalProps {
  batchId: string
  resume: Resume
  onClose: () => void
}

const SALES_ROLES: { value: SalesRole; label: string }[] = [
  { value: 'entry_sdr', label: 'Entry-Level SDR (0-1 years)' },
  { value: 'sdr', label: 'SDR/BDR (1-3 years)' },
  { value: 'account_executive', label: 'Account Executive (2-5 years)' },
  { value: 'senior_ae', label: 'Senior/Enterprise AE (5+ years)' },
  { value: 'account_manager', label: 'Account Manager / CSM' },
  { value: 'sales_manager', label: 'Sales Manager / Director' },
]

export default function JDMatcherModal({ batchId, resume, onClose }: JDMatcherModalProps) {
  const [jobDescription, setJobDescription] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [targetRole, setTargetRole] = useState<SalesRole | ''>('')
  const [matchResult, setMatchResult] = useState<JDMatchResult | null>(null)
  const [showUpgrade, setShowUpgrade] = useState(false)

  const matchJD = useMatchJD()
  const { data: subscription } = useSubscription()

  const hasJdMatching = subscription?.features?.includes('jd_matching') ?? false

  // If user doesn't have JD matching, show upgrade modal
  if (!hasJdMatching) {
    return (
      <>
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md bg-white rounded-xl shadow-xl p-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-amber-100 rounded-full flex items-center justify-center">
                <Target className="w-8 h-8 text-amber-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                Upgrade to Unlock JD Matching
              </h2>
              <p className="text-gray-600 mb-6">
                JD Matching is a Pro feature. Upgrade to match resumes against job descriptions
                with AI-powered skill matching and gap analysis.
              </p>
              <div className="flex gap-3">
                <button onClick={onClose} className="flex-1 btn-secondary">
                  Close
                </button>
                <button
                  onClick={() => setShowUpgrade(true)}
                  className="flex-1 btn-primary bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600"
                >
                  Upgrade to Pro
                </button>
              </div>
            </div>
          </div>
        </div>
        <UpgradeModal
          isOpen={showUpgrade}
          onClose={() => {
            setShowUpgrade(false)
            onClose()
          }}
          feature="jd_matching"
        />
      </>
    )
  }

  const handleAnalyze = async () => {
    if (!jobDescription.trim() || jobDescription.length < 50) return

    try {
      const result = await matchJD.mutateAsync({
        batch_id: batchId,
        resume_id: resume.resume_id,
        job_description: jobDescription,
        job_title: jobTitle || undefined,
        target_role: targetRole || undefined,
      })

      setMatchResult(result)
    } catch (error) {
      console.error('Failed to match JD:', error)
    }
  }

  const handleReset = () => {
    setMatchResult(null)
    setJobDescription('')
    setJobTitle('')
    setTargetRole('')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-xl shadow-xl">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Target className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">JD Match Analysis</h2>
              <p className="text-sm text-gray-500">
                {resume.extracted_data?.name || resume.filename}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {matchResult ? (
            <>
              <MatchResults result={matchResult} />

              {jobTitle && (
                <p className="text-sm text-gray-500">
                  Matched against: <span className="font-medium">{jobTitle}</span>
                </p>
              )}

              <div className="flex justify-between items-center pt-4 border-t">
                <button
                  onClick={handleReset}
                  className="btn-secondary"
                >
                  Try Another JD
                </button>
                <button
                  onClick={onClose}
                  className="btn-primary"
                >
                  Done
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Resume Info */}
              <div className="p-4 bg-gray-50 rounded-lg flex items-center gap-3">
                <FileText className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900">
                    {resume.extracted_data?.name || 'Candidate'}
                  </p>
                  <p className="text-sm text-gray-500">{resume.filename}</p>
                  {resume.scores?.overall && (
                    <p className="text-xs text-gray-400 mt-1">
                      Overall Score: {resume.scores.overall.toFixed(1)}
                    </p>
                  )}
                </div>
              </div>

              {/* Job Title */}
              <div>
                <label className="label">Job Title (optional)</label>
                <input
                  type="text"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="e.g., Account Executive, SDR, Enterprise AE"
                  className="input"
                />
              </div>

              {/* Target Role */}
              <div>
                <label className="label">Target Sales Role (optional)</label>
                <select
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value as SalesRole | '')}
                  className="input"
                >
                  <option value="">Auto-detect from JD</option>
                  {SALES_ROLES.map((role) => (
                    <option key={role.value} value={role.value}>
                      {role.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  If not selected, we'll detect the role from the job description
                </p>
              </div>

              {/* Job Description */}
              <div>
                <label className="label">Job Description *</label>
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
                  className="input min-h-[200px] font-mono text-sm"
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

              {matchJD.isError && (
                <div className="p-3 bg-danger-50 text-danger-700 rounded-lg text-sm">
                  Failed to analyze match. Please try again.
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!matchResult && (
          <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
            <button onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button
              onClick={handleAnalyze}
              disabled={jobDescription.length < 50 || matchJD.isPending}
              className="btn-primary gap-2"
            >
              {matchJD.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analyze Match
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
