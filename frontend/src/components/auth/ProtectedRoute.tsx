import { useAuth, RedirectToSignIn } from '@clerk/clerk-react'
import { ReactNode } from 'react'

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
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  // Redirect to sign-in if not authenticated
  if (!isSignedIn) {
    return <RedirectToSignIn />
  }

  return <>{children}</>
}
