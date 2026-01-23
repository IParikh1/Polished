import { useState } from 'react'
import {
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Sparkles,
  AlertCircle,
} from 'lucide-react'
import clsx from 'clsx'

interface ResumePreviewProps {
  resumeText: string
  sections?: Record<string, string>
  changesMode?: string[]
  keywordsAdded?: string[]
  suggestions?: string[]
  matchImprovement?: number
  isLoading?: boolean
}

export default function ResumePreview({
  resumeText,
  sections,
  changesMode,
  keywordsAdded,
  suggestions,
  matchImprovement,
  isLoading,
}: ResumePreviewProps) {
  const [copied, setCopied] = useState(false)
  const [showSections, setShowSections] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(true)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(resumeText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-600">Generating optimized resume...</p>
            <p className="text-sm text-gray-500 mt-1">This may take a moment</p>
          </div>
        </div>
      </div>
    )
  }

  if (!resumeText) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center h-64 text-center">
          <div>
            <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">
              Select options and generate to see your optimized resume
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      {/* Header with stats */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Generated Resume</h3>
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-500" />
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

        {/* Stats row */}
        <div className="flex flex-wrap gap-3">
          {matchImprovement !== undefined && matchImprovement > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-sm">
              <Sparkles className="w-3.5 h-3.5" />
              +{matchImprovement}% match improvement
            </div>
          )}
          {keywordsAdded && keywordsAdded.length > 0 && (
            <div className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
              {keywordsAdded.length} keywords added
            </div>
          )}
          {changesMode && changesMode.length > 0 && (
            <div className="px-2.5 py-1 bg-purple-50 text-purple-700 rounded-full text-sm">
              {changesMode.length} changes made
            </div>
          )}
        </div>
      </div>

      {/* Suggestions panel */}
      {suggestions && suggestions.length > 0 && (
        <div className="border-b border-gray-200">
          <button
            onClick={() => setShowSuggestions(!showSuggestions)}
            className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50"
          >
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-medium text-gray-900">
                {suggestions.length} Suggestions for Further Improvement
              </span>
            </div>
            {showSuggestions ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>
          {showSuggestions && (
            <div className="px-4 pb-4">
              <ul className="space-y-2">
                {suggestions.map((suggestion, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-gray-600"
                  >
                    <span className="text-amber-500 mt-0.5">-</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Sections toggle */}
      {sections && Object.keys(sections).length > 0 && (
        <div className="border-b border-gray-200">
          <button
            onClick={() => setShowSections(!showSections)}
            className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50"
          >
            <span className="text-sm font-medium text-gray-900">
              View by Section
            </span>
            {showSections ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>
          {showSections && (
            <div className="px-4 pb-4 space-y-4">
              {Object.entries(sections).map(([name, content]) => (
                <div key={name}>
                  <h4 className="text-sm font-medium text-gray-700 capitalize mb-2">
                    {name.replace(/_/g, ' ')}
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600 whitespace-pre-wrap">
                    {content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Full resume text */}
      <div className="p-4">
        <div
          className={clsx(
            'bg-gray-50 rounded-lg p-4 text-sm text-gray-800 whitespace-pre-wrap font-mono',
            'max-h-[500px] overflow-y-auto'
          )}
        >
          {resumeText}
        </div>
      </div>

      {/* Keywords added */}
      {keywordsAdded && keywordsAdded.length > 0 && (
        <div className="px-4 pb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Keywords Added
          </h4>
          <div className="flex flex-wrap gap-2">
            {keywordsAdded.map((keyword, i) => (
              <span
                key={i}
                className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
