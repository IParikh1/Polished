import React, { useState, useMemo, useRef } from 'react'
import { Download, FileText, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RefreshCw, Eye } from 'lucide-react'
import { Document, Page, pdfjs } from 'react-pdf'
import ReactMarkdown from 'react-markdown'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import './ResumePreview.css'

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

interface Props {
  pdfFile: File | null
  resumeContent?: string
  isUpdating?: boolean
}

type ViewMode = 'original' | 'improved'

function ResumePreview({ pdfFile, resumeContent, isUpdating }: Props) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('original')
  const [isDownloading, setIsDownloading] = useState<boolean>(false)
  const improvedContentRef = useRef<HTMLDivElement>(null)

  // Auto-switch to improved view when new content arrives
  React.useEffect(() => {
    if (resumeContent) {
      setViewMode('improved')
    }
  }, [resumeContent])

  // Create a URL for the original PDF file
  const originalPdfUrl = useMemo(() => {
    if (pdfFile) {
      return URL.createObjectURL(pdfFile)
    }
    return null
  }, [pdfFile])

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setIsLoading(false)
    setError(null)
  }

  const onDocumentLoadError = (err: Error) => {
    console.error('PDF load error:', err)
    setError('Failed to load PDF preview')
    setIsLoading(false)
  }

  const goToPrevPage = () => setPageNumber(prev => Math.max(prev - 1, 1))
  const goToNextPage = () => setPageNumber(prev => Math.min(prev + 1, numPages))
  const zoomIn = () => setScale(prev => Math.min(prev + 0.2, 2.0))
  const zoomOut = () => setScale(prev => Math.max(prev - 0.2, 0.5))

  const handleDownload = async () => {
    if (viewMode === 'improved' && resumeContent && improvedContentRef.current) {
      // Generate and download PDF from improved content
      setIsDownloading(true)
      try {
        const html2pdf = (await import('html2pdf.js')).default
        const opt = {
          margin: [0.5, 0.5, 0.5, 0.5] as [number, number, number, number],
          filename: 'improved-resume.pdf',
          image: { type: 'jpeg' as const, quality: 0.98 },
          html2canvas: { scale: 2, useCORS: true, letterRendering: true },
          jsPDF: { unit: 'in' as const, format: 'letter' as const, orientation: 'portrait' as const }
        }
        await html2pdf().set(opt).from(improvedContentRef.current).save()
      } catch (err) {
        console.error('PDF download error:', err)
        alert('Failed to download PDF. Please try again.')
      } finally {
        setIsDownloading(false)
      }
    } else if (pdfFile) {
      // Download original
      const url = URL.createObjectURL(pdfFile)
      const a = document.createElement('a')
      a.href = url
      a.download = pdfFile.name || 'resume.pdf'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  // Show empty state if no PDF
  if (!pdfFile) {
    return (
      <div className="resume-preview-container">
        <div className="resume-preview-header">
          <div className="preview-title">
            <FileText size={20} />
            <span>Resume Preview</span>
          </div>
        </div>
        <div className="resume-preview-empty">
          <FileText size={48} />
          <p>Your resume will appear here</p>
          <span>Upload a resume to see the preview</span>
        </div>
      </div>
    )
  }

  const isPdf = pdfFile.type === 'application/pdf' || pdfFile.name.toLowerCase().endsWith('.pdf')
  const hasImprovedContent = !!resumeContent
  const showOriginalPdf = viewMode === 'original' && isPdf
  const showImprovedContent = viewMode === 'improved' && hasImprovedContent

  return (
    <div className="resume-preview-container">
      <div className="resume-preview-header">
        <div className="preview-title">
          <FileText size={20} />
          <span>Resume Preview</span>
          {isUpdating && (
            <span className="updating-badge">
              <RefreshCw size={14} className="spin" />
              Updating...
            </span>
          )}
        </div>
        <div className="preview-controls">
          {hasImprovedContent && (
            <div className="view-toggle">
              <button
                className={viewMode === 'original' ? 'active' : ''}
                onClick={() => setViewMode('original')}
              >
                Original
              </button>
              <button
                className={viewMode === 'improved' ? 'active' : ''}
                onClick={() => setViewMode('improved')}
              >
                <Eye size={14} />
                Improved
              </button>
            </div>
          )}
          {showOriginalPdf && numPages > 0 && (
            <>
              <div className="zoom-controls">
                <button onClick={zoomOut} title="Zoom out" disabled={scale <= 0.5}>
                  <ZoomOut size={16} />
                </button>
                <span className="zoom-level">{Math.round(scale * 100)}%</span>
                <button onClick={zoomIn} title="Zoom in" disabled={scale >= 2.0}>
                  <ZoomIn size={16} />
                </button>
              </div>
              {numPages > 1 && (
                <div className="page-controls">
                  <button onClick={goToPrevPage} disabled={pageNumber <= 1}>
                    <ChevronLeft size={16} />
                  </button>
                  <span className="page-info">{pageNumber} / {numPages}</span>
                  <button onClick={goToNextPage} disabled={pageNumber >= numPages}>
                    <ChevronRight size={16} />
                  </button>
                </div>
              )}
            </>
          )}
          <button className="download-btn" onClick={handleDownload} disabled={isDownloading}>
            <Download size={18} />
            {isDownloading ? 'Generating...' : 'Download PDF'}
          </button>
        </div>
      </div>

      <div className="resume-preview-scroll">
        {/* Original PDF View */}
        {showOriginalPdf && (
          <div className="pdf-container">
            {isLoading && (
              <div className="pdf-loading">
                <div className="loading-spinner" />
                <p>Loading PDF...</p>
              </div>
            )}
            {error && (
              <div className="pdf-error">
                <p>{error}</p>
              </div>
            )}
            <Document
              file={originalPdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading=""
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                renderTextLayer={true}
                renderAnnotationLayer={true}
              />
            </Document>
          </div>
        )}

        {/* Improved Content View - Rendered Markdown */}
        {showImprovedContent && (
          <div className="resume-paper" ref={improvedContentRef}>
            <ReactMarkdown>{resumeContent}</ReactMarkdown>
          </div>
        )}

        {/* Non-PDF original file */}
        {!isPdf && viewMode === 'original' && (
          <div className="non-pdf-preview">
            <FileText size={48} />
            <p>Preview not available for {pdfFile.name.split('.').pop()?.toUpperCase()} files</p>
            <span>Click Download to view your file</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default ResumePreview
