import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Plus, FileText, Clock, CheckCircle2, AlertCircle, Loader2, RotateCcw, ListOrdered } from 'lucide-react'
import { useBatches, useBatch, useCreateBatch, useProcessBatch, useReopenBatch, useCloseBatch } from '../hooks/useBatches'
import { useRankings } from '../hooks/useRankings'
import BatchList from '../components/batch/BatchList'
import BatchUpload from '../components/batch/BatchUpload'
import BatchProgress from '../components/batch/BatchProgress'
import RankingTable from '../components/batch/RankingTable'
import ExportButton from '../components/batch/ExportButton'
import JDInput from '../components/batch/JDInput'
import BatchFilters from '../components/batch/BatchFilters'
import BatchAnalytics from '../components/batch/BatchAnalytics'
import clsx from 'clsx'

export default function BatchDashboard() {
  const { batchId } = useParams()
  const navigate = useNavigate()
  const [isCreating, setIsCreating] = useState(false)
  const [newBatchName, setNewBatchName] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [filters, setFilters] = useState({ minScore: 0, maxScore: 100 })

  const { data: batchesData, isLoading: loadingBatches } = useBatches()
  const { data: selectedBatch, isLoading: loadingBatch } = useBatch(batchId)
  const { data: rankingsData, isLoading: loadingRankings } = useRankings(batchId, {
    min_score: filters.minScore,
    max_score: filters.maxScore,
    limit: 100,
  })

  const createBatch = useCreateBatch()
  const processBatch = useProcessBatch()
  const reopenBatch = useReopenBatch()
  const closeBatch = useCloseBatch()

  const handleCreateBatch = async () => {
    if (!newBatchName.trim()) return

    try {
      const batch = await createBatch.mutateAsync({
        name: newBatchName,
        job_description: jobDescription || undefined,
        premium_features: jobDescription ? ['jd_matching'] : [],
      })
      setIsCreating(false)
      setNewBatchName('')
      setJobDescription('')
      navigate(`/batches/${batch.batch_id}`)
    } catch (error) {
      console.error('Failed to create batch:', error)
    }
  }

  const handleProcessBatch = async () => {
    if (!batchId) return
    try {
      await processBatch.mutateAsync(batchId)
    } catch (error) {
      console.error('Failed to start processing:', error)
    }
  }

  const handleReopenBatch = async () => {
    if (!batchId) return
    try {
      await reopenBatch.mutateAsync(batchId)
    } catch (error) {
      console.error('Failed to reopen batch:', error)
    }
  }

  const handleCloseBatch = async () => {
    if (!batchId) return
    try {
      await closeBatch.mutateAsync(batchId)
    } catch (error) {
      console.error('Failed to close batch:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-500" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-success-500" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-danger-500" />
      default:
        return <FileText className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    const classes = {
      pending: 'badge-gray',
      processing: 'badge-primary',
      completed: 'badge-success',
      failed: 'badge-danger',
    }
    return (
      <span className={clsx('badge', classes[status as keyof typeof classes] || 'badge-gray')}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Resume Batches</h1>
          <p className="text-gray-600">Upload, score, and rank resumes at scale</p>
        </div>
        <button onClick={() => setIsCreating(true)} className="btn-primary gap-2">
          <Plus className="w-4 h-4" />
          New Batch
        </button>
      </div>

      {/* Create Batch Modal */}
      {isCreating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-lg p-6 bg-white rounded-xl shadow-xl">
            <h2 className="text-lg font-semibold mb-4">Create New Batch</h2>
            <div className="space-y-4">
              <div>
                <label className="label">Batch Name</label>
                <input
                  type="text"
                  value={newBatchName}
                  onChange={(e) => setNewBatchName(e.target.value)}
                  placeholder="e.g., Software Engineers Q1 2026"
                  className="input"
                />
              </div>
              <div>
                <label className="label">Job Description (optional - enables JD matching)</label>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description here to enable smart matching..."
                  className="input min-h-[120px]"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={() => setIsCreating(false)} className="btn-secondary">
                  Cancel
                </button>
                <button
                  onClick={handleCreateBatch}
                  disabled={!newBatchName.trim() || createBatch.isPending}
                  className="btn-primary"
                >
                  {createBatch.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Create Batch'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Batch List Sidebar */}
        <div className="lg:col-span-1">
          <div className="card p-4">
            <h3 className="font-semibold text-gray-900 mb-4">Your Batches</h3>
            {loadingBatches ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <BatchList
                batches={batchesData?.batches || []}
                selectedId={batchId}
                onSelect={(id) => navigate(`/batches/${id}`)}
              />
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {batchId && selectedBatch ? (
            <>
              {/* Batch Header */}
              <div className="card p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      {getStatusIcon(selectedBatch.status)}
                      <h2 className="text-xl font-semibold text-gray-900">{selectedBatch.name}</h2>
                      {getStatusBadge(selectedBatch.status)}
                    </div>
                    <p className="text-gray-600">
                      {rankingsData?.total || selectedBatch.total_resumes} resumes | {selectedBatch.processed_resumes} processed
                    </p>
                    {selectedBatch.job_description && (
                      <p className="text-sm text-primary-600 mt-1">JD Matching enabled</p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {selectedBatch.status === 'pending' && (rankingsData?.total || selectedBatch.total_resumes) > 0 && (
                      <>
                        <button
                          onClick={handleCloseBatch}
                          disabled={closeBatch.isPending}
                          className="btn-secondary gap-2"
                          title="Close batch to view rankings without processing"
                        >
                          {closeBatch.isPending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <>
                              <ListOrdered className="w-4 h-4" />
                              View Rankings
                            </>
                          )}
                        </button>
                        <button
                          onClick={handleProcessBatch}
                          disabled={processBatch.isPending}
                          className="btn-primary gap-2"
                        >
                          {processBatch.isPending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            'Start Processing'
                          )}
                        </button>
                      </>
                    )}
                    {(selectedBatch.status === 'completed' || selectedBatch.status === 'failed') && (
                      <>
                        <button
                          onClick={handleReopenBatch}
                          disabled={reopenBatch.isPending}
                          className="btn-secondary gap-2"
                          title="Reopen batch to add more resumes"
                        >
                          {reopenBatch.isPending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <>
                              <RotateCcw className="w-4 h-4" />
                              Reopen
                            </>
                          )}
                        </button>
                        {selectedBatch.status === 'completed' && (
                          <ExportButton
                            batchId={batchId}
                            hasJobDescription={!!selectedBatch.job_description}
                          />
                        )}
                      </>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                {selectedBatch.status === 'processing' && (
                  <BatchProgress batchId={batchId} />
                )}
              </div>

              {/* Upload Section */}
              {selectedBatch.status === 'pending' && (
                <div className="card p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Upload Resumes</h3>
                  <BatchUpload batchId={batchId} />
                </div>
              )}

              {/* JD Input for JD Matching */}
              {selectedBatch.status === 'pending' && !selectedBatch.job_description && (
                <JDInput batchId={batchId} />
              )}

              {/* Rankings */}
              {selectedBatch.status === 'completed' && (
                <>
                  {/* Batch Analytics */}
                  {!loadingRankings && rankingsData?.resumes && rankingsData.resumes.length > 0 && (
                    <BatchAnalytics resumes={rankingsData.resumes} />
                  )}

                  <div className="card p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-gray-900">Ranked Resumes</h3>
                      <BatchFilters filters={filters} onChange={setFilters} />
                    </div>
                    {loadingRankings ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                      </div>
                    ) : (
                      <RankingTable
                        resumes={rankingsData?.resumes || []}
                        batchId={batchId}
                        hasJdMatching={!!selectedBatch.job_description}
                      />
                    )}
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="card p-12 text-center">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {loadingBatch ? 'Loading...' : 'Select a batch to get started'}
              </h3>
              <p className="text-gray-600 mb-4">
                Choose a batch from the sidebar or create a new one
              </p>
              <button onClick={() => setIsCreating(true)} className="btn-primary gap-2">
                <Plus className="w-4 h-4" />
                Create New Batch
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
