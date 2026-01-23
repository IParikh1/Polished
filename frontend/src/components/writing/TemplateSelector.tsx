import { FileText, Briefcase, Sparkles, Crown, Minus } from 'lucide-react'
import clsx from 'clsx'

export type ResumeTemplate = 'modern' | 'classic' | 'ats_friendly' | 'executive' | 'minimal'

interface TemplateSelectorProps {
  value: ResumeTemplate
  onChange: (template: ResumeTemplate) => void
  disabled?: boolean
  className?: string
}

const templates = [
  {
    id: 'modern' as ResumeTemplate,
    label: 'Modern',
    icon: Sparkles,
    description: 'Clean, contemporary design with accent colors',
    recommended: ['sdr', 'account_executive', 'senior_ae'],
  },
  {
    id: 'classic' as ResumeTemplate,
    label: 'Classic',
    icon: Briefcase,
    description: 'Traditional format with centered header',
    recommended: ['sales_manager', 'account_manager'],
  },
  {
    id: 'ats_friendly' as ResumeTemplate,
    label: 'ATS-Friendly',
    icon: FileText,
    description: 'Optimized for Applicant Tracking Systems',
    recommended: ['entry_sdr', 'sdr', 'account_executive'],
  },
  {
    id: 'executive' as ResumeTemplate,
    label: 'Executive',
    icon: Crown,
    description: 'Sophisticated design for senior roles',
    recommended: ['senior_ae', 'sales_manager'],
  },
  {
    id: 'minimal' as ResumeTemplate,
    label: 'Minimal',
    icon: Minus,
    description: 'Clean and simple, focuses on content',
    recommended: ['entry_sdr', 'sdr'],
  },
]

export function TemplateSelector({
  value,
  onChange,
  disabled,
  className,
}: TemplateSelectorProps) {
  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Resume Template
      </label>
      <p className="text-sm text-gray-500 mb-3">
        Choose a template style for your generated resume
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {templates.map((template) => {
          const Icon = template.icon
          const isSelected = value === template.id

          return (
            <button
              key={template.id}
              type="button"
              disabled={disabled}
              onClick={() => onChange(template.id)}
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
                <span
                  className={clsx(
                    'font-medium text-sm block',
                    isSelected ? 'text-primary-900' : 'text-gray-900'
                  )}
                >
                  {template.label}
                </span>
                <p
                  className={clsx(
                    'text-xs mt-1',
                    isSelected ? 'text-primary-700' : 'text-gray-500'
                  )}
                >
                  {template.description}
                </p>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export { templates }
export default TemplateSelector
