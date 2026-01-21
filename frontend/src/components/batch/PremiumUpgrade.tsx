import { Sparkles, Target, MessageSquare, Check, ArrowRight } from 'lucide-react'

interface PremiumUpgradeProps {
  feature?: 'jd_matching' | 'deep_analysis' | 'consulting'
  onUpgrade?: () => void
}

const features = {
  jd_matching: {
    name: 'JD Matching',
    description: 'Match resumes against job descriptions with AI-powered skill analysis',
    icon: Target,
    benefits: [
      'Automatic skill gap analysis',
      'Match score for each candidate',
      'Missing skills identification',
      'Hiring recommendations',
    ],
  },
  deep_analysis: {
    name: 'Deep Analysis',
    description: 'Get comprehensive LLM-powered insights for each resume',
    icon: Sparkles,
    benefits: [
      'Strengths and weaknesses assessment',
      'Culture fit evaluation',
      'Red flag detection',
      'Interview question suggestions',
    ],
  },
  consulting: {
    name: 'Resume Consulting',
    description: 'AI-powered resume improvement suggestions and rewrites',
    icon: MessageSquare,
    benefits: [
      'Section-by-section feedback',
      'Automated rewrites',
      'Role-specific optimization',
      'Interactive chat assistance',
    ],
  },
}

const plans = [
  {
    name: 'Basic',
    price: 29,
    features: ['jd_matching', 'bulk_export'],
    description: 'JD Matching for smarter hiring',
  },
  {
    name: 'Pro',
    price: 99,
    features: ['jd_matching', 'deep_analysis', 'api_access', 'priority_processing'],
    description: 'Full analysis capabilities',
    popular: true,
  },
  {
    name: 'Enterprise',
    price: 499,
    features: ['jd_matching', 'deep_analysis', 'consulting', 'custom_scoring', 'placement_tracking'],
    description: 'Everything including consulting',
  },
]

export default function PremiumUpgrade({ feature, onUpgrade }: PremiumUpgradeProps) {
  const featureInfo = feature ? features[feature] : null

  return (
    <div className="max-w-4xl mx-auto">
      {/* Feature-specific header */}
      {featureInfo && (
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <featureInfo.icon className="w-8 h-8 text-primary-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Unlock {featureInfo.name}
          </h2>
          <p className="text-gray-600 max-w-md mx-auto">
            {featureInfo.description}
          </p>
        </div>
      )}

      {/* Feature benefits */}
      {featureInfo && (
        <div className="bg-gray-50 rounded-xl p-6 mb-8">
          <h3 className="font-semibold text-gray-900 mb-4">What you get:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {featureInfo.benefits.map((benefit, i) => (
              <div key={i} className="flex items-center gap-2 text-gray-700">
                <Check className="w-5 h-5 text-success-500 flex-shrink-0" />
                {benefit}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pricing Plans */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const includesFeature = !feature || plan.features.includes(feature)

          return (
            <div
              key={plan.name}
              className={`card p-6 ${
                plan.popular ? 'ring-2 ring-primary-500 relative' : ''
              } ${!includesFeature ? 'opacity-60' : ''}`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="badge-primary px-3 py-1">Most Popular</span>
                </div>
              )}

              <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{plan.description}</p>

              <div className="my-4">
                <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                <span className="text-gray-500">/month</span>
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-gray-700">
                    <Check
                      className={`w-4 h-4 ${
                        feature && f === feature ? 'text-primary-500' : 'text-success-500'
                      }`}
                    />
                    {features[f as keyof typeof features]?.name || f}
                  </li>
                ))}
              </ul>

              <button
                onClick={onUpgrade}
                disabled={!includesFeature}
                className={`w-full gap-2 ${
                  plan.popular ? 'btn-primary' : 'btn-secondary'
                }`}
              >
                {includesFeature ? (
                  <>
                    Upgrade to {plan.name}
                    <ArrowRight className="w-4 h-4" />
                  </>
                ) : (
                  'Feature not included'
                )}
              </button>
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <p className="text-center text-sm text-gray-500 mt-6">
        All plans include unlimited batches, quick scoring, and CSV/JSON exports.
        <br />
        Cancel anytime. 14-day money-back guarantee.
      </p>
    </div>
  )
}
