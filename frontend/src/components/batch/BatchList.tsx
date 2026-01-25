import { FileText, Clock, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import type { Batch } from '../../api/batchClient'
import clsx from 'clsx'
import { format, parseISO } from 'date-fns'

interface BatchListProps {
  batches: Batch[]
  selectedId?: string
  onSelect: (batchId: string) => void
}

export default function BatchList({ batches, selectedId, onSelect }: BatchListProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-400" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-success-500" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-danger-500" />
      default:
        return <FileText className="w-4 h-4 text-gray-400" />
    }
  }

  if (batches.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
        <p className="text-sm">No batches yet</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {batches.map((batch) => (
        <button
          key={batch.batch_id}
          onClick={() => onSelect(batch.batch_id)}
          className={clsx(
            'w-full text-left p-3 rounded-lg transition-colors',
            selectedId === batch.batch_id
              ? 'bg-primary-50 border border-primary-200'
              : 'hover:bg-gray-50 border border-transparent'
          )}
        >
          <div className="flex items-start gap-3">
            {getStatusIcon(batch.status)}
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900 truncate">{batch.name}</div>
              <div className="text-sm text-gray-500">
                {batch.total_resumes} resumes
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {format(parseISO(batch.created_at), 'MMM d, yyyy')}
              </div>
            </div>
            {batch.status === 'completed' && (
              <div className="text-xs font-medium text-success-600">
                {batch.processed_resumes}/{batch.total_resumes}
              </div>
            )}
          </div>
        </button>
      ))}
    </div>
  )
}
