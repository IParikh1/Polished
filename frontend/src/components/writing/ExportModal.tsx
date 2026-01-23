import { useState } from 'react'
import {
  X,
  FileText,
  FileType,
  Code,
  Download,
  Loader2,
  Check,
  AlertCircle,
} from 'lucide-react'
import clsx from 'clsx'
import { useExportResume } from '../../hooks/useResumeWriting'
import type { ResumeTemplate, DocumentFormat } from '../../api/batchClient'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  batchId?: string
  resumeId?: string
  sessionId?: string
  resumeText?: string
  template: ResumeTemplate
  resumeData?: {
    name?: string
    email?: string
    phone?: string
    location?: string
    linkedin?: string
    summary?: string
    skills?: string[]
  }
}

const formats: Array<{
  id: DocumentFormat
  label: string
  icon: typeof FileText
  description: string
}> = [
  {
    id: 'pdf',
    label: 'PDF',
    icon: FileText,
    description: 'Best for applications and printing',
  },
  {
    id: 'docx',
    label: 'Word (DOCX)',
    icon: FileType,
    description: 'Editable format for further changes',
  },
  {
    id: 'txt',
    label: 'Plain Text',
    icon: FileText,
    description: 'Simple text, good for copy-paste',
  },
  {
    id: 'html',
    label: 'HTML',
    icon: Code,
    description: 'Web format with styling',
  },
]

export default function ExportModal({
  isOpen,
  onClose,
  batchId,
  resumeId,
  sessionId,
  resumeText,
  template,
  resumeData,
}: ExportModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<DocumentFormat>('pdf')
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const exportMutation = useExportResume()

  const handleExport = async () => {
    try {
      const result = await exportMutation.mutateAsync({
        batch_id: batchId,
        resume_id: resumeId,
        session_id: sessionId,
        resume_text: resumeText,
        format: selectedFormat,
        template,
        name: resumeData?.name,
        email: resumeData?.email,
        phone: resumeData?.phone,
        location: resumeData?.location,
        linkedin: resumeData?.linkedin,
        summary: resumeData?.summary,
        skills: resumeData?.skills,
      })
      setDownloadUrl(result.download_url)
    } catch {
      // Error handled by mutation
    }
  }

  const handleDownload = () => {
    if (downloadUrl) {
      window.open(downloadUrl, '_blank')
    }
  }

  const handleClose = () => {
    setDownloadUrl(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Export Resume</h2>
          <button
            onClick={handleClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {downloadUrl ? (
            <div className="text-center py-6">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-medium text-gray-900 mb-2">
                Export Ready!
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                Your resume has been generated and is ready to download.
              </p>
              <button
                onClick={handleDownload}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download {selectedFormat.toUpperCase()}
              </button>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                Choose a format to export your optimized resume
              </p>

              <div className="space-y-2">
                {formats.map((format) => {
                  const Icon = format.icon
                  const isSelected = selectedFormat === format.id

                  return (
                    <button
                      key={format.id}
                      onClick={() => setSelectedFormat(format.id)}
                      disabled={exportMutation.isPending}
                      className={clsx(
                        'w-full flex items-center gap-3 p-3 rounded-lg border-2 transition-all text-left',
                        exportMutation.isPending && 'opacity-50 cursor-not-allowed',
                        isSelected
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <div
                        className={clsx(
                          'p-2 rounded-lg',
                          isSelected ? 'bg-primary-100' : 'bg-gray-100'
                        )}
                      >
                        <Icon
                          className={clsx(
                            'w-5 h-5',
                            isSelected ? 'text-primary-600' : 'text-gray-500'
                          )}
                        />
                      </div>
                      <div className="flex-1">
                        <span
                          className={clsx(
                            'font-medium text-sm block',
                            isSelected ? 'text-primary-900' : 'text-gray-900'
                          )}
                        >
                          {format.label}
                        </span>
                        <span
                          className={clsx(
                            'text-xs',
                            isSelected ? 'text-primary-700' : 'text-gray-500'
                          )}
                        >
                          {format.description}
                        </span>
                      </div>
                      <div
                        className={clsx(
                          'w-4 h-4 rounded-full border-2',
                          isSelected
                            ? 'border-primary-500 bg-primary-500'
                            : 'border-gray-300'
                        )}
                      >
                        {isSelected && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>

              {exportMutation.isError && (
                <div className="mt-4 flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>
                    {exportMutation.error?.message || 'Failed to export resume'}
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!downloadUrl && (
          <div className="flex gap-3 p-4 border-t border-gray-200">
            <button
              onClick={handleClose}
              className="btn-secondary flex-1"
              disabled={exportMutation.isPending}
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={exportMutation.isPending}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {exportMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Export
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
