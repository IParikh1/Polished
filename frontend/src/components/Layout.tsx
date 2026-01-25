import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { FileText, MessageSquare, BarChart3, Settings, Menu, X, Sparkles, HelpCircle, Crown, CreditCard, User } from 'lucide-react'
import { useState } from 'react'
import { UserButton } from '@clerk/clerk-react'
import clsx from 'clsx'
import { useSubscription, useCreatePortal } from '../hooks/useSubscription'

// Check if Clerk is configured
const isClerkConfigured = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

const navigation = [
  { name: 'Batches', href: '/batches', icon: FileText },
  { name: 'Writing', href: '/writing', icon: Sparkles },
  { name: 'Consulting', href: '/consulting', icon: MessageSquare },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Help', href: '/help', icon: HelpCircle },
]

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Get subscription status
  const { data: subscription, isLoading: subLoading } = useSubscription()
  const createPortal = useCreatePortal()
  const isPro = subscription?.is_pro ?? false

  const handleManageSubscription = async () => {
    if (isPro && subscription?.manage_url) {
      try {
        const result = await createPortal.mutateAsync(window.location.href)
        window.location.href = result.portal_url
      } catch (error) {
        console.error('Failed to create portal session:', error)
        navigate('/settings')
      }
    } else {
      navigate('/pricing')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div
        className={clsx(
          'fixed inset-0 z-50 lg:hidden',
          sidebarOpen ? 'block' : 'hidden'
        )}
      >
        <div
          className="fixed inset-0 bg-gray-900/50"
          onClick={() => setSidebarOpen(false)}
        />
        <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl">
          <div className="flex items-center justify-between h-16 px-4 border-b">
            <span className="text-xl font-bold text-primary-600">Polished</span>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-lg hover:bg-gray-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <nav className="p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.href)
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={clsx(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-1 bg-white border-r border-gray-200">
          <div className="flex items-center h-16 px-6 border-b">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">Polished</span>
            </Link>
          </div>
          <nav className="flex-1 p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.href)
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
          <div className="p-4 border-t">
            {subLoading ? (
              <div className="p-4 bg-gray-100 rounded-lg animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
              </div>
            ) : isPro ? (
              <div className="p-4 bg-gradient-to-r from-amber-400 to-amber-500 rounded-lg text-white">
                <div className="flex items-center gap-2 mb-1">
                  <Crown className="w-4 h-4" />
                  <h4 className="font-semibold">Pro Plan</h4>
                </div>
                <p className="text-sm text-amber-100 mb-3">
                  All premium features unlocked
                </p>
                <button
                  onClick={handleManageSubscription}
                  disabled={createPortal.isPending}
                  className="w-full py-2 bg-white text-amber-600 rounded-lg text-sm font-medium hover:bg-amber-50 transition-colors flex items-center justify-center gap-2"
                >
                  <CreditCard className="w-4 h-4" />
                  {createPortal.isPending ? 'Loading...' : 'Manage Subscription'}
                </button>
              </div>
            ) : (
              <div className="p-4 bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg text-white">
                <h4 className="font-semibold mb-1">Upgrade to Pro</h4>
                <p className="text-sm text-primary-100 mb-3">
                  Unlock JD matching, deep analysis, and more.
                </p>
                <Link
                  to="/pricing"
                  className="block w-full py-2 bg-white text-primary-600 rounded-lg text-sm font-medium hover:bg-primary-50 transition-colors text-center"
                >
                  View Plans
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-40 flex items-center h-16 px-4 bg-white border-b border-gray-200 lg:px-8">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 -ml-2 rounded-lg hover:bg-gray-100 lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-4">
            {isPro && (
              <span className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded-full bg-gradient-to-r from-amber-400 to-amber-500 text-white text-xs font-medium">
                <Crown className="w-3 h-3" />
                Pro
              </span>
            )}
            <Link to="/help" className="btn-secondary">
              <span className="hidden sm:inline">Documentation</span>
            </Link>
            {isClerkConfigured ? (
              <UserButton
                afterSignOutUrl="/sign-in"
                appearance={{
                  elements: {
                    avatarBox: 'w-9 h-9',
                  },
                }}
              />
            ) : (
              <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center">
                <User className="w-5 h-5 text-gray-500" />
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
