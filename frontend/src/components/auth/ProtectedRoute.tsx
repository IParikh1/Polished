import { useAuth, RedirectToSignIn } from '@clerk/clerk-react'
import { ReactNode } from 'react'
import { AuthProvider, useAuthContext } from '../../contexts/AuthContext'

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
  const { isAuthReady } = useAuthContext()

  if (!isAuthReady) {
    return <LoadingSpinner />
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
