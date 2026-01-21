import { useState } from 'react'
import { Target, Sparkles, Loader2 } from 'lucide-react'
import { useUpdateBatch } from '../../hooks/useBatches'

interface JDInputProps {
  batchId: string
}

export default function JDInput({ batchId }: JDInputProps) {
  const [jobDescription, setJobDescription] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)

  const updateBatch = useUpdateBatch()

  const handleSave = async () => {
    if (!jobDescription.trim()) return

    try {
      await updateBatch.mutateAsync({
        batchId,
        data: {
          job_description: jobDescription,
          premium_features: ['jd_matching'],
        },
      })
      setIsExpanded(false)
    } catch (error) {
      console.error('Failed to update batch:', error)
    }
  }

  if (!isExpanded) {
    return (
      <div className="card p-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-primary-50 rounded-lg">
            <Target className="w-6 h-6 text-primary-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900">Enable JD Matching</h3>
            <p className="text-sm text-gray-600">
              Add a job description to match and rank resumes against specific requirements
            </p>
          </div>
          <button onClick={() => setIsExpanded(true)} className="btn-primary gap-2">
            <Sparkles className="w-4 h-4" />
            Add JD
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-4">
        <Target className="w-5 h-5 text-primary-600" />
        <h3 className="font-semibold text-gray-900">Job Description Matching</h3>
        <span className="badge-primary">Premium</span>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Paste the job description below. Our AI will analyze and match each resume against the
        requirements, highlighting skill gaps and providing match scores.
      </p>

      <textarea
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        placeholder="Paste the full job description here...

Example:
We are looking for a Senior Software Engineer with 5+ years of experience in Python, AWS, and distributed systems. The ideal candidate should have experience with:
- Building scalable APIs
- Working with cloud infrastructure
- Leading small teams
..."
        className="input min-h-[200px] mb-4"
      />

      <div className="flex justify-end gap-3">
        <button onClick={() => setIsExpanded(false)} className="btn-secondary">
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={!jobDescription.trim() || updateBatch.isPending}
          className="btn-primary gap-2"
        >
          {updateBatch.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <Target className="w-4 h-4" />
              Enable Matching
            </>
          )}
        </button>
      </div>
    </div>
  )
}
