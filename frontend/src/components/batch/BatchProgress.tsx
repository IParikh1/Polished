import { useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { useProcessingStatus } from '../../hooks/useBatches'

interface BatchProgressProps {
  batchId: string
}

export default function BatchProgress({ batchId }: BatchProgressProps) {
  const { data: status, refetch } = useProcessingStatus(batchId, true)

  // Refetch periodically while processing
  useEffect(() => {
    if (status?.status === 'processing') {
      const interval = setInterval(() => {
        refetch()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [status?.status, refetch])

  if (!status) return null

  const progressPercent = status.total_resumes > 0
    ? Math.round((status.processed_resumes / status.total_resumes) * 100)
    : 0

  return (
    <div className="mt-4 p-4 bg-primary-50 rounded-lg">
      <div className="flex items-center gap-3 mb-2">
        <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
        <div className="flex-1">
          <div className="flex justify-between text-sm">
            <span className="font-medium text-primary-700">Processing resumes...</span>
            <span className="text-primary-600">
              {status.processed_resumes} / {status.total_resumes} ({progressPercent}%)
            </span>
          </div>
        </div>
      </div>
      <div className="h-2 bg-primary-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary-500 transition-all duration-500 ease-out progress-bar"
          style={{ width: `${progressPercent}%` }}
        />
      </div>
      <p className="text-xs text-primary-600 mt-2">
        Parsing, scoring, and ranking resumes. This may take a few minutes.
      </p>
    </div>
  )
}
