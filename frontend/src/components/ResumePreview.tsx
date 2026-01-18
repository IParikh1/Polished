import React, { useState, useMemo, useEffect, useRef } from 'react'
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
  const [improvedPdfBlob, setImprovedPdfBlob] = useState<Blob | null>(null)
  const [isGeneratingPdf, setIsGeneratingPdf] = useState<boolean>(false)
  const improvedContentRef = useRef<HTMLDivElement>(null)

  // Create a URL for the original PDF file
  const originalPdfUrl = useMemo(() => {
    if (pdfFile) {
      return URL.createObjectURL(pdfFile)
    }
    return null
  }, [pdfFile])

  // Create a URL for the improved PDF
  const improvedPdfUrl = useMemo(() => {
    if (improvedPdfBlob) {
      return URL.createObjectURL(improvedPdfBlob)
    }
    return null
  }, [improvedPdfBlob])

  // Determine which PDF to show
  const activePdfUrl = viewMode === 'improved' && improvedPdfUrl ? improvedPdfUrl : originalPdfUrl

  // Generate PDF from improved content when it changes
  useEffect(() => {
    if (resumeContent && viewMode === 'improved') {
      generateImprovedPdf()
    }
  }, [resumeContent, viewMode])

  // Auto-switch to improved view when new content arrives
  useEffect(() => {
    if (resumeContent) {
      setViewMode('improved')
    }
  }, [resumeContent])

  const generateImprovedPdf = async () => {
    if (!resumeContent || !improvedContentRef.current) return

    setIsGeneratingPdf(true)
    try {
      const html2pdf = (await import('html2pdf.js')).default

      const element = improvedContentRef.current
      const opt = {
        margin: [0.5, 0.5, 0.5, 0.5] as [number, number, number, number],
        filename: 'improved-resume.pdf',
        image: { type: 'jpeg' as const, quality: 0.98 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          letterRendering: true
        },
        jsPDF: {
          unit: 'in' as const,
          format: 'letter' as const,
          orientation: 'portrait' as const
        }
      }

      const pdfBlob = await html2pdf().set(opt).from(element).outputPdf('blob')
      setImprovedPdfBlob(pdfBlob)
      setPageNumber(1)
    } catch (err) {
      console.error('PDF generation error:', err)
      setError('Failed to generate improved PDF')
    } finally {
      setIsGeneratingPdf(false)
    }
  }

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
    if (viewMode === 'improved' && resumeContent) {
      // Download improved version
      if (improvedPdfBlob) {
        const url = URL.createObjectURL(improvedPdfBlob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'improved-resume.pdf'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } else {
        // Generate and download
        await generateImprovedPdf()
        if (improvedPdfBlob) {
          const url = URL.createObjectURL(improvedPdfBlob)
          const a = document.createElement('a')
          a.href = url
          a.download = 'improved-resume.pdf'
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          URL.revokeObjectURL(url)
        }
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
  const showPdfView = isPdf && (viewMode === 'original' || (viewMode === 'improved' && improvedPdfBlob))

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
          {showPdfView && numPages > 0 && (
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
          <button className="download-btn" onClick={handleDownload} disabled={isGeneratingPdf}>
            <Download size={18} />
            {isGeneratingPdf ? 'Generating...' : 'Download PDF'}
          </button>
        </div>
      </div>

      <div className="resume-preview-scroll">
        {/* Hidden div for PDF generation */}
        {resumeContent && (
          <div className="hidden-content" ref={improvedContentRef}>
            <div className="resume-paper-hidden">
              <ReactMarkdown>{resumeContent}</ReactMarkdown>
            </div>
          </div>
        )}

        {isGeneratingPdf && viewMode === 'improved' && (
          <div className="pdf-loading">
            <div className="loading-spinner" />
            <p>Generating improved resume...</p>
          </div>
        )}

        {viewMode === 'improved' && !improvedPdfBlob && !isGeneratingPdf && resumeContent && (
          <div className="resume-paper">
            <ReactMarkdown>{resumeContent}</ReactMarkdown>
          </div>
        )}

        {showPdfView && !isGeneratingPdf && (
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
              file={activePdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading=""
              key={activePdfUrl}
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
