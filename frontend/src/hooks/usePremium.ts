import { create } from 'zustand'

export interface PremiumState {
  tier: 'free' | 'basic' | 'pro' | 'enterprise'
  features: string[]
  setTier: (tier: PremiumState['tier']) => void
  hasFeature: (feature: string) => boolean
}

const TIER_FEATURES: Record<PremiumState['tier'], string[]> = {
  free: [],
  basic: ['jd_matching', 'bulk_export'],
  pro: ['jd_matching', 'deep_analysis', 'bulk_export', 'api_access', 'priority_processing'],
  enterprise: [
    'jd_matching',
    'deep_analysis',
    'consulting',
    'bulk_export',
    'api_access',
    'priority_processing',
    'custom_scoring',
    'placement_tracking',
  ],
}

export const usePremium = create<PremiumState>((set, get) => ({
  // Default to enterprise for MVP bypass mode
  tier: 'enterprise',
  features: TIER_FEATURES['enterprise'],

  setTier: (tier) =>
    set({
      tier,
      features: TIER_FEATURES[tier],
    }),

  hasFeature: (feature) => {
    const { features } = get()
    return features.includes(feature)
  },
}))

export function useHasFeature(feature: string): boolean {
  const hasFeature = usePremium((state) => state.hasFeature)
  return hasFeature(feature)
}
