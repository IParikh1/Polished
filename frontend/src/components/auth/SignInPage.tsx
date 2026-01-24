import { SignIn } from '@clerk/clerk-react'
import { FileText } from 'lucide-react'

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="flex items-center gap-2 mb-8">
        <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
          <FileText className="w-6 h-6 text-white" />
        </div>
        <span className="text-2xl font-bold text-gray-900">Polished</span>
      </div>

      <div className="w-full max-w-md">
        <SignIn
          appearance={{
            elements: {
              rootBox: 'w-full',
              card: 'shadow-lg rounded-xl',
              headerTitle: 'text-xl font-semibold',
              headerSubtitle: 'text-gray-600',
              socialButtonsBlockButton: 'border border-gray-300 hover:bg-gray-50',
              formFieldInput: 'rounded-lg border-gray-300 focus:border-primary-500 focus:ring-primary-500',
              formButtonPrimary: 'bg-primary-600 hover:bg-primary-700',
              footerActionLink: 'text-primary-600 hover:text-primary-700',
            },
          }}
          routing="path"
          path="/sign-in"
          signUpUrl="/sign-up"
        />
      </div>

      <p className="mt-8 text-center text-sm text-gray-500">
        AI-powered resume optimization for tech sales professionals
      </p>
    </div>
  )
}
