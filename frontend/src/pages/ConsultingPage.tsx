import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MessageSquare, Sparkles, RefreshCw, Send, Loader2, ArrowLeft } from 'lucide-react'
import {
  useConsultingSession,
  useCreateSession,
  useAnalyzeResume,
  useRewriteSection,
  useChatMessage,
  useChatHistory,
} from '../hooks/useConsulting'
import { useBatches } from '../hooks/useBatches'
import { useBatchResumes } from '../hooks/useRankings'
import ConsultingChat from '../components/consulting/ConsultingChat'
import RewritePreview from '../components/consulting/RewritePreview'
import RoleSelector from '../components/consulting/RoleSelector'
import clsx from 'clsx'

export default function ConsultingPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [selectedBatchId, setSelectedBatchId] = useState<string>('')
  const [selectedResumeId, setSelectedResumeId] = useState<string>('')
  const [targetRole, setTargetRole] = useState('')
  const [activeTab, setActiveTab] = useState<'analysis' | 'rewrite' | 'chat'>('analysis')
  const [selectedSection, setSelectedSection] = useState<'summary' | 'experience' | 'skills'>('summary')

  const { data: batchesData } = useBatches()
  const { data: resumesData } = useBatchResumes(selectedBatchId || undefined)
  const { data: session } = useConsultingSession(sessionId)
  const { data: chatHistory } = useChatHistory(sessionId)

  const createSession = useCreateSession()
  const analyzeResume = useAnalyzeResume()
  const rewriteSection = useRewriteSection()
  const sendMessage = useChatMessage()

  const handleStartSession = async () => {
    if (!selectedBatchId || !selectedResumeId) return

    try {
      const newSession = await createSession.mutateAsync({
        batch_id: selectedBatchId,
        resume_id: selectedResumeId,
        target_role: targetRole || undefined,
      })
      navigate(`/consulting/${newSession.session_id}`)
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const handleAnalyze = async () => {
    if (!sessionId) return
    try {
      await analyzeResume.mutateAsync({ sessionId })
    } catch (error) {
      console.error('Failed to analyze:', error)
    }
  }

  const handleRewrite = async () => {
    if (!sessionId) return
    try {
      await rewriteSection.mutateAsync({
        sessionId,
        section: selectedSection,
      })
    } catch (error) {
      console.error('Failed to rewrite:', error)
    }
  }

  // Session selection view
  if (!sessionId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Resume Consulting</h1>
          <p className="text-gray-600">Get AI-powered suggestions to improve your resumes</p>
        </div>

        <div className="max-w-2xl">
          <div className="card p-6 space-y-6">
            <div className="flex items-center gap-3 text-primary-600">
              <Sparkles className="w-6 h-6" />
              <h2 className="text-lg font-semibold">Start a Consulting Session</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Select Batch</label>
                <select
                  value={selectedBatchId}
                  onChange={(e) => {
                    setSelectedBatchId(e.target.value)
                    setSelectedResumeId('')
                  }}
                  className="input"
                >
                  <option value="">Choose a batch...</option>
                  {batchesData?.batches.map((batch) => (
                    <option key={batch.batch_id} value={batch.batch_id}>
                      {batch.name} ({batch.total_resumes} resumes)
                    </option>
                  ))}
                </select>
              </div>

              {selectedBatchId && (
                <div>
                  <label className="label">Select Resume</label>
                  <select
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    className="input"
                  >
                    <option value="">Choose a resume...</option>
                    {resumesData?.resumes.map((resume) => (
                      <option key={resume.resume_id} value={resume.resume_id}>
                        {resume.filename}
                        {resume.extracted_data?.name && ` - ${resume.extracted_data.name}`}
                        {resume.scores?.overall && ` (Score: ${resume.scores.overall})`}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <RoleSelector value={targetRole} onChange={setTargetRole} />

              <button
                onClick={handleStartSession}
                disabled={!selectedBatchId || !selectedResumeId || createSession.isPending}
                className="w-full btn-primary gap-2"
              >
                {createSession.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <MessageSquare className="w-4 h-4" />
                    Start Session
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Active session view
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/consulting')} className="btn-secondary p-2">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Resume Consulting</h1>
          <p className="text-gray-600">
            Session for {session?.target_role || 'General'} role
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-8">
          {[
            { id: 'analysis', label: 'Analysis', icon: Sparkles },
            { id: 'rewrite', label: 'Rewrite', icon: RefreshCw },
            { id: 'chat', label: 'Chat', icon: MessageSquare },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={clsx(
                'flex items-center gap-2 pb-4 text-sm font-medium border-b-2 transition-colors',
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {activeTab === 'analysis' && (
          <>
            <div className="lg:col-span-2 card p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Resume Analysis</h2>
                <button
                  onClick={handleAnalyze}
                  disabled={analyzeResume.isPending}
                  className="btn-primary gap-2"
                >
                  {analyzeResume.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Analyze
                    </>
                  )}
                </button>
              </div>

              {analyzeResume.data ? (
                <div className="space-y-6">
                  {/* Overall Assessment */}
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-medium text-gray-900 mb-2">Overall Assessment</h3>
                    <p className="text-gray-700">{analyzeResume.data.overall_assessment}</p>
                  </div>

                  {/* Strengths */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Strengths</h3>
                    <ul className="space-y-2">
                      {analyzeResume.data.strengths.map((strength, i) => (
                        <li key={i} className="flex items-start gap-2 text-gray-700">
                          <span className="text-success-500">+</span>
                          {strength}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Weaknesses */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Areas for Improvement</h3>
                    <ul className="space-y-2">
                      {analyzeResume.data.weaknesses.map((weakness, i) => (
                        <li key={i} className="flex items-start gap-2 text-gray-700">
                          <span className="text-warning-500">!</span>
                          {weakness}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Recommendations */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Recommendations</h3>
                    <ol className="space-y-2 list-decimal list-inside">
                      {analyzeResume.data.recommendations.map((rec, i) => (
                        <li key={i} className="text-gray-700">{rec}</li>
                      ))}
                    </ol>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  Click "Analyze" to get detailed feedback on this resume
                </div>
              )}
            </div>

            {/* Section Feedback Sidebar */}
            <div className="card p-6">
              <h3 className="font-medium text-gray-900 mb-4">Section Feedback</h3>
              {analyzeResume.data?.section_feedback ? (
                <div className="space-y-4">
                  {Object.entries(analyzeResume.data.section_feedback).map(([section, feedback]) => (
                    <div key={section} className="p-3 bg-gray-50 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-900 capitalize mb-1">{section}</h4>
                      <p className="text-sm text-gray-600">{feedback}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  Section-by-section feedback will appear after analysis
                </p>
              )}
            </div>
          </>
        )}

        {activeTab === 'rewrite' && (
          <>
            <div className="lg:col-span-2 card p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Section Rewriter</h2>
              </div>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="label">Select Section to Rewrite</label>
                  <select
                    value={selectedSection}
                    onChange={(e) => setSelectedSection(e.target.value as typeof selectedSection)}
                    className="input"
                  >
                    <option value="summary">Professional Summary</option>
                    <option value="experience">Experience</option>
                    <option value="skills">Skills</option>
                  </select>
                </div>

                <button
                  onClick={handleRewrite}
                  disabled={rewriteSection.isPending}
                  className="btn-primary gap-2"
                >
                  {rewriteSection.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      Rewrite Section
                    </>
                  )}
                </button>
              </div>

              {rewriteSection.data && (
                <RewritePreview data={rewriteSection.data} />
              )}
            </div>

            <div className="card p-6">
              <h3 className="font-medium text-gray-900 mb-4">Rewrite Tips</h3>
              <ul className="space-y-3 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-primary-500">1.</span>
                  Start with your most impactful achievements
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-500">2.</span>
                  Use action verbs and quantify results
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-500">3.</span>
                  Tailor content to your target role
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary-500">4.</span>
                  Keep it concise and scannable
                </li>
              </ul>
            </div>
          </>
        )}

        {activeTab === 'chat' && (
          <div className="lg:col-span-3">
            <ConsultingChat
              sessionId={sessionId}
              messages={chatHistory?.messages || []}
              onSend={(message) => sendMessage.mutate({ sessionId, message })}
              isLoading={sendMessage.isPending}
            />
          </div>
        )}
      </div>
    </div>
  )
}
