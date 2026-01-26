import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useUser } from '@clerk/clerk-react'
import { getCurrentUser, syncUserInfo, CurrentUserResponse } from '../api/batchClient'

/**
 * Hook to get and manage the current user's profile.
 *
 * This hook:
 * 1. Gets email from Clerk's useUser() hook (since JWT may not include it)
 * 2. Passes email to /user/me endpoint
 * 3. Creates the user in DynamoDB if they don't exist
 * 4. Returns user info including isAdmin status
 *
 * Use this instead of useAdminStats for checking admin status,
 * as it ensures the user record exists first.
 */
export function useCurrentUser() {
  // Get user info from Clerk (includes email that JWT doesn't have)
  const { user: clerkUser, isLoaded: clerkLoaded } = useUser()

  // Extract email and name from Clerk user
  const email = clerkUser?.primaryEmailAddress?.emailAddress
  const name = clerkUser?.fullName || clerkUser?.firstName || undefined

  return useQuery({
    queryKey: ['currentUser', email], // Include email in key so it refetches if email changes
    queryFn: () => getCurrentUser(email, name),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Only retry once on failure
    refetchOnWindowFocus: false,
    enabled: clerkLoaded, // Only run query after Clerk has loaded
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
