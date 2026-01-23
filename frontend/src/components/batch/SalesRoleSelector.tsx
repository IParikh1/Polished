import {
  Phone,
  Target,
  TrendingUp,
  Building2,
  Users,
  Crown,
  Briefcase
} from 'lucide-react'
import clsx from 'clsx'

export type SalesRole =
  | 'entry_sdr'
  | 'sdr'
  | 'account_executive'
  | 'senior_ae'
  | 'account_manager'
  | 'sales_manager'

interface SalesRoleSelectorProps {
  value: SalesRole | null
  onChange: (role: SalesRole | null) => void
  disabled?: boolean
  className?: string
}

const salesRoles = [
  {
    id: 'entry_sdr' as SalesRole,
    label: 'Entry-Level SDR',
    sublabel: '0-1 years',
    icon: Phone,
    description: 'New to sales, building pipeline fundamentals'
  },
  {
    id: 'sdr' as SalesRole,
    label: 'SDR/BDR',
    sublabel: '1-3 years',
    icon: Target,
    description: 'Experienced in outbound, booking qualified meetings'
  },
  {
    id: 'account_executive' as SalesRole,
    label: 'Account Executive',
    sublabel: '2-5 years',
    icon: TrendingUp,
    description: 'Full-cycle sales, closing deals and managing pipeline'
  },
  {
    id: 'senior_ae' as SalesRole,
    label: 'Senior/Enterprise AE',
    sublabel: '5+ years',
    icon: Building2,
    description: 'Large deals, complex sales, C-suite relationships'
  },
  {
    id: 'account_manager' as SalesRole,
    label: 'Account Manager',
    sublabel: '2+ years',
    icon: Users,
    description: 'Customer retention, upsells, NRR focus'
  },
  {
    id: 'sales_manager' as SalesRole,
    label: 'Sales Manager/Director',
    sublabel: '5+ years',
    icon: Crown,
    description: 'Team leadership, revenue responsibility'
  },
]

export function SalesRoleSelector({ value, onChange, disabled, className }: SalesRoleSelectorProps) {
  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Target Sales Role
      </label>
      <p className="text-sm text-gray-500 mb-3">
        Select the role this resume is targeting for optimized analysis
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {salesRoles.map((role) => {
          const Icon = role.icon
          const isSelected = value === role.id

          return (
            <button
              key={role.id}
              type="button"
              disabled={disabled}
              onClick={() => onChange(isSelected ? null : role.id)}
              className={clsx(
                'flex items-start gap-3 p-4 rounded-lg border-2 transition-all text-left',
                disabled && 'opacity-50 cursor-not-allowed',
                isSelected
                  ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-500'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              )}
            >
              <div
                className={clsx(
                  'flex-shrink-0 p-2 rounded-lg',
                  isSelected ? 'bg-primary-100' : 'bg-gray-100'
                )}
              >
                <Icon
                  className={clsx(
                    'w-5 h-5',
                    isSelected ? 'text-primary-600' : 'text-gray-500'
                  )}
                />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span
                    className={clsx(
                      'font-medium text-sm',
                      isSelected ? 'text-primary-900' : 'text-gray-900'
                    )}
                  >
                    {role.label}
                  </span>
                  <span
                    className={clsx(
                      'text-xs px-1.5 py-0.5 rounded-full',
                      isSelected
                        ? 'bg-primary-200 text-primary-700'
                        : 'bg-gray-200 text-gray-600'
                    )}
                  >
                    {role.sublabel}
                  </span>
                </div>
                <p
                  className={clsx(
                    'text-xs mt-1',
                    isSelected ? 'text-primary-700' : 'text-gray-500'
                  )}
                >
                  {role.description}
                </p>
              </div>
            </button>
          )
        })}
      </div>

      {value && (
        <div className="mt-3 flex items-center gap-2 text-sm">
          <Briefcase className="w-4 h-4 text-primary-500" />
          <span className="text-primary-700">
            Optimizing for: <strong>{salesRoles.find(r => r.id === value)?.label}</strong>
          </span>
          <button
            type="button"
            onClick={() => onChange(null)}
            className="text-gray-400 hover:text-gray-600 ml-auto"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  )
}

export function SalesRoleDisplay({ role }: { role: SalesRole | null }) {
  if (!role) return null

  const roleInfo = salesRoles.find(r => r.id === role)
  if (!roleInfo) return null

  const Icon = roleInfo.icon

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-50 rounded-full">
      <Icon className="w-4 h-4 text-primary-600" />
      <span className="text-sm font-medium text-primary-700">{roleInfo.label}</span>
    </div>
  )
}

export { salesRoles }
export default SalesRoleSelector
