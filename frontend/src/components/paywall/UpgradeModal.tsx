import { X, Check, Zap, Target, Brain, FileEdit, Download, ArrowRight } from 'lucide-react'
import { useStripeConfig, useCreateCheckout } from '../../hooks/useSubscription'
import { useNavigate } from 'react-router-dom'

interface UpgradeModalProps {
  isOpen: boolean
  onClose: () => void
  feature?: string
}

// Feature information mapping
const FEATURE_INFO: Record<
  string,
  {
    name: string
    description: string
    icon: React.ElementType
    benefits: string[]
  }
> = {
  jd_matching: {
    name: 'JD Matching',
    description: 'Match resumes against job descriptions with AI-powered skill matching',
    icon: Target,
    benefits: [
      'AI-powered skill matching',
      'Gap analysis & recommendations',
      'Keyword optimization suggestions',
      'Match score calculation',
    ],
  },
  deep_analysis: {
    name: 'Deep Analysis',
    description: 'Get comprehensive LLM analysis of each resume',
    icon: Brain,
    benefits: [
      'Strengths & weaknesses analysis',
      'Red flag detection',
      'Interview question suggestions',
      'Growth potential assessment',
    ],
  },
  resume_writing: {
    name: 'Resume Writing',
    description: 'AI-powered resume generation and optimization',
    icon: FileEdit,
    benefits: [
      'Full resume generation',
      'Section rewriting',
      'Summary generation',
      'Bullet point enhancement',
    ],
  },
  bulk_export: {
    name: 'PDF/DOCX Export',
    description: 'Export resumes in professional formats',
    icon: Download,
    benefits: [
      'PDF export',
      'DOCX export',
      'Multiple templates',
      'Custom formatting',
    ],
  },
  priority_processing: {
    name: 'Priority Processing',
    description: 'Get faster processing for your batches',
    icon: Zap,
    benefits: [
      'Faster queue priority',
      'Reduced wait times',
      'Bulk processing support',
      'Real-time updates',
    ],
  },
}

export default function UpgradeModal({ isOpen, onClose, feature }: UpgradeModalProps) {
  const navigate = useNavigate()
  const { data: stripeConfig, isLoading: configLoading } = useStripeConfig()
  const createCheckout = useCreateCheckout()

  if (!isOpen) return null

  const featureInfo = feature ? FEATURE_INFO[feature] : null
  const FeatureIcon = featureInfo?.icon || Zap

  const handleUpgrade = async () => {
    if (!stripeConfig?.stripe_configured || !stripeConfig?.pro_price_id) {
      // Stripe not configured - go to pricing page
      onClose()
      navigate('/pricing')
      return
    }

    try {
      const result = await createCheckout.mutateAsync({
        priceId: stripeConfig.pro_price_id,
        successUrl: `${window.location.origin}/settings?subscription=success`,
        cancelUrl: `${window.location.origin}${window.location.pathname}`,
      })

      // Redirect to Stripe checkout
      window.location.href = result.checkout_url
    } catch (error) {
      console.error('Failed to create checkout session:', error)
      // Fallback to pricing page
      onClose()
      navigate('/pricing')
    }
  }

  const handleViewPricing = () => {
    onClose()
    navigate('/pricing')
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 transition-opacity" onClick={onClose} />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden">
          {/* Header gradient */}
          <div className="bg-gradient-to-r from-amber-400 to-amber-500 px-6 py-8 text-white">
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-white/80 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center">
                <FeatureIcon className="w-7 h-7" />
              </div>
              <div>
                <div className="text-amber-100 text-sm font-medium">Unlock</div>
                <h2 className="text-2xl font-bold">
                  {featureInfo?.name || 'Pro Features'}
                </h2>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-6">
            <p className="text-gray-600 mb-6">
              {featureInfo?.description ||
                'Upgrade to Pro to unlock all premium features and supercharge your resume ranking workflow.'}
            </p>

            {/* Feature benefits */}
            {featureInfo?.benefits && (
              <div className="space-y-3 mb-6">
                {featureInfo.benefits.map((benefit, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Check className="w-3 h-3 text-green-600" />
                    </div>
                    <span className="text-gray-700">{benefit}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Pro features overview */}
            {!featureInfo && (
              <div className="space-y-3 mb-6">
                {[
                  'JD Matching with AI',
                  'Deep Resume Analysis',
                  'AI Resume Writing',
                  'PDF & DOCX Export',
                  'Priority Processing',
                ].map((feat, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Check className="w-3 h-3 text-green-600" />
                    </div>
                    <span className="text-gray-700">{feat}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Pricing */}
            <div className="bg-gray-50 rounded-xl p-4 mb-6">
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-bold text-gray-900">$29</span>
                <span className="text-gray-500">/month</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Cancel anytime. 7-day money-back guarantee.
              </p>
            </div>

            {/* Actions */}
            <div className="space-y-3">
              <button
                onClick={handleUpgrade}
                disabled={createCheckout.isPending || configLoading}
                className="w-full bg-gradient-to-r from-amber-400 to-amber-500 text-white font-semibold py-3 px-4 rounded-lg hover:from-amber-500 hover:to-amber-600 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {createCheckout.isPending ? (
                  'Processing...'
                ) : (
                  <>
                    Upgrade to Pro
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              <button
                onClick={handleViewPricing}
                className="w-full text-gray-600 font-medium py-2 hover:text-gray-900 transition-colors"
              >
                View all Pro features
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
