import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { useAuth, useSession } from '@clerk/clerk-react'
import { setAuthToken } from '../api/batchClient'

interface AuthContextValue {
  isAuthReady: boolean
  isAuthenticated: boolean
  authError: string | null
}

const AuthContext = createContext<AuthContextValue>({
  isAuthReady: false,
  isAuthenticated: false,
  authError: null,
})

export function useAuthContext() {
  return useContext(AuthContext)
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { getToken, isSignedIn, isLoaded } = useAuth()
  const { session } = useSession()
  const [isAuthReady, setIsAuthReady] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const maxRetries = 3

  const syncToken = useCallback(async (): Promise<boolean> => {
    if (!isLoaded) {
      return false
    }

    if (isSignedIn && session) {
      try {
        const token = await getToken()
        if (token) {
          setAuthToken(token)
          setAuthError(null)
          return true
        } else {
          console.warn('No token received from Clerk')
          setAuthToken(null)
          return false
        }
      } catch (error) {
        console.error('Failed to get auth token:', error)
        setAuthToken(null)
        return false
      }
    } else {
      setAuthToken(null)
      return true // Auth is "ready" even if not signed in
    }
  }, [getToken, isSignedIn, isLoaded, session])

  useEffect(() => {
    let mounted = true

    async function initAuth() {
      const success = await syncToken()
      if (mounted) {
        if (success) {
          setIsAuthReady(true)
          setRetryCount(0)
        } else if (retryCount < maxRetries) {
          // Retry after a short delay
          setTimeout(() => {
            if (mounted) {
              setRetryCount(prev => prev + 1)
            }
          }, 1000 * (retryCount + 1)) // Exponential backoff: 1s, 2s, 3s
        } else {
          // Max retries reached, set error and allow app to continue
          setAuthError('Failed to initialize authentication. Please refresh the page.')
          setIsAuthReady(true) // Allow app to render, but with error state
        }
      }
    }

    if (isLoaded) {
      initAuth()
    }

    // Refresh token periodically (every 5 minutes)
    const interval = setInterval(syncToken, 5 * 60 * 1000)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [syncToken, isLoaded, retryCount])

  // Also sync when session changes
  useEffect(() => {
    if (isAuthReady && session) {
      syncToken()
    }
  }, [session, isAuthReady, syncToken])

  const value: AuthContextValue = {
    isAuthReady,
    isAuthenticated: isSignedIn ?? false,
    authError,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
