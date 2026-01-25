import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { setAuthToken } from '../api/batchClient'

// Check if Clerk is configured
const isClerkConfigured = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

/**
 * Hook to sync Clerk auth token with the API client.
 * Should be used in a component that's always rendered when authenticated.
 * If Clerk isn't configured, this is a no-op.
 */
export function useAuthSync() {
  // If Clerk isn't configured, don't try to use Clerk hooks
  if (!isClerkConfigured) {
    return useAuthSyncDisabled()
  }

  return useAuthSyncEnabled()
}

// No-op version when Clerk isn't configured
function useAuthSyncDisabled() {
  useEffect(() => {
    // No auth token when Clerk isn't configured
    setAuthToken(null)
  }, [])
}

// Active version when Clerk is configured
function useAuthSyncEnabled() {
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
