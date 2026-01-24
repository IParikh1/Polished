import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { setAuthToken } from '../api/batchClient'

/**
 * Hook to sync Clerk auth token with the API client.
 * Should be used in a component that's always rendered when authenticated.
 */
export function useAuthSync() {
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
