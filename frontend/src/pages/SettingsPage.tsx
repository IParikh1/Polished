import { useState } from 'react'
import {
  Settings,
  Key,
  Bell,
  Palette,
  Shield,
  User,
  CreditCard,
  Zap,
  Check,
  X,
  Eye,
  EyeOff,
  Save,
  Loader2,
  ExternalLink,
  AlertCircle
} from 'lucide-react'
import clsx from 'clsx'

interface SettingsSectionProps {
  title: string
  description: string
  icon: React.ElementType
  children: React.ReactNode
}

function SettingsSection({ title, description, icon: Icon, children }: SettingsSectionProps) {
  return (
    <div className="card p-6">
      <div className="flex items-start gap-4 mb-6">
        <div className="p-2 bg-primary-50 rounded-lg">
          <Icon className="w-5 h-5 text-primary-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
      {children}
    </div>
  )
}

interface ToggleProps {
  enabled: boolean
  onToggle: () => void
  label: string
  description?: string
}

function Toggle({ enabled, onToggle, label, description }: ToggleProps) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
      <div>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {description && <p className="text-xs text-gray-500">{description}</p>}
      </div>
      <button
        onClick={onToggle}
        className={clsx(
          'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
          enabled ? 'bg-primary-600' : 'bg-gray-200'
        )}
      >
        <span
          className={clsx(
            'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
            enabled ? 'translate-x-5' : 'translate-x-0'
          )}
        />
      </button>
    </div>
  )
}

export default function SettingsPage() {
  // API Settings
  const [anthropicKey, setAnthropicKey] = useState('')
  const [showAnthropicKey, setShowAnthropicKey] = useState(false)
  const [apiSaving, setApiSaving] = useState(false)
  const [apiSaved, setApiSaved] = useState(false)

  // Notification Settings
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [batchCompletionNotify, setBatchCompletionNotify] = useState(true)
  const [weeklyReports, setWeeklyReports] = useState(false)
  const [errorAlerts, setErrorAlerts] = useState(true)

  // Appearance Settings
  const [darkMode, setDarkMode] = useState(false)
  const [compactView, setCompactView] = useState(false)
  const [showScoreColors, setShowScoreColors] = useState(true)

  // Processing Settings
  const [autoProcess, setAutoProcess] = useState(false)
  const [deepAnalysisDefault, setDeepAnalysisDefault] = useState(false)
  const [jdMatchingDefault, setJdMatchingDefault] = useState(true)

  // Export Settings
  const [defaultExportFormat, setDefaultExportFormat] = useState<'pdf' | 'docx' | 'csv'>('pdf')
  const [includeScoresInExport, setIncludeScoresInExport] = useState(true)
  const [includeAnalysisInExport, setIncludeAnalysisInExport] = useState(false)

  const handleSaveApiKey = async () => {
    setApiSaving(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setApiSaving(false)
    setApiSaved(true)
    setTimeout(() => setApiSaved(false), 3000)
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your account and application preferences</p>
      </div>

      {/* API Configuration */}
      <SettingsSection
        title="API Configuration"
        description="Configure your AI service API keys for enhanced features"
        icon={Key}
      >
        <div className="space-y-4">
          <div>
            <label className="label">Anthropic API Key</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showAnthropicKey ? 'text' : 'password'}
                  value={anthropicKey}
                  onChange={(e) => setAnthropicKey(e.target.value)}
                  placeholder="sk-ant-api03-..."
                  className="input pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showAnthropicKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <button
                onClick={handleSaveApiKey}
                disabled={apiSaving || !anthropicKey}
                className="btn-primary gap-2"
              >
                {apiSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : apiSaved ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {apiSaved ? 'Saved' : 'Save'}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Required for AI-powered resume writing and deep analysis features.{' '}
              <a
                href="https://console.anthropic.com/account/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline inline-flex items-center gap-1"
              >
                Get your API key <ExternalLink className="w-3 h-3" />
              </a>
            </p>
          </div>

          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800">API Key Security</p>
                <p className="text-xs text-amber-700 mt-1">
                  Your API key is stored securely and encrypted. It is only used for processing requests
                  and is never shared with third parties.
                </p>
              </div>
            </div>
          </div>
        </div>
      </SettingsSection>

      {/* Processing Settings */}
      <SettingsSection
        title="Processing Defaults"
        description="Configure default settings for batch processing"
        icon={Zap}
      >
        <div className="space-y-1">
          <Toggle
            enabled={autoProcess}
            onToggle={() => setAutoProcess(!autoProcess)}
            label="Auto-process batches"
            description="Automatically start processing when uploads complete"
          />
          <Toggle
            enabled={deepAnalysisDefault}
            onToggle={() => setDeepAnalysisDefault(!deepAnalysisDefault)}
            label="Enable deep analysis by default"
            description="Run AI-powered deep analysis on all resumes (uses API credits)"
          />
          <Toggle
            enabled={jdMatchingDefault}
            onToggle={() => setJdMatchingDefault(!jdMatchingDefault)}
            label="Enable JD matching by default"
            description="Compare resumes against job descriptions when provided"
          />
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100">
          <label className="label">Default Target Role</label>
          <select className="input max-w-xs">
            <option value="">No default (ask each time)</option>
            <option value="entry_sdr">Entry-Level SDR</option>
            <option value="sdr">SDR</option>
            <option value="account_executive">Account Executive</option>
            <option value="senior_ae">Senior/Enterprise AE</option>
            <option value="account_manager">Account Manager</option>
            <option value="sales_manager">Sales Manager/Director</option>
          </select>
        </div>
      </SettingsSection>

      {/* Export Settings */}
      <SettingsSection
        title="Export Settings"
        description="Configure default export options"
        icon={Settings}
      >
        <div className="space-y-4">
          <div>
            <label className="label">Default Export Format</label>
            <div className="flex gap-3">
              {(['pdf', 'docx', 'csv'] as const).map((format) => (
                <button
                  key={format}
                  onClick={() => setDefaultExportFormat(format)}
                  className={clsx(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    defaultExportFormat === format
                      ? 'bg-primary-100 text-primary-700 border-2 border-primary-300'
                      : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                  )}
                >
                  {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <Toggle
              enabled={includeScoresInExport}
              onToggle={() => setIncludeScoresInExport(!includeScoresInExport)}
              label="Include scores in export"
              description="Add score breakdown to exported data"
            />
            <Toggle
              enabled={includeAnalysisInExport}
              onToggle={() => setIncludeAnalysisInExport(!includeAnalysisInExport)}
              label="Include analysis in export"
              description="Add AI analysis to exported data (larger file size)"
            />
          </div>
        </div>
      </SettingsSection>

      {/* Notifications */}
      <SettingsSection
        title="Notifications"
        description="Manage how you receive updates and alerts"
        icon={Bell}
      >
        <div className="space-y-1">
          <Toggle
            enabled={emailNotifications}
            onToggle={() => setEmailNotifications(!emailNotifications)}
            label="Email notifications"
            description="Receive updates via email"
          />
          <Toggle
            enabled={batchCompletionNotify}
            onToggle={() => setBatchCompletionNotify(!batchCompletionNotify)}
            label="Batch completion alerts"
            description="Get notified when batch processing completes"
          />
          <Toggle
            enabled={weeklyReports}
            onToggle={() => setWeeklyReports(!weeklyReports)}
            label="Weekly summary reports"
            description="Receive weekly analytics digest"
          />
          <Toggle
            enabled={errorAlerts}
            onToggle={() => setErrorAlerts(!errorAlerts)}
            label="Error alerts"
            description="Get notified immediately on processing errors"
          />
        </div>
      </SettingsSection>

      {/* Appearance */}
      <SettingsSection
        title="Appearance"
        description="Customize how the application looks"
        icon={Palette}
      >
        <div className="space-y-1">
          <Toggle
            enabled={darkMode}
            onToggle={() => setDarkMode(!darkMode)}
            label="Dark mode"
            description="Use dark theme (coming soon)"
          />
          <Toggle
            enabled={compactView}
            onToggle={() => setCompactView(!compactView)}
            label="Compact view"
            description="Reduce spacing for more content on screen"
          />
          <Toggle
            enabled={showScoreColors}
            onToggle={() => setShowScoreColors(!showScoreColors)}
            label="Color-coded scores"
            description="Show green/yellow/red based on score value"
          />
        </div>
      </SettingsSection>

      {/* Account & Subscription */}
      <SettingsSection
        title="Subscription"
        description="Manage your subscription and billing"
        icon={CreditCard}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-primary-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Current Plan</p>
              <p className="text-sm text-gray-600">Free Trial</p>
            </div>
            <span className="badge badge-primary">Active</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Free</h4>
              <p className="text-2xl font-bold text-gray-900 mb-2">$0<span className="text-sm font-normal text-gray-500">/mo</span></p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> 10 resumes/month</li>
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> Basic scoring</li>
                <li className="flex items-center gap-2"><X className="w-4 h-4 text-gray-300" /> Deep analysis</li>
                <li className="flex items-center gap-2"><X className="w-4 h-4 text-gray-300" /> Resume writing</li>
              </ul>
            </div>

            <div className="p-4 border-2 border-primary-500 rounded-lg relative">
              <span className="absolute -top-2 left-4 px-2 bg-primary-500 text-white text-xs font-medium rounded">Popular</span>
              <h4 className="font-medium text-gray-900 mb-2">Pro</h4>
              <p className="text-2xl font-bold text-gray-900 mb-2">$49<span className="text-sm font-normal text-gray-500">/mo</span></p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> 500 resumes/month</li>
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> JD matching</li>
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> Deep analysis</li>
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> Resume writing</li>
              </ul>
              <button className="btn-primary w-full mt-4">Upgrade</button>
            </div>

            <div className="p-4 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Enterprise</h4>
              <p className="text-2xl font-bold text-gray-900 mb-2">Custom</p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> Unlimited resumes</li>
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> API access</li>
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> Custom integrations</li>
                <li className="flex items-center gap-2"><Check className="w-4 h-4 text-success-500" /> Dedicated support</li>
              </ul>
              <button className="btn-secondary w-full mt-4">Contact Sales</button>
            </div>
          </div>
        </div>
      </SettingsSection>

      {/* Security */}
      <SettingsSection
        title="Security"
        description="Manage your account security settings"
        icon={Shield}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium text-gray-900">Two-Factor Authentication</p>
              <p className="text-xs text-gray-500">Add an extra layer of security to your account</p>
            </div>
            <button className="btn-secondary text-sm">Enable 2FA</button>
          </div>
          <div className="flex items-center justify-between py-3 border-t border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-900">Active Sessions</p>
              <p className="text-xs text-gray-500">Manage devices where you are logged in</p>
            </div>
            <button className="btn-secondary text-sm">View Sessions</button>
          </div>
          <div className="flex items-center justify-between py-3 border-t border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-900">Password</p>
              <p className="text-xs text-gray-500">Last changed 30 days ago</p>
            </div>
            <button className="btn-secondary text-sm">Change Password</button>
          </div>
        </div>
      </SettingsSection>

      {/* Account */}
      <SettingsSection
        title="Account"
        description="Manage your account information"
        icon={User}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Name</label>
              <input type="text" placeholder="Your Name" className="input" />
            </div>
            <div>
              <label className="label">Email</label>
              <input type="email" placeholder="your@email.com" className="input" />
            </div>
          </div>
          <div>
            <label className="label">Company</label>
            <input type="text" placeholder="Company Name (optional)" className="input" />
          </div>
          <div className="flex justify-end">
            <button className="btn-primary gap-2">
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-sm font-medium text-danger-600 mb-2">Danger Zone</h4>
          <div className="flex items-center justify-between p-4 border border-danger-200 rounded-lg bg-danger-50">
            <div>
              <p className="text-sm font-medium text-gray-900">Delete Account</p>
              <p className="text-xs text-gray-500">Permanently delete your account and all data</p>
            </div>
            <button className="btn-danger text-sm">Delete Account</button>
          </div>
        </div>
      </SettingsSection>
    </div>
  )
}
