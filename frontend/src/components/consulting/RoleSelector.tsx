import { Briefcase, Code, Database, Cloud, LineChart, Palette, Users, Shield } from 'lucide-react'
import clsx from 'clsx'

interface RoleSelectorProps {
  value: string
  onChange: (role: string) => void
}

const roles = [
  { id: 'software_engineer', label: 'Software Engineer', icon: Code },
  { id: 'data_scientist', label: 'Data Scientist', icon: Database },
  { id: 'devops_engineer', label: 'DevOps Engineer', icon: Cloud },
  { id: 'product_manager', label: 'Product Manager', icon: LineChart },
  { id: 'ux_designer', label: 'UX Designer', icon: Palette },
  { id: 'engineering_manager', label: 'Engineering Manager', icon: Users },
  { id: 'security_engineer', label: 'Security Engineer', icon: Shield },
  { id: 'other', label: 'Other', icon: Briefcase },
]

export default function RoleSelector({ value, onChange }: RoleSelectorProps) {
  return (
    <div>
      <label className="label">Target Role (optional)</label>
      <p className="text-sm text-gray-500 mb-3">
        Select a role to get tailored recommendations
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {roles.map((role) => (
          <button
            key={role.id}
            type="button"
            onClick={() => onChange(value === role.id ? '' : role.id)}
            className={clsx(
              'flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-colors',
              value === role.id
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-600'
            )}
          >
            <role.icon
              className={clsx('w-5 h-5', value === role.id ? 'text-primary-600' : 'text-gray-400')}
            />
            <span className="text-xs font-medium text-center">{role.label}</span>
          </button>
        ))}
      </div>
      {value && value !== 'other' && (
        <p className="text-sm text-primary-600 mt-2">
          Selected: {roles.find((r) => r.id === value)?.label}
        </p>
      )}
      {value === 'other' && (
        <input
          type="text"
          placeholder="Enter custom role..."
          className="input mt-2"
          onChange={(e) => onChange(e.target.value || 'other')}
        />
      )}
    </div>
  )
}
