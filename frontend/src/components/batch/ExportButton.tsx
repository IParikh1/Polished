import { useState } from 'react'
import { Download, FileJson, FileSpreadsheet, X, Loader2, CheckCircle2 } from 'lucide-react'
import { useExportBatch } from '../../hooks/useRankings'
import clsx from 'clsx'

interface ExportButtonProps {
  batchId: string
  hasJobDescription?: boolean
}

export default function ExportButton({ batchId, hasJobDescription = false }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [format, setFormat] = useState<'json' | 'csv'>('csv')
  const [includeScores, setIncludeScores] = useState(true)
  const [includeExtractedData, setIncludeExtractedData] = useState(false)
  const [includeJdMatch, setIncludeJdMatch] = useState(false)

  const exportMutation = useExportBatch()

  const handleExport = async () => {
    try {
      const result = await exportMutation.mutateAsync({
        batchId,
        options: {
          format,
          include_scores: includeScores,
          include_extracted_data: includeExtractedData,
          include_jd_match: includeJdMatch,
        },
      })

      // Open download URL in new tab
      window.open(result.download_url, '_blank')
      setIsOpen(false)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  return (
    <>
      <button onClick={() => setIsOpen(true)} className="btn-secondary gap-2">
        <Download className="w-4 h-4" />
        Export
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md p-6 bg-white rounded-xl shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Export Batch Results</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Format Selection */}
              <div>
                <label className="label">Export Format</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setFormat('csv')}
                    className={`p-4 rounded-lg border-2 transition-colors ${
                      format === 'csv'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <FileSpreadsheet
                      className={`w-6 h-6 mx-auto mb-2 ${
                        format === 'csv' ? 'text-primary-600' : 'text-gray-400'
                      }`}
                    />
                    <div
                      className={`font-medium ${format === 'csv' ? 'text-primary-700' : 'text-gray-700'}`}
                    >
                      CSV
                    </div>
                    <div className="text-xs text-gray-500">For spreadsheets</div>
                  </button>
                  <button
                    onClick={() => setFormat('json')}
                    className={`p-4 rounded-lg border-2 transition-colors ${
                      format === 'json'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <FileJson
                      className={`w-6 h-6 mx-auto mb-2 ${
                        format === 'json' ? 'text-primary-600' : 'text-gray-400'
                      }`}
                    />
                    <div
                      className={`font-medium ${format === 'json' ? 'text-primary-700' : 'text-gray-700'}`}
                    >
                      JSON
                    </div>
                    <div className="text-xs text-gray-500">For developers</div>
                  </button>
                </div>
              </div>

              {/* Options */}
              <div>
                <label className="label">Include Data</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeScores}
                      onChange={(e) => setIncludeScores(e.target.checked)}
                      className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                    />
                    <div>
                      <div className="font-medium text-gray-900">Scoring Details</div>
                      <div className="text-sm text-gray-500">
                        Category scores and overall ranking
                      </div>
                    </div>
                  </label>
                  <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeExtractedData}
                      onChange={(e) => setIncludeExtractedData(e.target.checked)}
                      className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                    />
                    <div>
                      <div className="font-medium text-gray-900">Extracted Data</div>
                      <div className="text-sm text-gray-500">
                        Contact info, skills, experience
                      </div>
                    </div>
                  </label>
                  <label
                    className={clsx(
                      'flex items-center gap-3 p-3 rounded-lg border border-gray-200',
                      hasJobDescription
                        ? 'hover:bg-gray-50 cursor-pointer'
                        : 'opacity-50 cursor-not-allowed bg-gray-50'
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={includeJdMatch}
                      onChange={(e) => setIncludeJdMatch(e.target.checked)}
                      disabled={!hasJobDescription}
                      className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500 disabled:opacity-50"
                    />
                    <div>
                      <div className={clsx('font-medium', hasJobDescription ? 'text-gray-900' : 'text-gray-400')}>
                        JD Matching
                      </div>
                      <div className="text-sm text-gray-500">
                        {hasJobDescription
                          ? 'Match scores and skill gaps'
                          : 'No job description provided for this batch'}
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              {/* Export Button */}
              <button
                onClick={handleExport}
                disabled={exportMutation.isPending}
                className="w-full btn-primary gap-2"
              >
                {exportMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : exportMutation.isSuccess ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    Exported!
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Export {format.toUpperCase()}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
