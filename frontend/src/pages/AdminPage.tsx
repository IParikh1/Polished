import { useState } from 'react'
import {
  Users,
  BarChart3,
  Shield,
  DollarSign,
  FileText,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
  Crown,
  AlertCircle,
} from 'lucide-react'
import {
  useAdminStats,
  useAdminUsers,
  useSetUserAdmin,
  useSetUserTier,
} from '../hooks/useAdmin'
import type { AdminUser } from '../api/batchClient'
import { format, parseISO } from 'date-fns'
import clsx from 'clsx'

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  color: 'primary' | 'success' | 'warning' | 'danger'
}) {
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
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={clsx('p-3 rounded-lg', colorClasses[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  )
}

function TierBadge({ tier }: { tier: string }) {
  const classes = {
    free: 'bg-gray-100 text-gray-700',
    pro: 'bg-primary-100 text-primary-700',
    enterprise: 'bg-purple-100 text-purple-700',
  }

  return (
    <span
      className={clsx(
        'text-xs px-2 py-0.5 rounded-full font-medium',
        classes[tier as keyof typeof classes] || classes.free
      )}
    >
      {tier.charAt(0).toUpperCase() + tier.slice(1)}
    </span>
  )
}

function UserRow({
  user,
  expanded,
  onToggle,
  onSetAdmin,
  onSetTier,
}: {
  user: AdminUser
  expanded: boolean
  onToggle: () => void
  onSetAdmin: (isAdmin: boolean) => void
  onSetTier: (tier: string) => void
}) {
  const [showTierDropdown, setShowTierDropdown] = useState(false)

  return (
    <>
      <tr
        className="hover:bg-gray-50 cursor-pointer"
        onClick={onToggle}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
            <div>
              <div className="font-medium text-gray-900">
                {user.name || 'No name'}
                {user.is_admin && (
                  <Crown className="w-4 h-4 text-warning-500 inline ml-2" />
                )}
              </div>
              <div className="text-sm text-gray-500">{user.email}</div>
            </div>
          </div>
        </td>
        <td className="px-4 py-3">
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowTierDropdown(!showTierDropdown)
              }}
              className="flex items-center gap-1"
            >
              <TierBadge tier={user.subscription_tier} />
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </button>
            {showTierDropdown && (
              <div className="absolute z-10 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg py-1">
                {['free', 'pro', 'enterprise'].map((tier) => (
                  <button
                    key={tier}
                    onClick={(e) => {
                      e.stopPropagation()
                      onSetTier(tier)
                      setShowTierDropdown(false)
                    }}
                    className={clsx(
                      'w-full px-3 py-1 text-left text-sm hover:bg-gray-100',
                      tier === user.subscription_tier && 'bg-gray-50 font-medium'
                    )}
                  >
                    {tier.charAt(0).toUpperCase() + tier.slice(1)}
                  </button>
                ))}
              </div>
            )}
          </div>
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {user.subscription_status || '-'}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {user.usage?.batches_created || 0}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {user.usage?.resumes_processed || 0}
        </td>
        <td className="px-4 py-3 text-sm font-medium text-gray-900">
          ${(user.cost?.total_cost || 0).toFixed(2)}
        </td>
        <td className="px-4 py-3 text-sm text-gray-500">
          {format(parseISO(user.created_at), 'MMM d, yyyy')}
        </td>
        <td className="px-4 py-3">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onSetAdmin(!user.is_admin)
            }}
            className={clsx(
              'text-xs px-2 py-1 rounded',
              user.is_admin
                ? 'bg-danger-100 text-danger-700 hover:bg-danger-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}
          >
            {user.is_admin ? 'Remove Admin' : 'Make Admin'}
          </button>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-gray-50">
          <td colSpan={8} className="px-4 py-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-500">User ID</p>
                <p className="text-sm font-mono text-gray-700 truncate">{user.user_id}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Stripe Customer</p>
                <p className="text-sm font-mono text-gray-700 truncate">
                  {user.stripe_customer_id || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Last Updated</p>
                <p className="text-sm text-gray-700">
                  {format(parseISO(user.updated_at), 'MMM d, yyyy HH:mm')}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Usage Period</p>
                <p className="text-sm text-gray-700">{user.usage?.period || 'N/A'}</p>
              </div>
            </div>
            {user.usage && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500 mb-2">Usage Breakdown</p>
                <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      {user.usage.batches_created}
                    </p>
                    <p className="text-xs text-gray-500">Batches</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      {user.usage.resumes_processed}
                    </p>
                    <p className="text-xs text-gray-500">Resumes</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      {user.usage.exports_count}
                    </p>
                    <p className="text-xs text-gray-500">Exports</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      {user.usage.jd_matches}
                    </p>
                    <p className="text-xs text-gray-500">JD Matches</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      {user.usage.resume_writes}
                    </p>
                    <p className="text-xs text-gray-500">Resume Writes</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      {user.usage.deep_analyses}
                    </p>
                    <p className="text-xs text-gray-500">Deep Analyses</p>
                  </div>
                </div>
              </div>
            )}
            {user.cost && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500 mb-2">Cost Breakdown</p>
                <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      ${user.cost.batches_cost.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">Batches</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      ${user.cost.resumes_cost.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">Resumes</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      ${user.cost.exports_cost.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">Exports</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      ${user.cost.jd_matches_cost.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">JD Matches</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      ${user.cost.resume_writes_cost.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">Resume Writes</p>
                  </div>
                  <div className="bg-white p-2 rounded border border-gray-200">
                    <p className="text-lg font-bold text-gray-900">
                      ${user.cost.deep_analyses_cost.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">Deep Analyses</p>
                  </div>
                </div>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

export default function AdminPage() {
  const [expandedUserId, setExpandedUserId] = useState<string | null>(null)
  const [tierFilter, setTierFilter] = useState<string | undefined>(undefined)

  const { data: stats, isLoading: loadingStats, error: statsError, refetch: refetchStats } = useAdminStats()
  const { data: usersData, isLoading: loadingUsers, error: usersError, refetch: refetchUsers } = useAdminUsers(
    100,
    0,
    tierFilter
  )
  const setAdminMutation = useSetUserAdmin()
  const setTierMutation = useSetUserTier()

  const handleRefresh = () => {
    refetchStats()
    refetchUsers()
  }

  // Check if user has admin access (403 error means no access)
  // Only show Access Denied for actual 403 errors, not for empty results or loading states
  const is403Error = (error: unknown): boolean => {
    if (!error) return false
    const axiosError = error as { response?: { status?: number } }
    return axiosError?.response?.status === 403
  }

  const isUnauthorized = is403Error(statsError) || is403Error(usersError)

  if (isUnauthorized) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <AlertCircle className="w-12 h-12 text-danger-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
        <p className="text-gray-600">You do not have admin privileges.</p>
      </div>
    )
  }

  if (loadingStats || loadingUsers) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary-600" />
            Admin Dashboard
          </h1>
          <p className="text-gray-600">Manage users and monitor usage</p>
        </div>
        <button onClick={handleRefresh} className="btn-secondary gap-2">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Users"
            value={stats.total_users}
            subtitle={`${stats.users_by_tier.pro || 0} Pro, ${stats.users_by_tier.enterprise || 0} Enterprise`}
            icon={Users}
            color="primary"
          />
          <StatCard
            title="Total Batches"
            value={stats.total_batches}
            subtitle={`Period: ${stats.period}`}
            icon={FileText}
            color="success"
          />
          <StatCard
            title="Total Resumes"
            value={stats.total_resumes}
            icon={BarChart3}
            color="warning"
          />
          <StatCard
            title="Revenue"
            value={`$${stats.total_revenue.toFixed(2)}`}
            subtitle="From placements"
            icon={DollarSign}
            color="success"
          />
        </div>
      )}

      {/* Tier Distribution */}
      {stats && (
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Users by Tier</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-3xl font-bold text-gray-700">
                {stats.users_by_tier.free || 0}
              </p>
              <p className="text-sm text-gray-600">Free</p>
            </div>
            <div className="text-center p-4 bg-primary-50 rounded-lg">
              <p className="text-3xl font-bold text-primary-700">
                {stats.users_by_tier.pro || 0}
              </p>
              <p className="text-sm text-primary-600">Pro</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-3xl font-bold text-purple-700">
                {stats.users_by_tier.enterprise || 0}
              </p>
              <p className="text-sm text-purple-600">Enterprise</p>
            </div>
          </div>
        </div>
      )}

      {/* Users Table */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">All Users</h3>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Filter:</span>
            <select
              value={tierFilter || ''}
              onChange={(e) => setTierFilter(e.target.value || undefined)}
              className="input py-1 px-2 text-sm"
            >
              <option value="">All Tiers</option>
              <option value="free">Free</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  User
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Tier
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Batches
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Resumes
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Cost
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Joined
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {usersData?.users.map((user) => (
                <UserRow
                  key={user.user_id}
                  user={user}
                  expanded={expandedUserId === user.user_id}
                  onToggle={() =>
                    setExpandedUserId(
                      expandedUserId === user.user_id ? null : user.user_id
                    )
                  }
                  onSetAdmin={(isAdmin) =>
                    setAdminMutation.mutate({ userId: user.user_id, isAdmin })
                  }
                  onSetTier={(tier) =>
                    setTierMutation.mutate({ userId: user.user_id, tier })
                  }
                />
              ))}
              {usersData?.users.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                    No users found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {usersData && (
          <div className="mt-4 text-sm text-gray-500">
            Showing {usersData.users.length} of {usersData.total} users
          </div>
        )}
      </div>
    </div>
  )
}
