import { Link } from 'react-router-dom'
import {
  FileText,
  Upload,
  Target,
  Sparkles,
  BarChart3,
  PenLine,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react'

const isClerkConfigured = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

// Where the primary CTAs land: sign-up when auth is on, straight into the app otherwise
const ctaHref = isClerkConfigured ? '/sign-up' : '/batches'
const signInHref = isClerkConfigured ? '/sign-in' : '/batches'

const FEATURES = [
  {
    icon: Upload,
    title: 'Batch Upload & Ranking',
    description:
      'Drop in up to 100 resumes at once. PDF, DOCX, or TXT — parsed, scored, and ranked automatically.',
  },
  {
    icon: Target,
    title: 'Role-Specific Scoring',
    description:
      'Six tech-sales role profiles, from Entry SDR to Sales Director. Every resume is judged against the bar for its role.',
  },
  {
    icon: BarChart3,
    title: 'JD Matching',
    description:
      'Paste a job description and see exactly which candidates match — skill gaps, missing keywords, and quota fit included.',
  },
  {
    icon: Sparkles,
    title: 'AI Deep Analysis',
    description:
      'Strengths, weaknesses, red flags, and suggested interview questions for every candidate, powered by Claude.',
  },
  {
    icon: PenLine,
    title: 'Resume Writing & Export',
    description:
      'Generate polished, metrics-first resumes in five template styles. Export to PDF, DOCX, TXT, or HTML.',
  },
  {
    icon: ShieldCheck,
    title: 'Private & Isolated',
    description:
      'Your batches are yours alone. Per-account data isolation, encrypted storage, and secure authentication.',
  },
]

const STEPS = [
  {
    number: '1',
    title: 'Upload a batch',
    description: 'Create a batch, pick the target sales role, and drop in your resumes.',
  },
  {
    number: '2',
    title: 'Let Polished rank them',
    description:
      'Automatic parsing, role-aware scoring across six categories, and a ranked shortlist in minutes.',
  },
  {
    number: '3',
    title: 'Place with confidence',
    description:
      'Match against JDs, run deep analysis on finalists, and export results for your client.',
  },
]

const TIERS = [
  {
    name: 'Free',
    price: '$0',
    billing: 'forever',
    highlight: false,
    features: [
      '5 batches per month',
      '50 resumes per batch',
      'Role-specific scoring',
      'Automatic ranking',
      'CSV export',
    ],
    cta: 'Start Free',
  },
  {
    name: 'Pro',
    price: '$29',
    billing: 'per month',
    highlight: true,
    features: [
      '100 batches per month',
      '500 resumes per batch',
      'JD Matching',
      'AI Deep Analysis',
      'Resume Writing & PDF/DOCX export',
      'Priority processing',
    ],
    cta: 'Start with Pro',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    billing: 'talk to us',
    highlight: false,
    features: [
      'Unlimited batches & resumes',
      'Custom scoring rules',
      'API access',
      'Dedicated support',
      'SLA guarantee',
    ],
    cta: 'Contact Sales',
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Nav */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">Polished</span>
          </div>
          <nav className="hidden sm:flex items-center gap-8 text-sm font-medium text-gray-600">
            <a href="#features" className="hover:text-gray-900 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-gray-900 transition-colors">How it works</a>
            <a href="#pricing" className="hover:text-gray-900 transition-colors">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              to={signInHref}
              className="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors"
            >
              Sign in
            </Link>
            <Link
              to={ctaHref}
              className="text-sm font-semibold text-white bg-primary-600 hover:bg-primary-700 px-4 py-2 rounded-lg transition-colors"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-50 to-white pointer-events-none" />
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 text-center">
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-primary-700 bg-primary-100 rounded-full px-3 py-1 mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            Built for tech sales recruiting
          </span>
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight">
            Rank 100 sales resumes
            <br className="hidden sm:block" />
            <span className="text-primary-600"> in minutes, not days</span>
          </h1>
          <p className="mt-6 max-w-2xl mx-auto text-lg text-gray-600">
            Polished parses, scores, and ranks tech-sales resumes against the exact role you're
            hiring for — SDR to Sales Director — then helps you match, analyze, and place the
            best candidates.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to={ctaHref}
              className="inline-flex items-center gap-2 text-base font-semibold text-white bg-primary-600 hover:bg-primary-700 px-6 py-3 rounded-lg shadow-sm transition-colors"
            >
              Start ranking free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center gap-2 text-base font-semibold text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 px-6 py-3 rounded-lg transition-colors"
            >
              See how it works
            </a>
          </div>
          <p className="mt-4 text-sm text-gray-500">Free tier included · No credit card required</p>
        </div>
      </section>

      {/* Stats strip */}
      <section className="border-y border-gray-100 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid grid-cols-2 sm:grid-cols-4 gap-8 text-center">
          {[
            ['100', 'resumes per batch'],
            ['6', 'sales role profiles'],
            ['5', 'export templates'],
            ['minutes', 'to a ranked shortlist'],
          ].map(([stat, label]) => (
            <div key={label}>
              <div className="text-3xl font-extrabold text-primary-600">{stat}</div>
              <div className="mt-1 text-sm text-gray-600">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
            Everything between "pile of PDFs" and "placed candidate"
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            One workflow from upload to placement, purpose-built for tech-sales roles.
          </p>
        </div>
        <div className="mt-16 grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="p-6 rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all"
            >
              <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                <Icon className="w-5 h-5 text-primary-600" />
              </div>
              <h3 className="mt-4 text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-gray-600 leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="bg-gray-50 border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">How it works</h2>
          </div>
          <div className="mt-16 grid sm:grid-cols-3 gap-10">
            {STEPS.map(({ number, title, description }) => (
              <div key={number} className="text-center">
                <div className="mx-auto w-12 h-12 rounded-full bg-primary-600 text-white text-xl font-bold flex items-center justify-center">
                  {number}
                </div>
                <h3 className="mt-5 text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-gray-600 leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Simple pricing</h2>
          <p className="mt-4 text-lg text-gray-600">
            Start free. Upgrade when your pipeline does.
          </p>
        </div>
        <div className="mt-16 grid sm:grid-cols-3 gap-8 items-stretch">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`flex flex-col p-8 rounded-2xl border ${
                tier.highlight
                  ? 'border-primary-600 shadow-lg ring-1 ring-primary-600'
                  : 'border-gray-200'
              }`}
            >
              {tier.highlight && (
                <span className="self-start text-xs font-semibold uppercase tracking-wide text-primary-700 bg-primary-100 rounded-full px-3 py-1 mb-4">
                  Most popular
                </span>
              )}
              <h3 className="text-lg font-semibold">{tier.name}</h3>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-4xl font-extrabold">{tier.price}</span>
                <span className="text-sm text-gray-500">{tier.billing}</span>
              </div>
              <ul className="mt-6 space-y-3 flex-1">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="w-4 h-4 text-primary-600 mt-0.5 shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link
                to={ctaHref}
                className={`mt-8 inline-flex justify-center text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors ${
                  tier.highlight
                    ? 'text-white bg-primary-600 hover:bg-primary-700'
                    : 'text-primary-700 bg-primary-50 hover:bg-primary-100'
                }`}
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary-600">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            Stop skimming. Start ranking.
          </h2>
          <p className="mt-4 text-lg text-primary-100 max-w-xl mx-auto">
            Upload your first batch and get a ranked shortlist before your coffee gets cold.
          </p>
          <Link
            to={ctaHref}
            className="mt-8 inline-flex items-center gap-2 text-base font-semibold text-primary-700 bg-white hover:bg-primary-50 px-6 py-3 rounded-lg shadow-sm transition-colors"
          >
            Get started free
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-primary-600 rounded-md flex items-center justify-center">
              <FileText className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold">Polished</span>
          </div>
          <p className="text-sm text-gray-500">
            © {new Date().getFullYear()} Polished. Resume ranking for tech sales recruiting.
          </p>
          <div className="flex items-center gap-6 text-sm text-gray-600">
            <a href="#pricing" className="hover:text-gray-900 transition-colors">Pricing</a>
            <Link to={signInHref} className="hover:text-gray-900 transition-colors">Sign in</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
