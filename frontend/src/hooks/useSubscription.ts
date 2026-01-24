import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getSubscriptionStatus,
  checkFeatureAccess,
  getAllFeaturesStatus,
  getStripeConfig,
  createCheckoutSession,
  createPortalSession,
  getPricingInfo,
  SubscriptionResponse,
  FeatureAccessResponse,
  StripeConfig,
  PricingInfo,
} from '../api/batchClient'

// Hook to get user's subscription status
export function useSubscription() {
  return useQuery<SubscriptionResponse>({
    queryKey: ['subscription'],
    queryFn: getSubscriptionStatus,
    staleTime: 60 * 1000, // 1 minute
    retry: 1,
  })
}

// Hook to check access to a specific feature
export function useFeatureAccess(feature: string) {
  return useQuery<FeatureAccessResponse>({
    queryKey: ['feature-access', feature],
    queryFn: () => checkFeatureAccess(feature),
    staleTime: 60 * 1000,
    retry: 1,
  })
}

// Hook to get all features status
export function useAllFeaturesStatus() {
  return useQuery<{ features: FeatureAccessResponse[]; user_tier: string }>({
    queryKey: ['all-features-status'],
    queryFn: getAllFeaturesStatus,
    staleTime: 60 * 1000,
    retry: 1,
  })
}

// Hook to get Stripe configuration
export function useStripeConfig() {
  return useQuery<StripeConfig>({
    queryKey: ['stripe-config'],
    queryFn: getStripeConfig,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Hook to get pricing information
export function usePricingInfo() {
  return useQuery<PricingInfo>({
    queryKey: ['pricing-info'],
    queryFn: getPricingInfo,
    staleTime: 5 * 60 * 1000,
  })
}

// Hook to create a checkout session
export function useCreateCheckout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      priceId,
      successUrl,
      cancelUrl,
    }: {
      priceId: string
      successUrl: string
      cancelUrl: string
    }) => createCheckoutSession(priceId, successUrl, cancelUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription'] })
    },
  })
}

// Hook to create a customer portal session
export function useCreatePortal() {
  return useMutation({
    mutationFn: (returnUrl: string) => createPortalSession(returnUrl),
  })
}

// Helper hook to check if user has a specific feature
export function useHasFeature(feature: string): boolean {
  const { data: subscription } = useSubscription()
  return subscription?.features?.includes(feature) ?? false
}

// Helper hook to check if user is Pro
export function useIsPro(): boolean {
  const { data: subscription } = useSubscription()
  return subscription?.is_pro ?? false
}

// Helper hook to get user's tier
export function useTier(): string {
  const { data: subscription } = useSubscription()
  return subscription?.tier ?? 'free'
}
