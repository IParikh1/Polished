import React, { useState, useMemo, useRef } from 'react'
import { Download, FileText, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RefreshCw, Eye, ChevronDown } from 'lucide-react'
import { Document, Page, pdfjs } from 'react-pdf'
import ReactMarkdown from 'react-markdown'
import { Document as DocxDocument, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, BorderStyle } from 'docx'
import { saveAs } from 'file-saver'
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

// Normalize markdown content before processing to enforce correct format
function normalizeResumeMarkdown(markdown: string): string {
  let content = markdown

  // Remove any "REWRITTEN RESUME" or similar titles that precede the actual name
  content = content.replace(/^#\s*(REWRITTEN|IMPROVED|UPDATED|NEW)\s*(RESUME|VERSION)[\s\n]*/i, '')

  // Ensure proper spacing around section headers
  content = content.replace(/\n(##\s+)/g, '\n\n$1')

  // Normalize bullet points
  content = content.replace(/^[•*]\s+/gm, '- ')
  content = content.replace(/^(\s+)[•*]\s+/gm, '$1- ')

  return content.trim()
}

// Parse a line that contains company/date or job title/location with pipe separators
function parseCompanyOrTitleLine(line: string): TextRun[] {
  const runs: TextRun[] = []

  // Check if line has pipe separators (e.g., "**Company** | *Date*" or "*Title* | *Location*")
  if (line.includes('|')) {
    const parts = line.split('|').map(p => p.trim())

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]

      // Parse bold (**text**)
      const boldMatch = part.match(/^\*\*(.+)\*\*$/)
      if (boldMatch) {
        runs.push(new TextRun({ text: boldMatch[1], bold: true, size: 22 }))
      }
      // Parse italic (*text*)
      else if (part.match(/^\*(.+)\*$/)) {
        const italicMatch = part.match(/^\*(.+)\*$/)
        if (italicMatch) {
          runs.push(new TextRun({ text: italicMatch[1], italics: true, size: 22 }))
        }
      }
      // Plain text
      else {
        // Also parse inline formatting within the part
        const inlineRuns = parseInlineFormatting(part)
        runs.push(...inlineRuns)
      }

      // Add separator between parts (except for last)
      if (i < parts.length - 1) {
        runs.push(new TextRun({ text: ' | ', size: 22 }))
      }
    }
  } else {
    // No pipes, parse normally
    return parseInlineFormatting(line)
  }

  return runs
}

// Detect if a line is a company header (bold company name with optional date)
function isCompanyLine(line: string): boolean {
  // Company lines typically start with **CompanyName** and may have date
  return /^\*\*[^*]+\*\*/.test(line.trim())
}

// Detect if a line is a job title (italic text, possibly with location/department)
function isJobTitleLine(line: string): boolean {
  // Job title lines typically start with *Title* (italic)
  const trimmed = line.trim()
  return /^\*[^*]+\*/.test(trimmed) && !trimmed.startsWith('**')
}

// Convert markdown to Word document paragraphs
function markdownToDocx(markdown: string): Paragraph[] {
  const paragraphs: Paragraph[] = []
  const normalizedMarkdown = normalizeResumeMarkdown(markdown)
  const lines = normalizedMarkdown.split('\n')

  let isFirstParagraphAfterName = false
  let foundName = false

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // Skip empty lines but add spacing
    if (!line.trim()) {
      if (foundName && isFirstParagraphAfterName) {
        // Don't add extra blank after contact info
        isFirstParagraphAfterName = false
        continue
      }
      paragraphs.push(new Paragraph({ text: '', spacing: { after: 50 } }))
      continue
    }

    // H1 - Name (centered, large, with underline)
    if (line.startsWith('# ')) {
      foundName = true
      isFirstParagraphAfterName = true
      paragraphs.push(new Paragraph({
        children: [new TextRun({ text: line.slice(2).trim(), bold: true, size: 40 })],
        heading: HeadingLevel.HEADING_1,
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: '333333' } }
      }))
      continue
    }

    // H2 - Section headers (with border)
    if (line.startsWith('## ')) {
      paragraphs.push(new Paragraph({
        children: [new TextRun({ text: line.slice(3).toUpperCase().trim(), bold: true, size: 24 })],
        heading: HeadingLevel.HEADING_2,
        spacing: { before: 200, after: 80 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '333333' } }
      }))
      continue
    }

    // H3 - Sub-section headers
    if (line.startsWith('### ')) {
      paragraphs.push(new Paragraph({
        children: [new TextRun({ text: line.slice(4).trim(), bold: true, size: 22 })],
        heading: HeadingLevel.HEADING_3,
        spacing: { before: 150, after: 50 }
      }))
      continue
    }

    // Contact info line (right after name, contains email/phone/location)
    if (isFirstParagraphAfterName && (line.includes('@') || line.includes('|'))) {
      isFirstParagraphAfterName = false
      const children: TextRun[] = parseInlineFormatting(line)
      paragraphs.push(new Paragraph({
        children,
        alignment: AlignmentType.CENTER,
        spacing: { after: 150 }
      }))
      continue
    }

    isFirstParagraphAfterName = false

    // Company line (bold company name with date)
    if (isCompanyLine(line)) {
      const children: TextRun[] = parseCompanyOrTitleLine(line)
      paragraphs.push(new Paragraph({
        children,
        spacing: { before: 150, after: 30 }
      }))
      continue
    }

    // Job title line (italic title with location/department)
    if (isJobTitleLine(line)) {
      const children: TextRun[] = parseCompanyOrTitleLine(line)
      paragraphs.push(new Paragraph({
        children,
        spacing: { before: 30, after: 50 }
      }))
      continue
    }

    // Bullet points
    if (line.startsWith('- ') || line.startsWith('* ')) {
      const bulletText = line.slice(2)
      const children: TextRun[] = parseInlineFormatting(bulletText)
      paragraphs.push(new Paragraph({
        children,
        bullet: { level: 0 },
        spacing: { after: 40 }
      }))
      continue
    }

    // Sub-bullets (indented)
    if (line.match(/^(\s{2,}|\t)[-*]\s/)) {
      const bulletText = line.replace(/^(\s{2,}|\t)[-*]\s/, '')
      const children: TextRun[] = parseInlineFormatting(bulletText)
      paragraphs.push(new Paragraph({
        children,
        bullet: { level: 1 },
        spacing: { after: 40 }
      }))
      continue
    }

    // Skills line (bold category followed by colon)
    if (line.match(/^\*\*[^:]+:\*\*/)) {
      const children: TextRun[] = parseInlineFormatting(line)
      paragraphs.push(new Paragraph({
        children,
        spacing: { after: 50 }
      }))
      continue
    }

    // Regular paragraph with inline formatting
    const children: TextRun[] = parseInlineFormatting(line)
    paragraphs.push(new Paragraph({
      children,
      spacing: { after: 50 }
    }))
  }

  return paragraphs
}

// Parse inline markdown formatting (bold, italic)
function parseInlineFormatting(text: string): TextRun[] {
  const runs: TextRun[] = []
  let remaining = text

  // Pattern for **bold** and *italic*
  const pattern = /(\*\*([^*]+)\*\*|\*([^*]+)\*)/g
  let lastIndex = 0
  let match

  while ((match = pattern.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      runs.push(new TextRun({ text: text.slice(lastIndex, match.index), size: 22 }))
    }

    // Add the formatted text
    if (match[2]) {
      // Bold text
      runs.push(new TextRun({ text: match[2], bold: true, size: 22 }))
    } else if (match[3]) {
      // Italic text
      runs.push(new TextRun({ text: match[3], italics: true, size: 22 }))
    }

    lastIndex = match.index + match[0].length
  }

  // Add remaining text
  if (lastIndex < text.length) {
    runs.push(new TextRun({ text: text.slice(lastIndex), size: 22 }))
  }

  // If no formatting found, return the whole text
  if (runs.length === 0) {
    runs.push(new TextRun({ text, size: 22 }))
  }

  return runs
}

function ResumePreview({ pdfFile, resumeContent, isUpdating }: Props) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('original')
  const [isDownloading, setIsDownloading] = useState<boolean>(false)
  const [showDownloadMenu, setShowDownloadMenu] = useState<boolean>(false)
  const improvedContentRef = useRef<HTMLDivElement>(null)
  const downloadMenuRef = useRef<HTMLDivElement>(null)

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

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (downloadMenuRef.current && !downloadMenuRef.current.contains(event.target as Node)) {
        setShowDownloadMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleDownloadPDF = async () => {
    setShowDownloadMenu(false)
    if (viewMode === 'improved' && resumeContent && improvedContentRef.current) {
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

  const handleDownloadWord = async () => {
    setShowDownloadMenu(false)
    if (viewMode === 'improved' && resumeContent) {
      setIsDownloading(true)
      try {
        const paragraphs = markdownToDocx(resumeContent)
        const doc = new DocxDocument({
          sections: [{
            properties: {
              page: {
                margin: {
                  top: 720,    // 0.5 inch in twips
                  right: 720,
                  bottom: 720,
                  left: 720
                }
              }
            },
            children: paragraphs
          }]
        })
        const blob = await Packer.toBlob(doc)
        saveAs(blob, 'improved-resume.docx')
      } catch (err) {
        console.error('Word download error:', err)
        alert('Failed to download Word document. Please try again.')
      } finally {
        setIsDownloading(false)
      }
    } else {
      alert('Word export is only available for the improved resume. Please generate an improved version first.')
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
          <div className="download-dropdown" ref={downloadMenuRef}>
            <button
              className="download-btn"
              onClick={() => setShowDownloadMenu(!showDownloadMenu)}
              disabled={isDownloading}
            >
              <Download size={18} />
              {isDownloading ? 'Generating...' : 'Download'}
              <ChevronDown size={14} />
            </button>
            {showDownloadMenu && (
              <div className="download-menu">
                <button onClick={handleDownloadPDF}>
                  <FileText size={16} />
                  Download PDF
                </button>
                <button onClick={handleDownloadWord} disabled={!hasImprovedContent || viewMode !== 'improved'}>
                  <FileText size={16} />
                  Download Word (.docx)
                </button>
              </div>
            )}
          </div>
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
            <ReactMarkdown>{normalizeResumeMarkdown(resumeContent || '')}</ReactMarkdown>
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
