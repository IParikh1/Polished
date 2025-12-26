import React, { useState, useCallback } from 'react'
import { Upload, FileText, Loader, Sparkles, Shield, Target } from 'lucide-react'
import client from '../api/client'
import './ResumeUpload.css'

interface Props {
  onUploadComplete: (sessionId: string, initialAnalysis: string) => void
}

function ResumeUpload({ onUploadComplete }: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      uploadFile(files[0])
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      uploadFile(files[0])
    }
  }

  const uploadFile = async (file: File) => {
    const validTypes = ['.pdf', '.docx', '.doc', '.txt']
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!validTypes.includes(fileExt)) {
      setError('Please upload a PDF, DOCX, or TXT file')
      return
    }

    setIsUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await client.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      onUploadComplete(response.data.session_id, response.data.initial_analysis)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload resume')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="upload-container">
      <div className="upload-card">
        <div
          className={`upload-zone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isUploading ? (
            <div className="upload-loading">
              <div className="loader-ring">
                <Loader className="spinner" size={32} />
              </div>
              <h3>Analyzing Your Resume</h3>
              <p>Our expert AI is reviewing with 20 years of hiring experience...</p>
              <div className="loading-steps">
                <span className="step active">Parsing content</span>
                <span className="step">Evaluating structure</span>
                <span className="step">Generating insights</span>
              </div>
            </div>
          ) : (
            <>
              <div className="upload-icon-wrapper">
                <Upload size={32} />
              </div>
              <h2>Drop your resume here</h2>
              <p>or click to browse files</p>
              <div className="file-types">
                <span>PDF</span>
                <span>DOCX</span>
                <span>TXT</span>
              </div>
              <input
                type="file"
                accept=".pdf,.docx,.doc,.txt"
                onChange={handleFileSelect}
                className="file-input"
              />
            </>
          )}
        </div>

        {error && (
          <div className="upload-error">
            <span>{error}</span>
          </div>
        )}
      </div>

      <div className="features">
        <div className="feature">
          <div className="feature-icon">
            <Sparkles size={22} />
          </div>
          <div className="feature-content">
            <h3>Expert Analysis</h3>
            <p>AI trained on 50,000+ resumes from top tech companies</p>
          </div>
        </div>
        <div className="feature">
          <div className="feature-icon">
            <Shield size={22} />
          </div>
          <div className="feature-content">
            <h3>ATS Optimized</h3>
            <p>Ensure your resume passes Applicant Tracking Systems</p>
          </div>
        </div>
        <div className="feature">
          <div className="feature-icon">
            <Target size={22} />
          </div>
          <div className="feature-content">
            <h3>FAANG Ready</h3>
            <p>Tailored advice for top tech company applications</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResumeUpload
