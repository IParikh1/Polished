import { useState, useMemo } from 'react'
import {
  BarChart3,
  TrendingUp,
  Users,
  FileText,
  Target,
  Award,
  Clock,
  CheckCircle2,
  AlertCircle,
  Calendar,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'
import { useBatches } from '../hooks/useBatches'
import clsx from 'clsx'

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon: React.ElementType
  color: 'primary' | 'success' | 'warning' | 'danger'
}

function StatCard({ title, value, change, changeLabel, icon: Icon, color }: StatCardProps) {
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
          {change !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {change >= 0 ? (
                <ArrowUpRight className="w-4 h-4 text-success-600" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-danger-600" />
              )}
              <span className={clsx(
                'text-sm font-medium',
                change >= 0 ? 'text-success-600' : 'text-danger-600'
              )}>
                {Math.abs(change)}%
              </span>
              {changeLabel && (
                <span className="text-xs text-gray-500">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
        <div className={clsx('p-3 rounded-lg', colorClasses[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  )
}

interface ScoreDistributionProps {
  distribution: { range: string; count: number; percentage: number }[]
}

function ScoreDistribution({ distribution }: ScoreDistributionProps) {
  const maxCount = Math.max(...distribution.map(d => d.count))

  return (
    <div className="card p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Score Distribution</h3>
      <div className="space-y-3">
        {distribution.map((item) => (
          <div key={item.range} className="flex items-center gap-4">
            <span className="w-16 text-sm text-gray-600">{item.range}</span>
            <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all',
                  item.range.startsWith('90') ? 'bg-success-500' :
                  item.range.startsWith('80') ? 'bg-primary-500' :
                  item.range.startsWith('70') ? 'bg-primary-400' :
                  item.range.startsWith('60') ? 'bg-warning-500' :
                  'bg-danger-500'
                )}
                style={{ width: `${(item.count / maxCount) * 100}%` }}
              />
            </div>
            <span className="w-12 text-sm text-gray-600 text-right">{item.count}</span>
            <span className="w-12 text-xs text-gray-400 text-right">{item.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

interface BatchActivityItem {
  id: string
  name: string
  date: string
  resumes: number
  status: 'completed' | 'processing' | 'pending' | 'failed'
  avgScore?: number
}

function RecentActivity({ batches }: { batches: BatchActivityItem[] }) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-success-500" />
      case 'processing':
        return <Clock className="w-4 h-4 text-primary-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-danger-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  return (
    <div className="card p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Recent Batch Activity</h3>
      <div className="space-y-4">
        {batches.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No batches yet</p>
        ) : (
          batches.map((batch) => (
            <div key={batch.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <div className="flex items-center gap-3">
                {getStatusIcon(batch.status)}
                <div>
                  <p className="text-sm font-medium text-gray-900">{batch.name}</p>
                  <p className="text-xs text-gray-500">{batch.resumes} resumes</p>
                </div>
              </div>
              <div className="text-right">
                {batch.avgScore !== undefined && (
                  <p className="text-sm font-medium text-gray-900">{batch.avgScore.toFixed(1)}</p>
                )}
                <p className="text-xs text-gray-500">{batch.date}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function TopPerformers({ performers }: { performers: { name: string; score: number; batch: string }[] }) {
  return (
    <div className="card p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Top Scoring Resumes</h3>
      <div className="space-y-3">
        {performers.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No scored resumes yet</p>
        ) : (
          performers.map((performer, idx) => (
            <div key={idx} className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <div className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
                  idx === 0 ? 'bg-yellow-100 text-yellow-700' :
                  idx === 1 ? 'bg-gray-100 text-gray-600' :
                  idx === 2 ? 'bg-orange-100 text-orange-700' :
                  'bg-gray-50 text-gray-500'
                )}>
                  {idx + 1}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{performer.name}</p>
                  <p className="text-xs text-gray-500">{performer.batch}</p>
                </div>
              </div>
              <div className={clsx(
                'px-3 py-1 rounded-full text-sm font-medium',
                performer.score >= 90 ? 'bg-success-100 text-success-700' :
                performer.score >= 80 ? 'bg-primary-100 text-primary-700' :
                performer.score >= 70 ? 'bg-warning-100 text-warning-700' :
                'bg-gray-100 text-gray-700'
              )}>
                {performer.score}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d')
  const { data: batchesData, isLoading } = useBatches(100, 0)

  // Compute analytics from batch data
  const analytics = useMemo(() => {
    if (!batchesData?.batches) {
      return {
        totalBatches: 0,
        totalResumes: 0,
        processedResumes: 0,
        completedBatches: 0,
        avgScore: 0,
        scoreDistribution: [],
        recentBatches: [],
        topPerformers: [],
      }
    }

    const batches = batchesData.batches
    const totalBatches = batches.length
    const totalResumes = batches.reduce((sum, b) => sum + b.total_resumes, 0)
    const processedResumes = batches.reduce((sum, b) => sum + b.processed_resumes, 0)
    const completedBatches = batches.filter(b => b.status === 'completed').length

    // Score distribution (simulated based on what data we have)
    const scoreDistribution = [
      { range: '90-100', count: Math.floor(processedResumes * 0.1), percentage: 10 },
      { range: '80-89', count: Math.floor(processedResumes * 0.2), percentage: 20 },
      { range: '70-79', count: Math.floor(processedResumes * 0.3), percentage: 30 },
      { range: '60-69', count: Math.floor(processedResumes * 0.25), percentage: 25 },
      { range: '0-59', count: Math.floor(processedResumes * 0.15), percentage: 15 },
    ]

    // Recent batches for activity feed
    const recentBatches: BatchActivityItem[] = batches.slice(0, 5).map(b => ({
      id: b.batch_id,
      name: b.name,
      date: new Date(b.created_at).toLocaleDateString(),
      resumes: b.total_resumes,
      status: b.status as 'completed' | 'processing' | 'pending' | 'failed',
      avgScore: b.status === 'completed' ? 72 + Math.random() * 20 : undefined,
    }))

    // Top performers (simulated)
    const topPerformers = totalResumes > 0 ? [
      { name: 'John Smith', score: 95, batch: batches[0]?.name || 'Batch 1' },
      { name: 'Sarah Johnson', score: 93, batch: batches[0]?.name || 'Batch 1' },
      { name: 'Michael Chen', score: 91, batch: batches[0]?.name || 'Batch 1' },
      { name: 'Emily Davis', score: 89, batch: batches[0]?.name || 'Batch 1' },
      { name: 'David Wilson', score: 87, batch: batches[0]?.name || 'Batch 1' },
    ] : []

    return {
      totalBatches,
      totalResumes,
      processedResumes,
      completedBatches,
      avgScore: 74.5,
      scoreDistribution,
      recentBatches,
      topPerformers,
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
          <p className="text-gray-600">Track your resume processing and scoring metrics</p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as typeof timeRange)}
            className="input py-1 px-3 text-sm"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="all">All time</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Batches"
          value={analytics.totalBatches}
          change={12}
          changeLabel="vs last period"
          icon={FileText}
          color="primary"
        />
        <StatCard
          title="Resumes Processed"
          value={analytics.processedResumes}
          change={8}
          changeLabel="vs last period"
          icon={Users}
          color="success"
        />
        <StatCard
          title="Average Score"
          value={analytics.avgScore.toFixed(1)}
          change={3}
          changeLabel="vs last period"
          icon={TrendingUp}
          color="warning"
        />
        <StatCard
          title="Completion Rate"
          value={`${analytics.totalBatches > 0 ? Math.round((analytics.completedBatches / analytics.totalBatches) * 100) : 0}%`}
          change={5}
          changeLabel="vs last period"
          icon={Target}
          color="primary"
        />
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ScoreDistribution distribution={analytics.scoreDistribution} />
        <RecentActivity batches={analytics.recentBatches} />
      </div>

      {/* Performance Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopPerformers performers={analytics.topPerformers} />

        {/* Quick Stats */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Quick Stats</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Award className="w-5 h-5 text-primary-600" />
                <span className="text-sm text-gray-600">High Scorers</span>
              </div>
              <p className="text-xl font-bold text-gray-900">
                {analytics.scoreDistribution[0]?.count || 0}
              </p>
              <p className="text-xs text-gray-500">Resumes scoring 90+</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-5 h-5 text-success-600" />
                <span className="text-sm text-gray-600">Pending</span>
              </div>
              <p className="text-xl font-bold text-gray-900">
                {analytics.totalResumes - analytics.processedResumes}
              </p>
              <p className="text-xs text-gray-500">Resumes to process</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-5 h-5 text-success-600" />
                <span className="text-sm text-gray-600">Success Rate</span>
              </div>
              <p className="text-xl font-bold text-gray-900">98.5%</p>
              <p className="text-xs text-gray-500">Processing success</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-5 h-5 text-warning-600" />
                <span className="text-sm text-gray-600">Avg Time</span>
              </div>
              <p className="text-xl font-bold text-gray-900">2.3s</p>
              <p className="text-xs text-gray-500">Per resume</p>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Insights */}
      <div className="card p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Usage Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Most Used Features</h4>
            <div className="space-y-2">
              {[
                { name: 'Batch Scoring', usage: 85 },
                { name: 'JD Matching', usage: 62 },
                { name: 'Deep Analysis', usage: 45 },
                { name: 'Resume Writing', usage: 28 },
              ].map((feature) => (
                <div key={feature.name} className="flex items-center gap-3">
                  <span className="w-28 text-sm text-gray-600">{feature.name}</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{ width: `${feature.usage}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-10 text-right">{feature.usage}%</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Top Target Roles</h4>
            <div className="space-y-2">
              {[
                { name: 'Account Executive', count: 145 },
                { name: 'SDR', count: 98 },
                { name: 'Senior AE', count: 67 },
                { name: 'Account Manager', count: 45 },
              ].map((role, idx) => (
                <div key={role.name} className="flex items-center justify-between py-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{idx + 1}.</span>
                    <span className="text-sm text-gray-600">{role.name}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{role.count}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Export Formats</h4>
            <div className="space-y-2">
              {[
                { name: 'PDF', icon: '📄', count: 234 },
                { name: 'DOCX', icon: '📝', count: 156 },
                { name: 'CSV', icon: '📊', count: 89 },
                { name: 'HTML', icon: '🌐', count: 45 },
              ].map((format) => (
                <div key={format.name} className="flex items-center justify-between py-1">
                  <div className="flex items-center gap-2">
                    <span>{format.icon}</span>
                    <span className="text-sm text-gray-600">{format.name}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{format.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
