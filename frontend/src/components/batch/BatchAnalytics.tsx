import { useMemo } from 'react'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Star,
  AlertTriangle,
  FileText,
  Sparkles,
  Award,
} from 'lucide-react'
import type { Resume } from '../../api/batchClient'
import clsx from 'clsx'

interface BatchAnalyticsProps {
  resumes: Resume[]
}

interface ScoreCategory {
  key: string
  label: string
  type: 'substance' | 'presentation'
  description: string
}

const SCORE_CATEGORIES: ScoreCategory[] = [
  { key: 'experience', label: 'Experience', type: 'substance', description: 'Years & relevance' },
  { key: 'skills', label: 'Skills', type: 'substance', description: 'Tools & methods' },
  { key: 'achievements', label: 'Achievements', type: 'substance', description: 'Quota & metrics' },
  { key: 'career_progression', label: 'Career Growth', type: 'substance', description: 'Title advancement' },
  { key: 'certifications', label: 'Certifications', type: 'substance', description: 'Professional certs' },
  { key: 'formatting', label: 'Formatting', type: 'presentation', description: 'Structure & layout' },
  { key: 'keywords', label: 'Keywords', type: 'presentation', description: 'Industry terms' },
  { key: 'education', label: 'Education', type: 'presentation', description: 'Degrees' },
  { key: 'contact_info', label: 'Contact Info', type: 'presentation', description: 'Email & phone' },
]

export default function BatchAnalytics({ resumes }: BatchAnalyticsProps) {
  const analytics = useMemo(() => {
    if (resumes.length === 0) {
      return null
    }

    // Get resumes with scores
    const scoredResumes = resumes.filter(r => r.scores?.overall !== undefined)
    if (scoredResumes.length === 0) {
      return null
    }

    // Score distribution
    const distribution = {
      excellent: scoredResumes.filter(r => (r.scores?.overall || 0) >= 80).length,
      good: scoredResumes.filter(r => (r.scores?.overall || 0) >= 60 && (r.scores?.overall || 0) < 80).length,
      fair: scoredResumes.filter(r => (r.scores?.overall || 0) >= 40 && (r.scores?.overall || 0) < 60).length,
      poor: scoredResumes.filter(r => (r.scores?.overall || 0) < 40).length,
    }

    // Average overall score
    const avgScore = scoredResumes.reduce((sum, r) => sum + (r.scores?.overall || 0), 0) / scoredResumes.length

    // Category averages
    const categoryAverages: Record<string, { avg: number; count: number }> = {}
    for (const cat of SCORE_CATEGORIES) {
      const values = scoredResumes
        .map(r => (r.scores as Record<string, number>)?.[cat.key])
        .filter((v): v is number => v !== undefined && v !== null)

      if (values.length > 0) {
        categoryAverages[cat.key] = {
          avg: values.reduce((a, b) => a + b, 0) / values.length,
          count: values.length,
        }
      }
    }

    // Identify weak areas (categories significantly below average)
    const substanceCategories = SCORE_CATEGORIES.filter(c => c.type === 'substance')
    const presentationCategories = SCORE_CATEGORIES.filter(c => c.type === 'presentation')

    const substanceAvg = substanceCategories
      .filter(c => categoryAverages[c.key])
      .reduce((sum, c) => sum + (categoryAverages[c.key]?.avg || 0), 0) /
      substanceCategories.filter(c => categoryAverages[c.key]).length || 0

    const presentationAvg = presentationCategories
      .filter(c => categoryAverages[c.key])
      .reduce((sum, c) => sum + (categoryAverages[c.key]?.avg || 0), 0) /
      presentationCategories.filter(c => categoryAverages[c.key]).length || 0

    // Top candidates
    const topCandidates = [...scoredResumes]
      .sort((a, b) => (b.scores?.overall || 0) - (a.scores?.overall || 0))
      .slice(0, 5)

    // Identify low scorers and why
    const lowScorers = scoredResumes.filter(r => (r.scores?.overall || 0) < 60)
    let lowScoreInsight = ''

    if (lowScorers.length > 0) {
      // Check if low scores are due to presentation or substance
      const lowScorerSubstanceAvg = lowScorers.reduce((sum, r) => {
        const scores = r.scores as Record<string, number>
        let total = 0, count = 0
        for (const cat of substanceCategories) {
          if (scores?.[cat.key] !== undefined) {
            total += scores[cat.key]
            count++
          }
        }
        return sum + (count > 0 ? total / count : 0)
      }, 0) / lowScorers.length

      const lowScorerPresentationAvg = lowScorers.reduce((sum, r) => {
        const scores = r.scores as Record<string, number>
        let total = 0, count = 0
        for (const cat of presentationCategories) {
          if (scores?.[cat.key] !== undefined) {
            total += scores[cat.key]
            count++
          }
        }
        return sum + (count > 0 ? total / count : 0)
      }, 0) / lowScorers.length

      if (lowScorerPresentationAvg < lowScorerSubstanceAvg - 10) {
        lowScoreInsight = 'presentation'
      } else if (lowScorerSubstanceAvg < lowScorerPresentationAvg - 10) {
        lowScoreInsight = 'substance'
      } else {
        lowScoreInsight = 'both'
      }
    }

    return {
      total: scoredResumes.length,
      distribution,
      avgScore,
      categoryAverages,
      substanceAvg,
      presentationAvg,
      topCandidates,
      lowScorers: lowScorers.length,
      lowScoreInsight,
    }
  }, [resumes])

  if (!analytics) {
    return (
      <div className="card p-8 text-center">
        <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Analytics Available</h3>
        <p className="text-gray-600">Process the batch to see analytics and insights.</p>
      </div>
    )
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-success-600'
    if (score >= 60) return 'text-primary-600'
    if (score >= 40) return 'text-warning-600'
    return 'text-danger-600'
  }

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-success-100'
    if (score >= 60) return 'bg-primary-100'
    if (score >= 40) return 'bg-warning-100'
    return 'bg-danger-100'
  }

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <Users className="w-6 h-6 text-primary-600 mx-auto mb-2" />
          <p className="text-2xl font-bold text-gray-900">{analytics.total}</p>
          <p className="text-sm text-gray-600">Resumes Scored</p>
        </div>
        <div className="card p-4 text-center">
          <Star className="w-6 h-6 text-warning-600 mx-auto mb-2" />
          <p className={clsx('text-2xl font-bold', getScoreColor(analytics.avgScore))}>
            {analytics.avgScore.toFixed(1)}
          </p>
          <p className="text-sm text-gray-600">Average Score</p>
        </div>
        <div className="card p-4 text-center">
          <Award className="w-6 h-6 text-success-600 mx-auto mb-2" />
          <p className="text-2xl font-bold text-success-600">{analytics.distribution.excellent}</p>
          <p className="text-sm text-gray-600">Strong (80+)</p>
        </div>
        <div className="card p-4 text-center">
          <AlertTriangle className="w-6 h-6 text-danger-600 mx-auto mb-2" />
          <p className="text-2xl font-bold text-danger-600">{analytics.lowScorers}</p>
          <p className="text-sm text-gray-600">Need Review (&lt;60)</p>
        </div>
      </div>

      {/* Score Distribution */}
      <div className="card p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary-600" />
          Score Distribution
        </h3>
        <div className="space-y-3">
          <div className="flex items-center gap-4">
            <span className="w-24 text-sm font-medium text-success-700">80-100</span>
            <div className="flex-1 h-8 bg-gray-100 rounded-lg overflow-hidden">
              <div
                className="h-full bg-success-500 flex items-center justify-end pr-2"
                style={{ width: `${(analytics.distribution.excellent / analytics.total) * 100}%` }}
              >
                {analytics.distribution.excellent > 0 && (
                  <span className="text-xs font-medium text-white">{analytics.distribution.excellent}</span>
                )}
              </div>
            </div>
            <span className="w-16 text-sm text-gray-500 text-right">
              {((analytics.distribution.excellent / analytics.total) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="w-24 text-sm font-medium text-primary-700">60-79</span>
            <div className="flex-1 h-8 bg-gray-100 rounded-lg overflow-hidden">
              <div
                className="h-full bg-primary-500 flex items-center justify-end pr-2"
                style={{ width: `${(analytics.distribution.good / analytics.total) * 100}%` }}
              >
                {analytics.distribution.good > 0 && (
                  <span className="text-xs font-medium text-white">{analytics.distribution.good}</span>
                )}
              </div>
            </div>
            <span className="w-16 text-sm text-gray-500 text-right">
              {((analytics.distribution.good / analytics.total) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="w-24 text-sm font-medium text-warning-700">40-59</span>
            <div className="flex-1 h-8 bg-gray-100 rounded-lg overflow-hidden">
              <div
                className="h-full bg-warning-500 flex items-center justify-end pr-2"
                style={{ width: `${(analytics.distribution.fair / analytics.total) * 100}%` }}
              >
                {analytics.distribution.fair > 0 && (
                  <span className="text-xs font-medium text-white">{analytics.distribution.fair}</span>
                )}
              </div>
            </div>
            <span className="w-16 text-sm text-gray-500 text-right">
              {((analytics.distribution.fair / analytics.total) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="w-24 text-sm font-medium text-danger-700">0-39</span>
            <div className="flex-1 h-8 bg-gray-100 rounded-lg overflow-hidden">
              <div
                className="h-full bg-danger-500 flex items-center justify-end pr-2"
                style={{ width: `${(analytics.distribution.poor / analytics.total) * 100}%` }}
              >
                {analytics.distribution.poor > 0 && (
                  <span className="text-xs font-medium text-white">{analytics.distribution.poor}</span>
                )}
              </div>
            </div>
            <span className="w-16 text-sm text-gray-500 text-right">
              {((analytics.distribution.poor / analytics.total) * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-600" />
            Why Scores Are Low
          </h3>

          {/* Insight Banner */}
          {analytics.lowScorers > 0 && (
            <div className={clsx(
              'p-4 rounded-lg mb-4',
              analytics.lowScoreInsight === 'presentation' ? 'bg-warning-50 border border-warning-200' :
              analytics.lowScoreInsight === 'substance' ? 'bg-danger-50 border border-danger-200' :
              'bg-gray-50 border border-gray-200'
            )}>
              {analytics.lowScoreInsight === 'presentation' && (
                <>
                  <p className="font-medium text-warning-800 flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Writing & Formatting Issues
                  </p>
                  <p className="text-sm text-warning-700 mt-1">
                    Low scorers have good experience but poor resume presentation.
                    These candidates may be worth interviewing.
                  </p>
                </>
              )}
              {analytics.lowScoreInsight === 'substance' && (
                <>
                  <p className="font-medium text-danger-800 flex items-center gap-2">
                    <TrendingDown className="w-4 h-4" />
                    Skill & Experience Gaps
                  </p>
                  <p className="text-sm text-danger-700 mt-1">
                    Low scorers lack relevant skills or experience.
                    These may not be good fits for the role.
                  </p>
                </>
              )}
              {analytics.lowScoreInsight === 'both' && (
                <>
                  <p className="font-medium text-gray-800 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Mixed Issues
                  </p>
                  <p className="text-sm text-gray-700 mt-1">
                    Low scorers have both skill gaps and presentation issues.
                    Review individually to assess potential.
                  </p>
                </>
              )}
            </div>
          )}

          {/* Substance vs Presentation */}
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Substance (Skills & Experience)</span>
                <span className={clsx('text-sm font-bold', getScoreColor(analytics.substanceAvg))}>
                  {analytics.substanceAvg.toFixed(0)}
                </span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={clsx('h-full rounded-full', getScoreBg(analytics.substanceAvg).replace('100', '500'))}
                  style={{ width: `${analytics.substanceAvg}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Presentation (Writing & Format)</span>
                <span className={clsx('text-sm font-bold', getScoreColor(analytics.presentationAvg))}>
                  {analytics.presentationAvg.toFixed(0)}
                </span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={clsx('h-full rounded-full', getScoreBg(analytics.presentationAvg).replace('100', '500'))}
                  style={{ width: `${analytics.presentationAvg}%` }}
                />
              </div>
            </div>
          </div>

          {/* Category Details */}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-3">Category Breakdown</p>
            <div className="grid grid-cols-2 gap-2">
              {SCORE_CATEGORIES.filter(cat => analytics.categoryAverages[cat.key]).map(cat => (
                <div key={cat.key} className="flex items-center justify-between py-1">
                  <span className="text-xs text-gray-600">{cat.label}</span>
                  <span className={clsx(
                    'text-xs font-medium px-2 py-0.5 rounded',
                    getScoreBg(analytics.categoryAverages[cat.key]?.avg || 0),
                    getScoreColor(analytics.categoryAverages[cat.key]?.avg || 0)
                  )}>
                    {(analytics.categoryAverages[cat.key]?.avg || 0).toFixed(0)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Candidates */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-success-600" />
            Top Candidates
          </h3>
          <div className="space-y-3">
            {analytics.topCandidates.map((resume, idx) => (
              <div
                key={resume.resume_id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
              >
                <div className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
                  idx === 0 ? 'bg-yellow-100 text-yellow-700' :
                  idx === 1 ? 'bg-gray-200 text-gray-600' :
                  idx === 2 ? 'bg-orange-100 text-orange-700' :
                  'bg-gray-100 text-gray-500'
                )}>
                  {idx + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {resume.extracted_data?.name || 'Unknown'}
                  </p>
                  <p className="text-xs text-gray-500 truncate">{resume.filename}</p>
                </div>
                <div className={clsx(
                  'px-3 py-1 rounded-full text-sm font-bold',
                  getScoreBg(resume.scores?.overall || 0),
                  getScoreColor(resume.scores?.overall || 0)
                )}>
                  {(resume.scores?.overall || 0).toFixed(1)}
                </div>
              </div>
            ))}
          </div>

          {analytics.distribution.excellent > 5 && (
            <p className="text-xs text-gray-500 mt-4 text-center">
              +{analytics.distribution.excellent - 5} more candidates scoring 80+
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
