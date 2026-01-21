import { Copy, Check, ArrowRight } from 'lucide-react'
import { useState } from 'react'
import type { RewriteResponse } from '../../api/consultClient'

interface RewritePreviewProps {
  data: RewriteResponse
}

export default function RewritePreview({ data }: RewritePreviewProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(data.rewritten_text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-success-600 bg-success-50'
    if (score >= 50) return 'text-primary-600 bg-primary-50'
    return 'text-warning-600 bg-warning-50'
  }

  return (
    <div className="space-y-6">
      {/* Improvement Score */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div>
          <h4 className="font-medium text-gray-900">Improvement Score</h4>
          <p className="text-sm text-gray-500">How much this rewrite improves the section</p>
        </div>
        <div
          className={`px-4 py-2 rounded-lg font-bold text-2xl ${getScoreColor(
            data.improvement_score
          )}`}
        >
          +{data.improvement_score.toFixed(0)}%
        </div>
      </div>

      {/* Before/After Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Original */}
        <div>
          <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">
            Original
          </h4>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-gray-700 whitespace-pre-wrap">{data.original_text}</p>
          </div>
        </div>

        {/* Rewritten */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-success-600 uppercase tracking-wider">
              Improved
            </h4>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-success-500" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy
                </>
              )}
            </button>
          </div>
          <div className="p-4 bg-success-50 rounded-lg border border-success-200">
            <p className="text-gray-900 whitespace-pre-wrap">{data.rewritten_text}</p>
          </div>
        </div>
      </div>

      {/* Changes Made */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Changes Made</h4>
        <div className="space-y-2">
          {data.changes_made.map((change, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-gray-700">
              <ArrowRight className="w-4 h-4 text-primary-500 flex-shrink-0" />
              {change}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
