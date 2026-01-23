import { useState, useEffect } from 'react'
import {
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ChevronRight,
  Loader2,
  Sparkles,
  X,
} from 'lucide-react'
import clsx from 'clsx'
import { useExtractMetrics, useFormatMetrics } from '../../hooks/useMetricsExtraction'
import type { SalesRole, MissingMetric } from '../../api/batchClient'

interface MetricsExtractorProps {
  batchId: string
  resumeId: string
  targetRole: SalesRole
  onMetricsCollected?: (metrics: Record<string, Record<string, string>>) => void
  className?: string
}

interface CollectedMetrics {
  [company: string]: {
    [metricType: string]: string
  }
}

export default function MetricsExtractor({
  batchId,
  resumeId,
  targetRole,
  onMetricsCollected,
  className,
}: MetricsExtractorProps) {
  const [collectedMetrics, setCollectedMetrics] = useState<CollectedMetrics>({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [inputValue, setInputValue] = useState('')
  const [showResults, setShowResults] = useState(false)

  const extractMutation = useExtractMetrics()
  const formatMutation = useFormatMetrics()

  // Auto-extract on mount
  useEffect(() => {
    if (batchId && resumeId && targetRole) {
      extractMutation.mutate({
        batch_id: batchId,
        resume_id: resumeId,
        target_role: targetRole,
      })
    }
  }, [batchId, resumeId, targetRole])

  const missingMetrics = extractMutation.data?.metrics_missing || []
  const foundMetrics = extractMutation.data?.metrics_found || []
  const overallScore = extractMutation.data?.overall_score || 0
  const recommendations = extractMutation.data?.recommendations || []

  const currentQuestion = missingMetrics[currentQuestionIndex]
  const totalQuestions = missingMetrics.length
  const answeredCount = Object.values(collectedMetrics).reduce(
    (acc, company) => acc + Object.keys(company).length,
    0
  )

  const handleAnswer = () => {
    if (!inputValue.trim() || !currentQuestion) return

    setCollectedMetrics((prev) => ({
      ...prev,
      [currentQuestion.company]: {
        ...prev[currentQuestion.company],
        [currentQuestion.metric_type]: inputValue.trim(),
      },
    }))

    setInputValue('')

    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex((prev) => prev + 1)
    } else {
      setShowResults(true)
    }
  }

  const handleSkip = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex((prev) => prev + 1)
    } else {
      setShowResults(true)
    }
  }

  const handleFinish = () => {
    if (Object.keys(collectedMetrics).length > 0) {
      formatMutation.mutate(
        {
          metrics: collectedMetrics,
          target_role: targetRole,
        },
        {
          onSuccess: () => {
            onMetricsCollected?.(collectedMetrics)
          },
        }
      )
    }
    setShowResults(true)
  }

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600 bg-green-100'
    if (score >= 40) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 70) return 'Strong'
    if (score >= 40) return 'Moderate'
    return 'Needs Work'
  }

  if (extractMutation.isPending) {
    return (
      <div className={clsx('card p-6', className)}>
        <div className="flex items-center justify-center h-48">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-3" />
            <p className="text-gray-600">Analyzing your resume metrics...</p>
          </div>
        </div>
      </div>
    )
  }

  if (extractMutation.isError) {
    return (
      <div className={clsx('card p-6', className)}>
        <div className="flex items-center gap-3 text-red-600">
          <AlertTriangle className="w-5 h-5" />
          <span>Failed to extract metrics. Please try again.</span>
        </div>
      </div>
    )
  }

  // Show results view
  if (showResults || totalQuestions === 0) {
    return (
      <div className={clsx('card', className)}>
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <BarChart3 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Metrics Analysis</h3>
                <p className="text-sm text-gray-500">
                  {foundMetrics.length} metrics found in your resume
                </p>
              </div>
            </div>
            <div
              className={clsx(
                'px-3 py-1.5 rounded-full text-sm font-medium',
                getScoreColor(overallScore)
              )}
            >
              {overallScore}% - {getScoreLabel(overallScore)}
            </div>
          </div>
        </div>

        {/* Found Metrics */}
        {foundMetrics.length > 0 && (
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              Metrics Found
            </h4>
            <div className="space-y-2">
              {foundMetrics.map((metric, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-2 bg-green-50 rounded-lg"
                >
                  <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-0.5 rounded">
                    {metric.metric_type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm text-green-800 font-medium">
                    {metric.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Collected Metrics */}
        {Object.keys(collectedMetrics).length > 0 && (
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary-500" />
              Metrics You Provided
            </h4>
            {Object.entries(collectedMetrics).map(([company, metrics]) => (
              <div key={company} className="mb-3">
                <p className="text-sm font-medium text-gray-900 mb-2">{company}</p>
                <div className="space-y-1">
                  {Object.entries(metrics).map(([type, value]) => (
                    <div
                      key={type}
                      className="flex items-center gap-2 text-sm text-gray-600"
                    >
                      <span className="text-gray-400">-</span>
                      <span className="capitalize">{type.replace(/_/g, ' ')}:</span>
                      <span className="font-medium text-gray-900">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Formatted Bullets */}
        {formatMutation.data && (
          <div className="p-4 border-b border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-500" />
              Ready-to-Use Bullet Points
            </h4>
            {Object.entries(formatMutation.data.formatted_metrics).map(
              ([company, bullets]) => (
                <div key={company} className="mb-3">
                  <p className="text-sm font-medium text-gray-900 mb-2">{company}</p>
                  <div className="bg-purple-50 rounded-lg p-3 text-sm text-gray-800 whitespace-pre-wrap">
                    {bullets}
                  </div>
                </div>
              )
            )}
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-amber-500" />
              Recommendations
            </h4>
            <ul className="space-y-2">
              {recommendations.map((rec, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-gray-600"
                >
                  <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )
  }

  // Questions view
  return (
    <div className={clsx('card', className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BarChart3 className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Collect Missing Metrics</h3>
              <p className="text-sm text-gray-500">
                Add metrics to strengthen your resume
              </p>
            </div>
          </div>
          <button
            onClick={handleFinish}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Skip all
          </button>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 transition-all duration-300"
              style={{
                width: `${((currentQuestionIndex + 1) / totalQuestions) * 100}%`,
              }}
            />
          </div>
          <span className="text-sm text-gray-500">
            {currentQuestionIndex + 1} of {totalQuestions}
          </span>
        </div>
      </div>

      {/* Current Question */}
      {currentQuestion && (
        <div className="p-4">
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-primary-600 bg-primary-100 px-2 py-0.5 rounded">
                {currentQuestion.company}
              </span>
              <span className="text-xs text-gray-400">
                Priority {currentQuestion.priority}
              </span>
            </div>
            <p className="text-gray-900 font-medium">{currentQuestion.question}</p>
          </div>

          <div className="space-y-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnswer()}
              placeholder="Enter your answer (e.g., 120%, $2M, 15)"
              className="input w-full"
              autoFocus
            />

            <div className="flex gap-2">
              <button
                onClick={handleAnswer}
                disabled={!inputValue.trim()}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={handleSkip}
                className="btn-secondary px-4"
              >
                Skip
              </button>
            </div>
          </div>

          {/* Hint */}
          <p className="text-xs text-gray-500 mt-3">
            Tip: Include specific numbers. "120% of quota" is better than "exceeded quota"
          </p>
        </div>
      )}

      {/* Already answered count */}
      {answeredCount > 0 && (
        <div className="px-4 pb-4">
          <div className="flex items-center gap-2 text-sm text-green-600">
            <CheckCircle2 className="w-4 h-4" />
            {answeredCount} metrics collected
          </div>
        </div>
      )}
    </div>
  )
}
