import { CheckCircle2, XCircle, Tag, Lightbulb, TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import type { JDMatchResult } from './JDMatcher'

interface MatchResultsProps {
  result: JDMatchResult
  compact?: boolean
}

export default function MatchResults({ result, compact = false }: MatchResultsProps) {
  const {
    match_score,
    matching_requirements,
    gaps,
    keywords_to_add,
    keywords_present,
    tailored_suggestions,
    experience_match,
  } = result

  // Determine score color and label
  const getScoreInfo = (score: number) => {
    if (score >= 80) return { color: 'text-success-600', bg: 'bg-success-500', label: 'Strong Match' }
    if (score >= 60) return { color: 'text-primary-600', bg: 'bg-primary-500', label: 'Good Match' }
    if (score >= 40) return { color: 'text-amber-600', bg: 'bg-amber-500', label: 'Moderate Match' }
    return { color: 'text-danger-600', bg: 'bg-danger-500', label: 'Weak Match' }
  }

  const scoreInfo = getScoreInfo(match_score)

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div
            className={clsx(
              'w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold',
              scoreInfo.bg
            )}
          >
            {match_score}
          </div>
          <span className={clsx('text-sm font-medium', scoreInfo.color)}>
            {scoreInfo.label}
          </span>
        </div>
        {gaps.length > 0 && (
          <span className="text-xs text-gray-500">
            {gaps.length} gap{gaps.length !== 1 ? 's' : ''} to address
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Score Header */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-4">
          <div
            className={clsx(
              'w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold shadow-lg',
              scoreInfo.bg
            )}
          >
            {match_score}
          </div>
          <div>
            <p className={clsx('text-lg font-semibold', scoreInfo.color)}>
              {scoreInfo.label}
            </p>
            <p className="text-sm text-gray-500">
              {experience_match ? (
                <span className="text-success-600">Experience level matches</span>
              ) : (
                <span className="text-amber-600">Experience gap detected</span>
              )}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Match Score</p>
          <p className="text-3xl font-bold text-gray-900">{match_score}/100</p>
        </div>
      </div>

      {/* Two-column layout for matching and gaps */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Matching Requirements */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-success-600">
            <CheckCircle2 className="w-4 h-4" />
            <h5 className="font-medium text-sm">Matching Requirements</h5>
          </div>
          {matching_requirements.length > 0 ? (
            <ul className="space-y-1">
              {matching_requirements.slice(0, 6).map((req, idx) => (
                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-success-500 mt-0.5">•</span>
                  <span>{req}</span>
                </li>
              ))}
              {matching_requirements.length > 6 && (
                <li className="text-xs text-gray-500">
                  +{matching_requirements.length - 6} more
                </li>
              )}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 italic">No clear matches found</p>
          )}
        </div>

        {/* Gaps */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-danger-600">
            <XCircle className="w-4 h-4" />
            <h5 className="font-medium text-sm">Gaps to Address</h5>
          </div>
          {gaps.length > 0 ? (
            <ul className="space-y-1">
              {gaps.slice(0, 6).map((gap, idx) => (
                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-danger-500 mt-0.5">•</span>
                  <span>{gap}</span>
                </li>
              ))}
              {gaps.length > 6 && (
                <li className="text-xs text-gray-500">
                  +{gaps.length - 6} more
                </li>
              )}
            </ul>
          ) : (
            <p className="text-sm text-success-600">No significant gaps!</p>
          )}
        </div>
      </div>

      {/* Keywords Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-gray-700">
          <Tag className="w-4 h-4" />
          <h5 className="font-medium text-sm">Keywords</h5>
        </div>

        <div className="space-y-2">
          {/* Keywords to Add */}
          {keywords_to_add.length > 0 && (
            <div>
              <p className="text-xs text-amber-600 mb-1">Add these keywords:</p>
              <div className="flex flex-wrap gap-1">
                {keywords_to_add.slice(0, 10).map((kw, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 rounded-full"
                  >
                    {kw}
                  </span>
                ))}
                {keywords_to_add.length > 10 && (
                  <span className="px-2 py-0.5 text-xs text-gray-500">
                    +{keywords_to_add.length - 10} more
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Keywords Present */}
          {keywords_present.length > 0 && (
            <div>
              <p className="text-xs text-success-600 mb-1">Keywords found:</p>
              <div className="flex flex-wrap gap-1">
                {keywords_present.slice(0, 8).map((kw, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs bg-success-100 text-success-800 rounded-full"
                  >
                    {kw}
                  </span>
                ))}
                {keywords_present.length > 8 && (
                  <span className="px-2 py-0.5 text-xs text-gray-500">
                    +{keywords_present.length - 8} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Suggestions Section */}
      {tailored_suggestions.length > 0 && (
        <div className="p-4 bg-primary-50 rounded-lg space-y-2">
          <div className="flex items-center gap-2 text-primary-700">
            <Lightbulb className="w-4 h-4" />
            <h5 className="font-medium text-sm">Recommendations</h5>
          </div>
          <ul className="space-y-1">
            {tailored_suggestions.map((suggestion, idx) => (
              <li key={idx} className="text-sm text-primary-800 flex items-start gap-2">
                <TrendingUp className="w-3 h-3 mt-1 flex-shrink-0" />
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
