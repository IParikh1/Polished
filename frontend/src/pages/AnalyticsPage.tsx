import { useMemo } from 'react'
import {
  BarChart3,
  TrendingUp,
  Users,
  FileText,
  Target,
  Clock,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Loader2,
} from 'lucide-react'
import { useBatches } from '../hooks/useBatches'
import { useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import clsx from 'clsx'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  color: 'primary' | 'success' | 'warning' | 'danger'
}

function StatCard({ title, value, subtitle, icon: Icon, color }: StatCardProps) {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    warning: 'bg-warning-50 text-warning-600',
    danger: 'bg-danger-50 text-danger-600',
  }

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={clsx('p-3 rounded-lg', colorClasses[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  )
}

interface BatchActivityItem {
  id: string
  name: string
  date: string
  resumes: number
  processed: number
  status: 'completed' | 'processing' | 'pending' | 'failed'
}

function RecentActivity({ batches }: { batches: BatchActivityItem[] }) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-success-500" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-danger-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string) => {
    const classes = {
      completed: 'bg-success-100 text-success-700',
      processing: 'bg-primary-100 text-primary-700',
      pending: 'bg-gray-100 text-gray-700',
      failed: 'bg-danger-100 text-danger-700',
    }
    return (
      <span className={clsx('text-xs px-2 py-0.5 rounded-full', classes[status as keyof typeof classes] || classes.pending)}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  return (
    <div className="card p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Recent Batch Activity</h3>
      <div className="space-y-4">
        {batches.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">No batches yet. Create your first batch to get started.</p>
        ) : (
          batches.map((batch) => (
            <div key={batch.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
              <div className="flex items-center gap-3">
                {getStatusIcon(batch.status)}
                <div>
                  <p className="text-sm font-medium text-gray-900">{batch.name}</p>
                  <p className="text-xs text-gray-500">
                    {batch.processed}/{batch.resumes} resumes processed
                  </p>
                </div>
              </div>
              <div className="text-right flex items-center gap-3">
                {getStatusBadge(batch.status)}
                <p className="text-xs text-gray-500 w-20">{batch.date}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function BatchStatusBreakdown({ batches }: { batches: { status: string; count: number }[] }) {
  const total = batches.reduce((sum, b) => sum + b.count, 0)

  const statusColors = {
    completed: 'bg-success-500',
    processing: 'bg-primary-500',
    pending: 'bg-gray-400',
    failed: 'bg-danger-500',
  }

  const statusLabels = {
    completed: 'Completed',
    processing: 'Processing',
    pending: 'Pending',
    failed: 'Failed',
  }

  return (
    <div className="card p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Batch Status Breakdown</h3>
      {total === 0 ? (
        <p className="text-sm text-gray-500 text-center py-8">No batches yet</p>
      ) : (
        <>
          <div className="h-4 bg-gray-100 rounded-full overflow-hidden flex mb-4">
            {batches.map((item) => (
              item.count > 0 && (
                <div
                  key={item.status}
                  className={clsx('h-full', statusColors[item.status as keyof typeof statusColors] || 'bg-gray-400')}
                  style={{ width: `${(item.count / total) * 100}%` }}
                  title={`${statusLabels[item.status as keyof typeof statusLabels] || item.status}: ${item.count}`}
                />
              )
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {batches.map((item) => (
              <div key={item.status} className="flex items-center gap-2">
                <div className={clsx('w-3 h-3 rounded-full', statusColors[item.status as keyof typeof statusColors] || 'bg-gray-400')} />
                <span className="text-sm text-gray-600">
                  {statusLabels[item.status as keyof typeof statusLabels] || item.status}
                </span>
                <span className="text-sm font-medium text-gray-900 ml-auto">{item.count}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function AnalyticsPage() {
  const queryClient = useQueryClient()

  // Fetch batches with auto-refresh every 30 seconds
  const { data: batchesData, isLoading, isFetching } = useBatches(100, 0)

  // Manual refresh handler
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['batches'] })
  }

  // Compute analytics from batch data
  const analytics = useMemo(() => {
    if (!batchesData?.batches) {
      return {
        totalBatches: 0,
        totalResumes: 0,
        processedResumes: 0,
        completedBatches: 0,
        processingBatches: 0,
        pendingBatches: 0,
        failedBatches: 0,
        completionRate: 0,
        recentBatches: [],
        statusBreakdown: [],
      }
    }

    const batches = batchesData.batches
    const totalBatches = batches.length
    const totalResumes = batches.reduce((sum, b) => sum + b.total_resumes, 0)
    const processedResumes = batches.reduce((sum, b) => sum + b.processed_resumes, 0)

    const completedBatches = batches.filter(b => b.status === 'completed').length
    const processingBatches = batches.filter(b => b.status === 'processing').length
    const pendingBatches = batches.filter(b => b.status === 'pending').length
    const failedBatches = batches.filter(b => b.status === 'failed').length

    const completionRate = totalBatches > 0 ? Math.round((completedBatches / totalBatches) * 100) : 0

    // Recent batches for activity feed
    const recentBatches: BatchActivityItem[] = batches.slice(0, 10).map(b => ({
      id: b.batch_id,
      name: b.name,
      date: format(parseISO(b.created_at), 'MMM d, yyyy'),
      resumes: b.total_resumes,
      processed: b.processed_resumes,
      status: b.status as 'completed' | 'processing' | 'pending' | 'failed',
    }))

    // Status breakdown for chart
    const statusBreakdown = [
      { status: 'completed', count: completedBatches },
      { status: 'processing', count: processingBatches },
      { status: 'pending', count: pendingBatches },
      { status: 'failed', count: failedBatches },
    ].filter(s => s.count > 0)

    return {
      totalBatches,
      totalResumes,
      processedResumes,
      completedBatches,
      processingBatches,
      pendingBatches,
      failedBatches,
      completionRate,
      recentBatches,
      statusBreakdown,
    }
  }, [batchesData])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Track your resume processing metrics</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isFetching}
          className="btn-secondary gap-2"
        >
          <RefreshCw className={clsx('w-4 h-4', isFetching && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Batches"
          value={analytics.totalBatches}
          subtitle={`${analytics.completedBatches} completed`}
          icon={FileText}
          color="primary"
        />
        <StatCard
          title="Total Resumes"
          value={analytics.totalResumes}
          subtitle={`${analytics.processedResumes} processed`}
          icon={Users}
          color="success"
        />
        <StatCard
          title="Completion Rate"
          value={`${analytics.completionRate}%`}
          subtitle={`${analytics.completedBatches} of ${analytics.totalBatches} batches`}
          icon={Target}
          color="warning"
        />
        <StatCard
          title="In Progress"
          value={analytics.processingBatches + analytics.pendingBatches}
          subtitle={`${analytics.processingBatches} processing, ${analytics.pendingBatches} pending`}
          icon={TrendingUp}
          color="primary"
        />
      </div>

      {/* Activity and Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentActivity batches={analytics.recentBatches} />
        <BatchStatusBreakdown batches={analytics.statusBreakdown} />
      </div>

      {/* Quick Stats */}
      <div className="card p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-success-50 rounded-lg text-center">
            <CheckCircle2 className="w-6 h-6 text-success-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-success-700">{analytics.completedBatches}</p>
            <p className="text-sm text-success-600">Completed</p>
          </div>
          <div className="p-4 bg-primary-50 rounded-lg text-center">
            <Loader2 className="w-6 h-6 text-primary-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-primary-700">{analytics.processingBatches}</p>
            <p className="text-sm text-primary-600">Processing</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg text-center">
            <Clock className="w-6 h-6 text-gray-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-700">{analytics.pendingBatches}</p>
            <p className="text-sm text-gray-600">Pending</p>
          </div>
          <div className="p-4 bg-danger-50 rounded-lg text-center">
            <AlertCircle className="w-6 h-6 text-danger-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-danger-700">{analytics.failedBatches}</p>
            <p className="text-sm text-danger-600">Failed</p>
          </div>
        </div>
      </div>

      {/* Empty state message */}
      {analytics.totalBatches === 0 && (
        <div className="card p-12 text-center">
          <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No analytics data yet</h3>
          <p className="text-gray-600">
            Create and process your first batch to see analytics here.
          </p>
        </div>
      )}
    </div>
  )
}
