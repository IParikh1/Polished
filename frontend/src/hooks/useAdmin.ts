import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getAdminStats,
  getAdminUsers,
  getAdminUser,
  setUserAdminStatus,
  setUserTier,
  getAdminUsage,
  getServiceCosts,
} from '../api/batchClient'

export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: getAdminStats,
    staleTime: 30 * 1000, // 30 seconds
    retry: false, // Don't retry on 403
  })
}

export function useAdminUsers(limit = 50, offset = 0, tier?: string) {
  return useQuery({
    queryKey: ['admin', 'users', limit, offset, tier],
    queryFn: () => getAdminUsers(limit, offset, tier),
    staleTime: 30 * 1000,
    retry: false,
  })
}

export function useAdminUser(userId: string) {
  return useQuery({
    queryKey: ['admin', 'user', userId],
    queryFn: () => getAdminUser(userId),
    enabled: !!userId,
    staleTime: 30 * 1000,
    retry: false,
  })
}

export function useSetUserAdmin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, isAdmin }: { userId: string; isAdmin: boolean }) =>
      setUserAdminStatus(userId, isAdmin),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
  })
}

export function useSetUserTier() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, tier }: { userId: string; tier: string }) =>
      setUserTier(userId, tier),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
  })
}

export function useAdminUsage(period?: string) {
  return useQuery({
    queryKey: ['admin', 'usage', period],
    queryFn: () => getAdminUsage(period),
    staleTime: 30 * 1000,
    retry: false,
  })
}

export function useServiceCosts() {
  return useQuery({
    queryKey: ['admin', 'service-costs'],
    queryFn: getServiceCosts,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
  })
}
