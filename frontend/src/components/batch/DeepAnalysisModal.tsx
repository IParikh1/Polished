import { X, Sparkles, CheckCircle2, AlertTriangle, Lightbulb, MessageSquare, AlertCircle } from 'lucide-react'
import type { Resume } from '../../api/batchClient'

interface DeepAnalysisModalProps {
  resume: Resume
  onClose: () => void
}

export default function DeepAnalysisModal({ resume, onClose }: DeepAnalysisModalProps) {
  const analysis = resume.deep_analysis

  if (!analysis) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-xl shadow-xl">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Sparkles className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">Deep Analysis</h2>
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
          {/* Overall Assessment */}
          {analysis.overall_assessment && (
            <div className="p-4 bg-primary-50 rounded-lg">
              <h3 className="font-medium text-primary-900 mb-2">Overall Assessment</h3>
              <p className="text-primary-800">{analysis.overall_assessment}</p>
            </div>
          )}

          {/* Strengths */}
          {analysis.strengths && analysis.strengths.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 font-medium text-gray-900 mb-3">
                <CheckCircle2 className="w-5 h-5 text-success-500" />
                Strengths
              </h3>
              <ul className="space-y-2">
                {analysis.strengths.map((strength, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-700">
                    <span className="text-success-500 font-bold">+</span>
                    {strength}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Weaknesses */}
          {analysis.weaknesses && analysis.weaknesses.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 font-medium text-gray-900 mb-3">
                <AlertTriangle className="w-5 h-5 text-warning-500" />
                Areas for Improvement
              </h3>
              <ul className="space-y-2">
                {analysis.weaknesses.map((weakness, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-700">
                    <span className="text-warning-500 font-bold">!</span>
                    {weakness}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 font-medium text-gray-900 mb-3">
                <Lightbulb className="w-5 h-5 text-primary-500" />
                Recommendations
              </h3>
              <ol className="space-y-2 list-decimal list-inside">
                {analysis.recommendations.map((rec, i) => (
                  <li key={i} className="text-gray-700">{rec}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Red Flags */}
          {analysis.red_flags && analysis.red_flags.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 font-medium text-gray-900 mb-3">
                <AlertCircle className="w-5 h-5 text-danger-500" />
                Red Flags
              </h3>
              <ul className="space-y-2">
                {analysis.red_flags.map((flag, i) => (
                  <li key={i} className="flex items-start gap-2 text-danger-700">
                    <span className="font-bold">X</span>
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Interview Questions */}
          {analysis.interview_questions && analysis.interview_questions.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 font-medium text-gray-900 mb-3">
                <MessageSquare className="w-5 h-5 text-primary-500" />
                Suggested Interview Questions
              </h3>
              <ol className="space-y-2 list-decimal list-inside">
                {analysis.interview_questions.map((question, i) => (
                  <li key={i} className="text-gray-700">{question}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Growth Potential */}
          {analysis.growth_potential && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-2">Growth Potential</h3>
              <p className="text-gray-700">{analysis.growth_potential}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
