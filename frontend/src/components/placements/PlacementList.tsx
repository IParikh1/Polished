import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { DollarSign, CheckCircle2, Clock, AlertTriangle, Building, User } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

interface Placement {
  placement_id: string
  batch_id: string
  resume_id: string
  company_name: string
  position: string
  candidate_name?: string
  placement_date: string
  reported_at: string
  verification_status: 'pending' | 'verified' | 'disputed'
  fee_amount: number
  fee_paid: boolean
}

interface PlacementListProps {
  batchId?: string
}

export default function PlacementList({ batchId }: PlacementListProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['placements', batchId],
    queryFn: async () => {
      const params = batchId ? { batch_id: batchId } : {}
      const response = await axios.get('/api/v1/placements', { params })
      return response.data
    },
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
        return <CheckCircle2 className="w-4 h-4 text-success-500" />
      case 'disputed':
        return <AlertTriangle className="w-4 h-4 text-danger-500" />
      default:
        return <Clock className="w-4 h-4 text-warning-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    const classes = {
      pending: 'badge-warning',
      verified: 'badge-success',
      disputed: 'badge-danger',
    }
    return (
      <span className={clsx('badge', classes[status as keyof typeof classes] || 'badge-gray')}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  const placements: Placement[] = data?.placements || []

  if (placements.length === 0) {
    return (
      <div className="text-center py-12">
        <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No placements yet</h3>
        <p className="text-gray-500">Report a placement to start earning $250 per verified hire</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Stats Summary */}
      {data?.stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{data.stats.total_placements}</div>
            <div className="text-sm text-gray-500">Total Placements</div>
          </div>
          <div className="p-4 bg-success-50 rounded-lg">
            <div className="text-2xl font-bold text-success-600">{data.stats.verified}</div>
            <div className="text-sm text-success-600">Verified</div>
          </div>
          <div className="p-4 bg-warning-50 rounded-lg">
            <div className="text-2xl font-bold text-warning-600">{data.stats.pending}</div>
            <div className="text-sm text-warning-600">Pending</div>
          </div>
          <div className="p-4 bg-primary-50 rounded-lg">
            <div className="text-2xl font-bold text-primary-600">
              ${data.stats.total_revenue?.toLocaleString() || 0}
            </div>
            <div className="text-sm text-primary-600">Total Revenue</div>
          </div>
        </div>
      )}

      {/* Placement List */}
      <div className="divide-y divide-gray-200">
        {placements.map((placement) => (
          <div key={placement.placement_id} className="py-4 flex items-start gap-4">
            <div className="p-2 bg-gray-100 rounded-lg">
              {getStatusIcon(placement.verification_status)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <Building className="w-4 h-4 text-gray-400" />
                <span className="font-medium text-gray-900">{placement.company_name}</span>
                {getStatusBadge(placement.verification_status)}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <User className="w-3 h-3" />
                <span>{placement.candidate_name || 'Unknown'}</span>
                <span className="text-gray-300">|</span>
                <span>{placement.position}</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Reported {formatDistanceToNow(new Date(placement.reported_at), { addSuffix: true })}
              </div>
            </div>
            <div className="text-right">
              <div
                className={clsx(
                  'text-lg font-bold',
                  placement.fee_paid ? 'text-success-600' : 'text-gray-900'
                )}
              >
                ${placement.fee_amount}
              </div>
              <div className="text-xs text-gray-500">
                {placement.fee_paid ? 'Paid' : placement.verification_status === 'verified' ? 'Pending Payment' : 'Awaiting Verification'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
