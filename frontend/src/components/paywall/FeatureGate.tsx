import { ReactNode, useState } from 'react'
import { Lock } from 'lucide-react'
import { useFeatureAccess, useSubscription } from '../../hooks/useSubscription'
import UpgradeModal from './UpgradeModal'

interface FeatureGateProps {
  feature: string
  children: ReactNode
  fallback?: ReactNode
  showOverlay?: boolean
}

export default function FeatureGate({
  feature,
  children,
  fallback,
  showOverlay = true,
}: FeatureGateProps) {
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const { data: subscription, isLoading } = useSubscription()

  // Check if feature is available
  const hasAccess = subscription?.features?.includes(feature) ?? false

  // If loading, show children with loading state
  if (isLoading) {
    return <>{children}</>
  }

  // If user has access, render children normally
  if (hasAccess) {
    return <>{children}</>
  }

  // If no access and fallback provided, render fallback
  if (fallback) {
    return <>{fallback}</>
  }

  // Default: render children with overlay
  if (showOverlay) {
    return (
      <>
        <div className="relative">
          {/* Dimmed content */}
          <div className="opacity-50 pointer-events-none select-none filter grayscale">
            {children}
          </div>

          {/* Overlay with lock and upgrade prompt */}
          <div
            className="absolute inset-0 flex items-center justify-center cursor-pointer bg-gray-900/10 rounded-lg"
            onClick={() => setShowUpgradeModal(true)}
          >
            <div className="bg-white/95 backdrop-blur-sm px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 border border-gray-200">
              <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
                <Lock className="w-4 h-4 text-amber-600" />
              </div>
              <div>
                <div className="font-medium text-gray-900 text-sm">Pro Feature</div>
                <div className="text-xs text-gray-500">Click to upgrade</div>
              </div>
            </div>
          </div>
        </div>

        <UpgradeModal
          isOpen={showUpgradeModal}
          onClose={() => setShowUpgradeModal(false)}
          feature={feature}
        />
      </>
    )
  }

  // Just hide the content
  return null
}

// Badge component to show "Pro" label
export function ProBadge({ className = '' }: { className?: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gradient-to-r from-amber-400 to-amber-500 text-white ${className}`}
    >
      PRO
    </span>
  )
}

// Button variant that shows upgrade modal for non-Pro users
interface ProButtonProps {
  feature: string
  onClick?: () => void
  children: ReactNode
  className?: string
  disabled?: boolean
}

export function ProButton({
  feature,
  onClick,
  children,
  className = '',
  disabled = false,
}: ProButtonProps) {
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const { data: subscription } = useSubscription()
  const hasAccess = subscription?.features?.includes(feature) ?? false

  const handleClick = () => {
    if (hasAccess && onClick) {
      onClick()
    } else if (!hasAccess) {
      setShowUpgradeModal(true)
    }
  }

  return (
    <>
      <button
        onClick={handleClick}
        disabled={disabled}
        className={`relative ${className} ${!hasAccess ? 'opacity-75' : ''}`}
      >
        {children}
        {!hasAccess && (
          <Lock className="w-3 h-3 absolute top-1 right-1 text-amber-500" />
        )}
      </button>

      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        feature={feature}
      />
    </>
  )
}
