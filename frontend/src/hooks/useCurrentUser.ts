import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCurrentUser, syncUserInfo, CurrentUserResponse } from '../api/batchClient'

/**
 * Hook to get and manage the current user's profile.
 *
 * This hook:
 * 1. Fetches the current user from /user/me on mount
 * 2. Creates the user in DynamoDB if they don't exist
 * 3. Returns user info including isAdmin status
 *
 * Use this instead of useAdminStats for checking admin status,
 * as it ensures the user record exists first.
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: getCurrentUser,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Only retry once on failure
    refetchOnWindowFocus: false,
  })
}

/**
 * Hook to sync user info from Clerk to DynamoDB.
 * Call this if the user updated their profile in Clerk.
 */
export function useSyncUserInfo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: syncUserInfo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] })
    },
  })
}

/**
 * Helper to check if user is admin from the current user data.
 */
export function isUserAdmin(user: CurrentUserResponse | undefined): boolean {
  return user?.is_admin ?? false
}
