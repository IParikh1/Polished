import React, { useRef, useEffect, useState } from 'react'
import { Download, FileText, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import './ResumePreview.css'

interface Props {
  resumeContent: string
  isUpdating?: boolean
}

function ResumePreview({ resumeContent, isUpdating }: Props) {
  const resumeRef = useRef<HTMLDivElement>(null)
  const [isDownloading, setIsDownloading] = useState(false)

  const handleDownload = async () => {
    if (!resumeRef.current || isDownloading) return

    setIsDownloading(true)

    try {
      // Dynamic import to avoid SSR issues
      const html2pdf = (await import('html2pdf.js')).default

      const element = resumeRef.current
      const opt = {
        margin: 0.5,
        filename: 'resume.pdf',
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

      await html2pdf().set(opt).from(element).save()
    } catch (err) {
      console.error('PDF download error:', err)
      alert('Failed to download PDF. Please try again.')
    } finally {
      setIsDownloading(false)
    }
  }

  if (!resumeContent) {
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
          <p>Your improved resume will appear here</p>
          <span>Ask the agent to improve your resume to see a live preview</span>
        </div>
      </div>
    )
  }

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
        <button
          className="download-btn"
          onClick={handleDownload}
          disabled={isDownloading}
        >
          <Download size={18} />
          {isDownloading ? 'Generating...' : 'Download PDF'}
        </button>
      </div>

      <div className="resume-preview-scroll">
        <div className="resume-paper" ref={resumeRef}>
          <ReactMarkdown>{resumeContent}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}

export default ResumePreview
