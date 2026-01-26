import {
  HelpCircle,
  Upload,
  Play,
  BarChart3,
  FileText,
  Target,
  Sparkles,
  Download,
  ChevronRight,
  CheckCircle2,
  Zap,
} from 'lucide-react'

interface StepProps {
  number: number
  title: string
  description: string
  icon: React.ElementType
}

function Step({ number, title, description, icon: Icon }: StepProps) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold">
          {number}
        </div>
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <Icon className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">{title}</h3>
        </div>
        <p className="text-gray-600">{description}</p>
      </div>
    </div>
  )
}

interface FeatureCardProps {
  title: string
  description: string
  icon: React.ElementType
  premium?: boolean
}

function FeatureCard({ title, description, icon: Icon, premium }: FeatureCardProps) {
  return (
    <div className="card p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${premium ? 'bg-amber-100' : 'bg-primary-100'}`}>
          <Icon className={`w-5 h-5 ${premium ? 'text-amber-600' : 'text-primary-600'}`} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900">{title}</h3>
            {premium && (
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">Pro</span>
            )}
          </div>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        </div>
      </div>
    </div>
  )
}

export default function HelpPage() {
  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <HelpCircle className="w-8 h-8 text-primary-600" />
          <h1 className="text-2xl font-bold text-gray-900">Help & Documentation</h1>
        </div>
        <p className="text-gray-600">
          Learn how to use Polished to score, rank, and optimize tech sales resumes
        </p>
      </div>

      {/* Quick Start Guide */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Quick Start Guide</h2>
        <div className="space-y-6">
          <Step
            number={1}
            title="Create a Batch"
            description="Click 'New Batch' to create a new batch. Give it a name and optionally paste a job description to enable JD matching."
            icon={FileText}
          />
          <div className="ml-14 border-l-2 border-gray-200 h-4" />
          <Step
            number={2}
            title="Upload Resumes"
            description="Drag and drop resume files (PDF, DOCX, DOC, TXT, RTF) into the upload area. Select a target sales role for optimized scoring, or enable 'Per-file roles' to assign different roles to each resume individually."
            icon={Upload}
          />
          <div className="ml-14 border-l-2 border-gray-200 h-4" />
          <Step
            number={3}
            title="Process or View Rankings"
            description="Click 'Start Processing' to run AI analysis on all resumes, or click 'View Rankings' to see basic scoring immediately without AI processing. You can always process later."
            icon={Play}
          />
          <div className="ml-14 border-l-2 border-gray-200 h-4" />
          <Step
            number={4}
            title="Review Rankings"
            description="View ranked resumes sorted by score. Click on any resume to see detailed analysis, score breakdown, and JD match results."
            icon={BarChart3}
          />
          <div className="ml-14 border-l-2 border-gray-200 h-4" />
          <Step
            number={5}
            title="Export Results"
            description="Export your rankings to CSV or JSON format. Choose which data to include: scores, extracted data, and JD match results. You can also reopen completed batches to add more resumes."
            icon={Download}
          />
        </div>
      </div>

      {/* Target Sales Roles */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Target Sales Roles</h2>
        <p className="text-gray-600 mb-4">
          Polished is optimized for tech sales positions. Select the appropriate role for accurate scoring:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <ChevronRight className="w-4 h-4 text-primary-500" />
            <div>
              <p className="font-medium text-gray-900">Entry-Level SDR</p>
              <p className="text-xs text-gray-500">0-1 years experience</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <ChevronRight className="w-4 h-4 text-primary-500" />
            <div>
              <p className="font-medium text-gray-900">SDR/BDR</p>
              <p className="text-xs text-gray-500">1-3 years experience</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <ChevronRight className="w-4 h-4 text-primary-500" />
            <div>
              <p className="font-medium text-gray-900">Account Executive</p>
              <p className="text-xs text-gray-500">2-5 years experience</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <ChevronRight className="w-4 h-4 text-primary-500" />
            <div>
              <p className="font-medium text-gray-900">Senior/Enterprise AE</p>
              <p className="text-xs text-gray-500">5+ years experience</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <ChevronRight className="w-4 h-4 text-primary-500" />
            <div>
              <p className="font-medium text-gray-900">Account Manager</p>
              <p className="text-xs text-gray-500">2+ years experience</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <ChevronRight className="w-4 h-4 text-primary-500" />
            <div>
              <p className="font-medium text-gray-900">Sales Manager/Director</p>
              <p className="text-xs text-gray-500">5+ years experience</p>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FeatureCard
            title="Resume Scoring"
            description="Automatic scoring based on experience, skills, education, formatting, and keyword matches."
            icon={BarChart3}
          />
          <FeatureCard
            title="Batch Processing"
            description="Upload and process up to 100 resumes at once. Perfect for high-volume recruiting."
            icon={Zap}
          />
          <FeatureCard
            title="JD Matching"
            description="Match resumes against job descriptions to find the best candidates for specific roles."
            icon={Target}
            premium
          />
          <FeatureCard
            title="Deep Analysis"
            description="AI-powered analysis providing strengths, weaknesses, and interview recommendations."
            icon={Sparkles}
            premium
          />
          <FeatureCard
            title="Resume Writing"
            description="Generate optimized resumes tailored for specific sales roles with AI assistance."
            icon={FileText}
            premium
          />
          <FeatureCard
            title="Export Options"
            description="Export rankings to CSV, JSON, PDF, or DOCX formats for sharing and reporting."
            icon={Download}
          />
        </div>
      </div>

      {/* Advanced Features */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Advanced Features</h2>
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-primary-500" />
              Per-File Role Assignment
            </h3>
            <p className="text-sm text-gray-600 mt-1 ml-6">
              When uploading resumes, click "Per-file roles" to assign different target roles to each resume individually.
              This is useful when processing candidates for multiple positions in one batch. Each resume will be scored
              against its assigned role's criteria.
            </p>
          </div>
          <div className="border-t border-gray-100 pt-4">
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-primary-500" />
              View Rankings Without Processing
            </h3>
            <p className="text-sm text-gray-600 mt-1 ml-6">
              Click "View Rankings" to see basic scores immediately without running AI processing.
              This gives you quick results based on keyword matching and formatting. You can always
              run full AI processing later for deeper analysis.
            </p>
          </div>
          <div className="border-t border-gray-100 pt-4">
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-primary-500" />
              Reopen Completed Batches
            </h3>
            <p className="text-sm text-gray-600 mt-1 ml-6">
              Need to add more resumes after a batch is complete? Click "Reopen" to set the batch
              back to pending status, then upload additional resumes. Process again when ready.
            </p>
          </div>
          <div className="border-t border-gray-100 pt-4">
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-primary-500" />
              Export Options
            </h3>
            <p className="text-sm text-gray-600 mt-1 ml-6">
              When exporting, choose exactly what data to include: scoring details (category breakdowns),
              extracted data (contact info, skills, experience), and JD match results. Export to CSV for
              spreadsheets or JSON for developers.
            </p>
          </div>
        </div>
      </div>

      {/* Scoring Breakdown */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">How Scoring Works</h2>
        <p className="text-gray-600 mb-4">
          Each resume is scored on a 0-100 scale using our tech sales-optimized algorithm based on 2025-2026 recruiter priorities:
        </p>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg border border-amber-200">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-amber-600" />
              <span className="font-medium text-gray-900">Achievements</span>
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">18%</span>
            </div>
            <span className="text-sm text-gray-600">Quota %, revenue $, deals closed, rankings</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success-500" />
              <span className="font-medium text-gray-900">Experience</span>
              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">20%</span>
            </div>
            <span className="text-sm text-gray-600">Years and relevance of sales work history</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success-500" />
              <span className="font-medium text-gray-900">Skills</span>
              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">20%</span>
            </div>
            <span className="text-sm text-gray-600">CRMs, sales tools, methodologies (MEDDIC, etc.)</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success-500" />
              <span className="font-medium text-gray-900">Keywords</span>
              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">10%</span>
            </div>
            <span className="text-sm text-gray-600">Industry terms and role-specific keywords</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success-500" />
              <span className="font-medium text-gray-900">Career Progression</span>
              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">9%</span>
            </div>
            <span className="text-sm text-gray-600">SDR → AE → Senior AE growth trajectory</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success-500" />
              <span className="font-medium text-gray-900">Certifications</span>
              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">8%</span>
            </div>
            <span className="text-sm text-gray-600">Salesforce, HubSpot, MEDDIC certifications</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success-500" />
              <span className="font-medium text-gray-900">Formatting</span>
              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">8%</span>
            </div>
            <span className="text-sm text-gray-600">Structure, readability, and ATS compatibility</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success-500" />
              <span className="font-medium text-gray-900">Education</span>
              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">5%</span>
            </div>
            <span className="text-sm text-gray-600">Degrees (less weighted for sales roles)</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success-500" />
              <span className="font-medium text-gray-900">Contact Info</span>
              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">2%</span>
            </div>
            <span className="text-sm text-gray-600">Email, phone, LinkedIn presence</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-4">
          Weights are optimized for tech sales recruiting based on research from Resume Worded, Enhancv, and industry benchmarks.
        </p>
      </div>

      {/* Score Legend */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Score Legend</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-success-50 rounded-lg border border-success-200">
            <p className="text-2xl font-bold text-success-600">80-100</p>
            <p className="text-sm text-success-700">Excellent</p>
          </div>
          <div className="text-center p-4 bg-primary-50 rounded-lg border border-primary-200">
            <p className="text-2xl font-bold text-primary-600">60-79</p>
            <p className="text-sm text-primary-700">Good</p>
          </div>
          <div className="text-center p-4 bg-amber-50 rounded-lg border border-amber-200">
            <p className="text-2xl font-bold text-amber-600">40-59</p>
            <p className="text-sm text-amber-700">Fair</p>
          </div>
          <div className="text-center p-4 bg-danger-50 rounded-lg border border-danger-200">
            <p className="text-2xl font-bold text-danger-600">0-39</p>
            <p className="text-sm text-danger-700">Needs Work</p>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Frequently Asked Questions</h2>
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-900">What file formats are supported?</h3>
            <p className="text-sm text-gray-600 mt-1">
              PDF, DOCX, DOC, TXT, and RTF files are supported. PDF is recommended for best results.
            </p>
          </div>
          <div className="border-t border-gray-100 pt-4">
            <h3 className="font-medium text-gray-900">How many resumes can I upload at once?</h3>
            <p className="text-sm text-gray-600 mt-1">
              You can upload up to 100 resumes per batch. For larger volumes, create multiple batches.
            </p>
          </div>
          <div className="border-t border-gray-100 pt-4">
            <h3 className="font-medium text-gray-900">How long does processing take?</h3>
            <p className="text-sm text-gray-600 mt-1">
              Processing typically takes 1-2 seconds per resume. A batch of 50 resumes completes in about 1-2 minutes.
            </p>
          </div>
          <div className="border-t border-gray-100 pt-4">
            <h3 className="font-medium text-gray-900">What is JD Matching?</h3>
            <p className="text-sm text-gray-600 mt-1">
              JD Matching compares each resume against a job description to calculate fit scores and identify skill gaps.
            </p>
          </div>
          <div className="border-t border-gray-100 pt-4">
            <h3 className="font-medium text-gray-900">How do I access premium features?</h3>
            <p className="text-sm text-gray-600 mt-1">
              Premium features like Deep Analysis and Resume Writing are available on Pro and Enterprise plans.
              Visit Settings to upgrade your plan.
            </p>
          </div>
        </div>
      </div>

      {/* Contact */}
      <div className="card p-6 bg-primary-50 border-primary-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Need More Help?</h2>
        <p className="text-gray-600">
          Contact our support team at{' '}
          <a href="mailto:support@getpolished.ai" className="text-primary-600 hover:underline">
            support@getpolished.ai
          </a>
        </p>
      </div>
    </div>
  )
}
