import { useState } from 'react'
import { ChevronDown, ChevronUp, Download, Star, Target, Sparkles } from 'lucide-react'
import type { Resume } from '../../api/batchClient'
import ScoreBreakdown from './ScoreBreakdown'
import DeepAnalysisModal from './DeepAnalysisModal'
import JDMatcherModal from './JDMatcherModal'
import clsx from 'clsx'

interface RankingTableProps {
  resumes: Resume[]
  batchId: string
  hasJdMatching?: boolean
}

export default function RankingTable({ resumes, batchId, hasJdMatching }: RankingTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null)
  const [jdMatchResume, setJdMatchResume] = useState<Resume | null>(null)

  const getScoreColor = (score: number | undefined) => {
    if (!score) return 'text-gray-400'
    if (score >= 80) return 'text-success-600'
    if (score >= 60) return 'text-primary-600'
    if (score >= 40) return 'text-warning-600'
    return 'text-danger-600'
  }

  const getScoreBg = (score: number | undefined) => {
    if (!score) return 'bg-gray-100'
    if (score >= 80) return 'bg-success-50'
    if (score >= 60) return 'bg-primary-50'
    if (score >= 40) return 'bg-warning-50'
    return 'bg-danger-50'
  }

  const getRankBadge = (rank: number | undefined) => {
    if (!rank) return null
    if (rank === 1) return <span className="text-xl">1st</span>
    if (rank === 2) return <span className="text-lg">2nd</span>
    if (rank === 3) return <span className="text-lg">3rd</span>
    return <span>#{rank}</span>
  }

  if (resumes.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No resumes found matching your criteria
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Rank</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Candidate</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Score</th>
              {hasJdMatching && (
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">JD Match</th>
              )}
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Skills</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            {resumes.map((resume) => (
              <>
                <tr
                  key={resume.resume_id}
                  className={clsx(
                    'border-b border-gray-100 hover:bg-gray-50 transition-colors',
                    expandedId === resume.resume_id && 'bg-gray-50'
                  )}
                >
                  <td className="py-3 px-4">
                    <div
                      className={clsx(
                        'w-10 h-10 rounded-full flex items-center justify-center font-bold',
                        resume.rank && resume.rank <= 3
                          ? 'bg-primary-100 text-primary-700'
                          : 'bg-gray-100 text-gray-600'
                      )}
                    >
                      {getRankBadge(resume.rank)}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div>
                      <div className="font-medium text-gray-900">
                        {resume.extracted_data?.name || 'Unknown'}
                      </div>
                      <div className="text-sm text-gray-500">{resume.filename}</div>
                      {resume.extracted_data?.email && (
                        <div className="text-xs text-gray-400">{resume.extracted_data.email}</div>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div
                      className={clsx(
                        'inline-flex items-center gap-1 px-3 py-1 rounded-full font-semibold',
                        getScoreBg(resume.scores?.overall),
                        getScoreColor(resume.scores?.overall)
                      )}
                    >
                      <Star className="w-4 h-4" />
                      {resume.scores?.overall?.toFixed(1) || '-'}
                    </div>
                  </td>
                  {hasJdMatching && (
                    <td className="py-3 px-4">
                      {resume.jd_match?.match_score !== undefined ? (
                        <div
                          className={clsx(
                            'inline-flex items-center gap-1 px-3 py-1 rounded-full font-medium text-sm',
                            getScoreBg(resume.jd_match.match_score),
                            getScoreColor(resume.jd_match.match_score)
                          )}
                        >
                          <Target className="w-3 h-3" />
                          {resume.jd_match.match_score.toFixed(0)}%
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  )}
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1">
                      {(resume.extracted_data?.skills || []).slice(0, 3).map((skill, i) => (
                        <span key={i} className="badge-gray text-xs">
                          {skill}
                        </span>
                      ))}
                      {(resume.extracted_data?.skills?.length || 0) > 3 && (
                        <span className="badge-gray text-xs">
                          +{(resume.extracted_data?.skills?.length || 0) - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setJdMatchResume(resume)}
                        className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                        title="Match Against Job Description"
                      >
                        <Target className="w-4 h-4" />
                      </button>
                      {resume.deep_analysis && (
                        <button
                          onClick={() => setSelectedResume(resume)}
                          className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                          title="View Deep Analysis"
                        >
                          <Sparkles className="w-4 h-4" />
                        </button>
                      )}
                      {resume.download_url && (
                        <a
                          href={resume.download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                          title="Download Resume"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      )}
                      <button
                        onClick={() =>
                          setExpandedId(expandedId === resume.resume_id ? null : resume.resume_id)
                        }
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        title="View Details"
                      >
                        {expandedId === resume.resume_id ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
                {expandedId === resume.resume_id && (
                  <tr>
                    <td colSpan={hasJdMatching ? 6 : 5} className="px-4 py-4 bg-gray-50">
                      <ScoreBreakdown resume={resume} hasJdMatching={hasJdMatching} />
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {/* Deep Analysis Modal */}
      {selectedResume && (
        <DeepAnalysisModal
          resume={selectedResume}
          onClose={() => setSelectedResume(null)}
        />
      )}

      {/* JD Matcher Modal */}
      {jdMatchResume && (
        <JDMatcherModal
          batchId={batchId}
          resume={jdMatchResume}
          onClose={() => setJdMatchResume(null)}
        />
      )}
    </>
  )
}
