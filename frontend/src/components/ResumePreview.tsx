import React, { useState, useMemo } from 'react'
import { Download, FileText, ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react'
import { Document, Page, pdfjs } from 'react-pdf'
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

function ResumePreview({ pdfFile, resumeContent, isUpdating }: Props) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Create a URL for the PDF file
  const pdfUrl = useMemo(() => {
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

  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(prev - 1, 1))
  }

  const goToNextPage = () => {
    setPageNumber(prev => Math.min(prev + 1, numPages))
  }

  const zoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 2.0))
  }

  const zoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5))
  }

  const handleDownload = () => {
    if (pdfFile) {
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

  // Check if the file is a PDF
  const isPdf = pdfFile.type === 'application/pdf' || pdfFile.name.toLowerCase().endsWith('.pdf')

  return (
    <div className="resume-preview-container">
      <div className="resume-preview-header">
        <div className="preview-title">
          <FileText size={20} />
          <span>Resume Preview</span>
        </div>
        <div className="preview-controls">
          {isPdf && numPages > 0 && (
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
          <button className="download-btn" onClick={handleDownload}>
            <Download size={18} />
            Download
          </button>
        </div>
      </div>

      <div className="resume-preview-scroll">
        {isPdf ? (
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
              file={pdfUrl}
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
        ) : (
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
