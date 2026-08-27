import { useState } from 'react'
import {
  Briefcase,
  TrendingUp,
  Code,
  Database,
  LineChart,
  Megaphone,
  Calculator,
  type LucideIcon,
} from 'lucide-react'
import clsx from 'clsx'

interface RoleSelectorProps {
  value: string
  onChange: (role: string) => void
}

interface RoleCategory {
  id: string
  label: string
  icon: LucideIcon
  roles: { id: string; label: string }[]
}

// Tech Sales ids mirror the backend SalesRole enum so its role-specific
// prompts and keyword sets line up; other roles are passed to the AI as-is.
const categories: RoleCategory[] = [
  {
    id: 'tech_sales',
    label: 'Tech Sales',
    icon: TrendingUp,
    roles: [
      { id: 'entry_sdr', label: 'Entry SDR' },
      { id: 'sdr', label: 'SDR / BDR' },
      { id: 'account_executive', label: 'Account Executive' },
      { id: 'senior_ae', label: 'Senior / Enterprise AE' },
      { id: 'account_manager', label: 'Account Manager / CSM' },
      { id: 'sales_manager', label: 'Sales Manager / Director' },
    ],
  },
  {
    id: 'software',
    label: 'Software Engineering',
    icon: Code,
    roles: [
      { id: 'software_engineer', label: 'Software Engineer' },
      { id: 'frontend_engineer', label: 'Frontend Engineer' },
      { id: 'backend_engineer', label: 'Backend Engineer' },
      { id: 'devops_engineer', label: 'DevOps / SRE' },
      { id: 'security_engineer', label: 'Security Engineer' },
      { id: 'engineering_manager', label: 'Engineering Manager' },
    ],
  },
  {
    id: 'data',
    label: 'Data & AI',
    icon: Database,
    roles: [
      { id: 'data_scientist', label: 'Data Scientist' },
      { id: 'data_engineer', label: 'Data Engineer' },
      { id: 'ml_engineer', label: 'ML Engineer' },
      { id: 'data_analyst', label: 'Data Analyst' },
      { id: 'analytics_manager', label: 'Analytics Manager' },
    ],
  },
  {
    id: 'product',
    label: 'Product & Design',
    icon: LineChart,
    roles: [
      { id: 'product_manager', label: 'Product Manager' },
      { id: 'technical_program_manager', label: 'Technical Program Manager' },
      { id: 'ux_designer', label: 'UX Designer' },
      { id: 'product_designer', label: 'Product Designer' },
    ],
  },
  {
    id: 'marketing',
    label: 'Marketing & Growth',
    icon: Megaphone,
    roles: [
      { id: 'marketing_manager', label: 'Marketing Manager' },
      { id: 'growth_marketer', label: 'Growth Marketer' },
      { id: 'content_strategist', label: 'Content Strategist' },
      { id: 'demand_gen_manager', label: 'Demand Gen Manager' },
    ],
  },
  {
    id: 'business_ops',
    label: 'Finance & Operations',
    icon: Calculator,
    roles: [
      { id: 'financial_analyst', label: 'Financial Analyst' },
      { id: 'operations_manager', label: 'Operations Manager' },
      { id: 'project_manager', label: 'Project Manager' },
      { id: 'business_analyst', label: 'Business Analyst' },
    ],
  },
]

function findCategoryForRole(roleId: string): string | null {
  for (const cat of categories) {
    if (cat.roles.some((r) => r.id === roleId)) return cat.id
  }
  return null
}

function findRoleLabel(roleId: string): string | undefined {
  for (const cat of categories) {
    const role = cat.roles.find((r) => r.id === roleId)
    if (role) return role.label
  }
  return undefined
}

export default function RoleSelector({ value, onChange }: RoleSelectorProps) {
  // Default to the category containing the current value, else Tech Sales;
  // a value not in any category means a custom "Other" role
  const [activeCategory, setActiveCategory] = useState<string>(
    () => findCategoryForRole(value) || (value ? 'other' : categories[0].id)
  )

  const active = categories.find((c) => c.id === activeCategory)
  const selectedLabel = value ? findRoleLabel(value) : undefined

  return (
    <div>
      <label className="label">Target Role (optional)</label>
      <p className="text-sm text-gray-500 mb-3">
        Pick a job type, then a role, to get tailored recommendations
      </p>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2 mb-3">
        {categories.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => setActiveCategory(cat.id)}
            className={clsx(
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors',
              activeCategory === cat.id
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-600'
            )}
          >
            <cat.icon className="w-3.5 h-3.5" />
            {cat.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setActiveCategory('other')}
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors',
            activeCategory === 'other'
              ? 'border-primary-500 bg-primary-50 text-primary-700'
              : 'border-gray-200 hover:border-gray-300 text-gray-600'
          )}
        >
          <Briefcase className="w-3.5 h-3.5" />
          Other
        </button>
      </div>

      {/* Roles in the active category */}
      {active && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {active.roles.map((role) => (
            <button
              key={role.id}
              type="button"
              onClick={() => onChange(value === role.id ? '' : role.id)}
              className={clsx(
                'p-3 rounded-lg border-2 text-xs font-medium text-center transition-colors',
                value === role.id
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-600'
              )}
            >
              {role.label}
            </button>
          ))}
        </div>
      )}

      {/* Custom role input */}
      {activeCategory === 'other' && (
        <input
          type="text"
          placeholder="Enter your target role (e.g. Solutions Architect)..."
          className="input"
          defaultValue={findRoleLabel(value) ? '' : value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}

      {value && selectedLabel && (
        <p className="text-sm text-primary-600 mt-2">Selected: {selectedLabel}</p>
      )}
      {value && !selectedLabel && (
        <p className="text-sm text-primary-600 mt-2">Selected: {value}</p>
      )}
    </div>
  )
}
