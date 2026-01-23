import { Briefcase, GraduationCap, Wrench, FileText, Target, CheckCircle2, XCircle } from 'lucide-react'
import type { Resume } from '../../api/batchClient'
import clsx from 'clsx'

interface ScoreBreakdownProps {
  resume: Resume
  hasJdMatching?: boolean
}

export default function ScoreBreakdown({ resume, hasJdMatching }: ScoreBreakdownProps) {
  const scores = resume.scores || { overall: 0 }
  const extracted = resume.extracted_data || {}
  const jdMatch = resume.jd_match

  const scoreCategories = [
    { key: 'experience', label: 'Experience', icon: Briefcase, score: scores.experience },
    { key: 'skills', label: 'Skills', icon: Wrench, score: scores.skills },
    { key: 'education', label: 'Education', icon: GraduationCap, score: scores.education },
    { key: 'formatting', label: 'Formatting', icon: FileText, score: scores.formatting },
    { key: 'keywords', label: 'Keywords', icon: Target, score: scores.keywords },
  ]

  const getScoreColor = (score: number | undefined) => {
    if (!score) return 'bg-gray-200'
    if (score >= 80) return 'bg-success-500'
    if (score >= 60) return 'bg-primary-500'
    if (score >= 40) return 'bg-warning-500'
    return 'bg-danger-500'
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Score Breakdown */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Score Breakdown</h4>
        <div className="space-y-3">
          {scoreCategories.map((category) => (
            <div key={category.key}>
              <div className="flex items-center justify-between text-sm mb-1">
                <div className="flex items-center gap-2 text-gray-600">
                  <category.icon className="w-4 h-4" />
                  {category.label}
                </div>
                <span className="font-medium text-gray-900">
                  {category.score?.toFixed(0) || '-'}
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={clsx('h-full transition-all', getScoreColor(category.score))}
                  style={{ width: `${category.score || 0}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Candidate Info */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Candidate Information</h4>
        <dl className="space-y-2 text-sm">
          {extracted.name && (
            <div className="flex">
              <dt className="w-24 text-gray-500">Name:</dt>
              <dd className="text-gray-900">{extracted.name}</dd>
            </div>
          )}
          {extracted.email && (
            <div className="flex">
              <dt className="w-24 text-gray-500">Email:</dt>
              <dd className="text-gray-900">{extracted.email}</dd>
            </div>
          )}
          {extracted.phone && (
            <div className="flex">
              <dt className="w-24 text-gray-500">Phone:</dt>
              <dd className="text-gray-900">{extracted.phone}</dd>
            </div>
          )}
          {extracted.years_of_experience && (
            <div className="flex">
              <dt className="w-24 text-gray-500">Experience:</dt>
              <dd className="text-gray-900">{extracted.years_of_experience} years</dd>
            </div>
          )}
        </dl>

        {extracted.skills && extracted.skills.length > 0 && (
          <div className="mt-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Skills</h5>
            <div className="flex flex-wrap gap-1">
              {extracted.skills.map((skill, i) => (
                <span key={i} className="badge-gray text-xs">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* JD Match (if available) */}
      {hasJdMatching && jdMatch && (
        <div>
          <h4 className="font-medium text-gray-900 mb-3">JD Match Analysis</h4>

          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">Match Score</span>
              <span className="font-bold text-primary-600">
                {jdMatch.match_score.toFixed(0)}%
              </span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={clsx('h-full', getScoreColor(jdMatch.match_score))}
                style={{ width: `${jdMatch.match_score}%` }}
              />
            </div>
          </div>

          {jdMatch.matched_skills && jdMatch.matched_skills.length > 0 && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-success-700 mb-1 flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" />
                Matched Skills
              </h5>
              <div className="flex flex-wrap gap-1">
                {jdMatch.matched_skills.map((skill, i) => (
                  <span key={i} className="badge-success text-xs">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {jdMatch.missing_skills && jdMatch.missing_skills.length > 0 && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-danger-700 mb-1 flex items-center gap-1">
                <XCircle className="w-4 h-4" />
                Missing Skills
              </h5>
              <div className="flex flex-wrap gap-1">
                {jdMatch.missing_skills.map((skill, i) => (
                  <span key={i} className="badge-danger text-xs">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {jdMatch.recommendation && (
            <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
              {jdMatch.recommendation}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
