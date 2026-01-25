import { useAuth, useClerk, RedirectToSignIn } from '@clerk/clerk-react'
import { ReactNode } from 'react'
import { AuthProvider, useAuthContext } from '../../contexts/AuthContext'
import { RefreshCw, LogOut } from 'lucide-react'

interface ProtectedRouteProps {
  children: ReactNode
}

// Check if Clerk is configured
const isClerkConfigured = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  // If Clerk isn't configured, bypass auth and render children directly
  if (!isClerkConfigured) {
    return <>{children}</>
  }

  return <ProtectedRouteWithAuth>{children}</ProtectedRouteWithAuth>
}

// Inner component that uses Clerk hooks (only used when Clerk is configured)
function ProtectedRouteWithAuth({ children }: ProtectedRouteProps) {
  const { isLoaded, isSignedIn } = useAuth()

  // Show loading state while Clerk is initializing
  if (!isLoaded) {
    return <LoadingSpinner />
  }

  // Redirect to sign-in if not authenticated
  if (!isSignedIn) {
    return <RedirectToSignIn />
  }

  // Wrap with AuthProvider to manage token sync
  return (
    <AuthProvider>
      <AuthGuard>{children}</AuthGuard>
    </AuthProvider>
  )
}

// Waits for auth token to be ready before rendering children
function AuthGuard({ children }: ProtectedRouteProps) {
  const { isAuthReady, authError } = useAuthContext()
  const { signOut } = useClerk()

  if (!isAuthReady) {
    return <LoadingSpinner />
  }

  // Show error banner if auth had issues, but still render the app
  if (authError) {
    return (
      <>
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 flex items-center justify-between">
          <span className="text-sm text-amber-800">{authError}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-1 px-3 py-1 text-sm font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-md transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
            <button
              onClick={() => signOut({ redirectUrl: '/sign-in' })}
              className="inline-flex items-center gap-1 px-3 py-1 text-sm font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-md transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
          </div>
        </div>
        {children}
      </>
    )
  }

  return <>{children}</>
}

function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )
}
