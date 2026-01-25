import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { useAuth, useSession } from '@clerk/clerk-react'
import { setAuthToken } from '../api/batchClient'

interface AuthContextValue {
  isAuthReady: boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue>({
  isAuthReady: false,
  isAuthenticated: false,
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

  const syncToken = useCallback(async () => {
    if (!isLoaded) {
      return false
    }

    if (isSignedIn && session) {
      try {
        const token = await getToken()
        if (token) {
          setAuthToken(token)
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
      if (mounted && success) {
        setIsAuthReady(true)
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
  }, [syncToken, isLoaded])

  // Also sync when session changes
  useEffect(() => {
    if (isAuthReady && session) {
      syncToken()
    }
  }, [session, isAuthReady, syncToken])

  const value: AuthContextValue = {
    isAuthReady,
    isAuthenticated: isSignedIn ?? false,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
