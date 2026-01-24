import { Check, X, Zap, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { usePricingInfo, useSubscription, useStripeConfig, useCreateCheckout } from '../hooks/useSubscription'
import { useNavigate } from 'react-router-dom'

export default function PricingPage() {
  const navigate = useNavigate()
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null)
  const { data: pricingInfo, isLoading: pricingLoading } = usePricingInfo()
  const { data: subscription } = useSubscription()
  const { data: stripeConfig } = useStripeConfig()
  const createCheckout = useCreateCheckout()

  const handleUpgrade = async (priceId: string) => {
    if (!stripeConfig?.stripe_configured) {
      alert('Payment processing is not yet configured. Please check back later.')
      return
    }

    try {
      const result = await createCheckout.mutateAsync({
        priceId,
        successUrl: `${window.location.origin}/settings?subscription=success`,
        cancelUrl: `${window.location.origin}/pricing`,
      })
      window.location.href = result.checkout_url
    } catch (error) {
      console.error('Failed to create checkout:', error)
      alert('Failed to start checkout. Please try again.')
    }
  }

  const toggleFaq = (index: number) => {
    setExpandedFaq(expandedFaq === index ? null : index)
  }

  if (pricingLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  const tiers = pricingInfo?.tiers || []
  const faq = pricingInfo?.faq || []

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Simple, Transparent Pricing
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Choose the plan that's right for you. Upgrade anytime to unlock powerful
          features for your recruiting workflow.
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="grid md:grid-cols-3 gap-8 mb-16">
        {tiers.map((tier) => {
          const isCurrentPlan = subscription?.tier === tier.id
          const isHighlighted = tier.highlighted

          return (
            <div
              key={tier.id}
              className={`relative rounded-2xl border-2 p-8 ${
                isHighlighted
                  ? 'border-amber-400 bg-amber-50/50 shadow-xl'
                  : 'border-gray-200 bg-white'
              }`}
            >
              {isHighlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center gap-1 px-4 py-1 rounded-full bg-gradient-to-r from-amber-400 to-amber-500 text-white text-sm font-semibold">
                    <Zap className="w-4 h-4" />
                    Most Popular
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                <p className="text-gray-600 text-sm">{tier.description}</p>
              </div>

              <div className="mb-6">
                {tier.price !== null ? (
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-gray-900">
                      ${tier.price}
                    </span>
                    <span className="text-gray-500">/{tier.billing}</span>
                  </div>
                ) : (
                  <div className="text-4xl font-bold text-gray-900">Custom</div>
                )}
              </div>

              {/* CTA Button */}
              <div className="mb-8">
                {isCurrentPlan ? (
                  <button
                    disabled
                    className="w-full py-3 px-4 rounded-lg bg-gray-100 text-gray-500 font-semibold cursor-not-allowed"
                  >
                    Current Plan
                  </button>
                ) : tier.id === 'enterprise' ? (
                  <a
                    href="mailto:support@polished.app?subject=Enterprise%20Plan%20Inquiry"
                    className="block w-full py-3 px-4 rounded-lg bg-gray-900 text-white font-semibold text-center hover:bg-gray-800 transition-colors"
                  >
                    Contact Sales
                  </a>
                ) : tier.id === 'pro' ? (
                  <button
                    onClick={() => handleUpgrade(tier.price_id || '')}
                    disabled={createCheckout.isPending || !stripeConfig?.stripe_configured}
                    className="w-full py-3 px-4 rounded-lg bg-gradient-to-r from-amber-400 to-amber-500 text-white font-semibold hover:from-amber-500 hover:to-amber-600 transition-all disabled:opacity-50"
                  >
                    {createCheckout.isPending ? 'Processing...' : tier.cta}
                  </button>
                ) : (
                  <button
                    disabled
                    className="w-full py-3 px-4 rounded-lg bg-gray-100 text-gray-600 font-semibold cursor-default"
                  >
                    {tier.cta}
                  </button>
                )}
              </div>

              {/* Features */}
              <div className="space-y-3">
                {tier.features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-3 h-3 text-green-600" />
                    </div>
                    <span className="text-gray-700 text-sm">{feature}</span>
                  </div>
                ))}

                {tier.limitations.map((limitation, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <X className="w-3 h-3 text-gray-400" />
                    </div>
                    <span className="text-gray-400 text-sm">{limitation}</span>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Feature Comparison */}
      <div className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
          Feature Comparison
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="py-4 px-4 text-left text-gray-600 font-medium">Feature</th>
                <th className="py-4 px-4 text-center text-gray-600 font-medium">Free</th>
                <th className="py-4 px-4 text-center text-amber-600 font-medium bg-amber-50/50">
                  Pro
                </th>
                <th className="py-4 px-4 text-center text-gray-600 font-medium">Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {[
                { feature: 'Batches per month', free: '5', pro: '100', enterprise: 'Unlimited' },
                { feature: 'Resumes per batch', free: '50', pro: '500', enterprise: 'Unlimited' },
                { feature: 'Basic scoring', free: true, pro: true, enterprise: true },
                { feature: 'Role optimization', free: true, pro: true, enterprise: true },
                { feature: 'CSV export', free: true, pro: true, enterprise: true },
                { feature: 'JD Matching', free: false, pro: true, enterprise: true },
                { feature: 'Deep Analysis', free: false, pro: true, enterprise: true },
                { feature: 'Resume Writing', free: false, pro: true, enterprise: true },
                { feature: 'PDF/DOCX Export', free: false, pro: true, enterprise: true },
                { feature: 'Priority Processing', free: false, pro: true, enterprise: true },
                { feature: 'Custom Scoring', free: false, pro: false, enterprise: true },
                { feature: 'API Access', free: false, pro: false, enterprise: true },
                { feature: 'SSO/SAML', free: false, pro: false, enterprise: true },
                { feature: 'Dedicated Support', free: false, pro: false, enterprise: true },
              ].map((row, index) => (
                <tr key={index} className="border-b">
                  <td className="py-4 px-4 text-gray-700">{row.feature}</td>
                  <td className="py-4 px-4 text-center">
                    {typeof row.free === 'boolean' ? (
                      row.free ? (
                        <Check className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <X className="w-5 h-5 text-gray-300 mx-auto" />
                      )
                    ) : (
                      <span className="text-gray-600">{row.free}</span>
                    )}
                  </td>
                  <td className="py-4 px-4 text-center bg-amber-50/50">
                    {typeof row.pro === 'boolean' ? (
                      row.pro ? (
                        <Check className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <X className="w-5 h-5 text-gray-300 mx-auto" />
                      )
                    ) : (
                      <span className="text-gray-600">{row.pro}</span>
                    )}
                  </td>
                  <td className="py-4 px-4 text-center">
                    {typeof row.enterprise === 'boolean' ? (
                      row.enterprise ? (
                        <Check className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <X className="w-5 h-5 text-gray-300 mx-auto" />
                      )
                    ) : (
                      <span className="text-gray-600">{row.enterprise}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* FAQ */}
      <div className="max-w-3xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
          Frequently Asked Questions
        </h2>
        <div className="space-y-4">
          {faq.map((item, index) => (
            <div
              key={index}
              className="border rounded-lg overflow-hidden"
            >
              <button
                onClick={() => toggleFaq(index)}
                className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50"
              >
                <span className="font-medium text-gray-900">{item.question}</span>
                {expandedFaq === index ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
              {expandedFaq === index && (
                <div className="px-6 pb-4">
                  <p className="text-gray-600">{item.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Money Back Guarantee */}
      <div className="text-center mt-12 p-8 bg-gray-50 rounded-2xl">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          7-Day Money-Back Guarantee
        </h3>
        <p className="text-gray-600 max-w-xl mx-auto">
          Not satisfied with Pro? Contact us within 7 days for a full refund.
          No questions asked.
        </p>
      </div>
    </div>
  )
}
