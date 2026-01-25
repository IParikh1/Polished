import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { setAuthToken } from '../api/batchClient'

// Check if Clerk is configured - this is determined at module load time
const isClerkConfigured = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

/**
 * Hook to sync Clerk auth token with the API client.
 * Should be used in a component that's always rendered when authenticated.
 * If Clerk isn't configured, this sets auth token to null.
 *
 * We export different implementations to avoid conditional hook calls.
 * The choice is made at module load time (constant), satisfying React's rules.
 */
export const useAuthSync = isClerkConfigured ? useAuthSyncWithClerk : useAuthSyncNoOp

// No-op version when Clerk isn't configured
function useAuthSyncNoOp() {
  useEffect(() => {
    setAuthToken(null)
  }, [])
}

// Version that syncs with Clerk auth
function useAuthSyncWithClerk() {
  const { getToken, isSignedIn } = useAuth()

  useEffect(() => {
    async function syncToken() {
      if (isSignedIn) {
        try {
          const token = await getToken()
          setAuthToken(token)
        } catch (error) {
          console.error('Failed to get auth token:', error)
          setAuthToken(null)
        }
      } else {
        setAuthToken(null)
      }
    }

    syncToken()

    // Refresh token periodically (every 5 minutes)
    const interval = setInterval(syncToken, 5 * 60 * 1000)

    return () => clearInterval(interval)
  }, [getToken, isSignedIn])
}
