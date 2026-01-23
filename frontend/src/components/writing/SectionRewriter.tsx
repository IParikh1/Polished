import { useState } from 'react'
import {
  PenLine,
  RefreshCw,
  Copy,
  Check,
  AlertCircle,
  ArrowRight,
  Loader2,
} from 'lucide-react'
import clsx from 'clsx'
import { useRewriteSection } from '../../hooks/useResumeWriting'
import type { SalesRole } from '../../api/batchClient'

interface SectionRewriterProps {
  batchId?: string
  resumeId?: string
  targetRole: SalesRole
  jobDescription?: string
  className?: string
}

const sections = [
  { id: 'summary', label: 'Professional Summary' },
  { id: 'experience', label: 'Experience' },
  { id: 'skills', label: 'Skills' },
  { id: 'education', label: 'Education' },
]

export default function SectionRewriter({
  batchId,
  resumeId,
  targetRole,
  jobDescription,
  className,
}: SectionRewriterProps) {
  const [selectedSection, setSelectedSection] = useState('summary')
  const [sectionContent, setSectionContent] = useState('')
  const [context, setContext] = useState('')
  const [copied, setCopied] = useState(false)

  const rewriteMutation = useRewriteSection()

  const handleRewrite = async () => {
    if (!sectionContent.trim()) return

    try {
      await rewriteMutation.mutateAsync({
        batch_id: batchId,
        resume_id: resumeId,
        section_name: selectedSection,
        section_content: sectionContent,
        target_role: targetRole,
        context: context || undefined,
        job_description: jobDescription,
      })
    } catch {
      // Error handled by mutation
    }
  }

  const handleCopy = async () => {
    if (rewriteMutation.data?.rewritten) {
      await navigator.clipboard.writeText(rewriteMutation.data.rewritten)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleUseRewritten = () => {
    if (rewriteMutation.data?.rewritten) {
      setSectionContent(rewriteMutation.data.rewritten)
      rewriteMutation.reset()
    }
  }

  return (
    <div className={clsx('card', className)}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <PenLine className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Section Rewriter</h3>
            <p className="text-sm text-gray-500">
              Improve specific sections of your resume
            </p>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Section selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Section
          </label>
          <div className="flex flex-wrap gap-2">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setSelectedSection(section.id)}
                disabled={rewriteMutation.isPending}
                className={clsx(
                  'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                  selectedSection === section.id
                    ? 'bg-purple-100 text-purple-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                {section.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Current Content
          </label>
          <textarea
            value={sectionContent}
            onChange={(e) => setSectionContent(e.target.value)}
            placeholder={`Paste your current ${sections.find(s => s.id === selectedSection)?.label.toLowerCase()} here...`}
            className="input min-h-[120px] resize-y"
            disabled={rewriteMutation.isPending}
          />
        </div>

        {/* Additional context */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Additional Context (Optional)
          </label>
          <input
            type="text"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="e.g., Focus on leadership, emphasize SaaS experience"
            className="input"
            disabled={rewriteMutation.isPending}
          />
        </div>

        {/* Rewrite button */}
        <button
          onClick={handleRewrite}
          disabled={!sectionContent.trim() || rewriteMutation.isPending}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {rewriteMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Rewriting...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4" />
              Rewrite Section
            </>
          )}
        </button>

        {rewriteMutation.isError && (
          <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>
              {rewriteMutation.error?.message || 'Failed to rewrite section'}
            </span>
          </div>
        )}

        {/* Result */}
        {rewriteMutation.data && (
          <div className="border-t border-gray-200 pt-4 mt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-900">Rewritten Version</h4>
              <div className="flex items-center gap-2">
                {rewriteMutation.data.improvement_score > 0 && (
                  <span className="text-xs px-2 py-1 bg-green-50 text-green-700 rounded-full">
                    +{rewriteMutation.data.improvement_score}% improvement
                  </span>
                )}
                <button
                  onClick={handleCopy}
                  className="text-gray-500 hover:text-gray-700 p-1"
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-3 text-sm text-gray-800 whitespace-pre-wrap mb-3">
              {rewriteMutation.data.rewritten}
            </div>

            {rewriteMutation.data.changes && rewriteMutation.data.changes.length > 0 && (
              <div className="mb-3">
                <h5 className="text-sm font-medium text-gray-700 mb-2">
                  Changes Made
                </h5>
                <ul className="text-sm text-gray-600 space-y-1">
                  {rewriteMutation.data.changes.map((change, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <ArrowRight className="w-3 h-3 text-purple-500 mt-1 flex-shrink-0" />
                      {change}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <button
              onClick={handleUseRewritten}
              className="btn-secondary w-full"
            >
              Use This Version
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
