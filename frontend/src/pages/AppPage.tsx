import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, ArrowLeft } from 'lucide-react'
import ResumeUpload from '../components/ResumeUpload'
import ChatInterface from '../components/ChatInterface'
import ResumePreview from '../components/ResumePreview'
import './AppPage.css'

interface SessionData {
  sessionId: string
  initialAnalysis: string
}

function AppPage() {
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionData | null>(null)
  const [resumeContent, setResumeContent] = useState<string>('')
  const [isUpdating, setIsUpdating] = useState(false)

  const handleUploadComplete = (sessionId: string, initialAnalysis: string) => {
    setSession({ sessionId, initialAnalysis })
    setResumeContent('')
  }

  const handleNewSession = () => {
    setSession(null)
    setResumeContent('')
  }

  const handleResumeUpdate = (content: string) => {
    setIsUpdating(true)
    setTimeout(() => {
      setResumeContent(content)
      setIsUpdating(false)
    }, 300)
  }

  return (
    <div className="app-page">
      <header className="app-header">
        <button className="back-btn" onClick={() => navigate('/')}>
          <ArrowLeft size={20} />
        </button>
        <div className="header-brand" onClick={() => navigate('/')}>
          <Sparkles size={24} />
          <h1>Polished</h1>
        </div>
        <p>AI trained on FAANG hiring best practices</p>
      </header>

      <main className="app-main">
        {!session ? (
          <ResumeUpload onUploadComplete={handleUploadComplete} />
        ) : (
          <div className="workspace">
            <ChatInterface
              sessionId={session.sessionId}
              initialAnalysis={session.initialAnalysis}
              onNewSession={handleNewSession}
              onResumeUpdate={handleResumeUpdate}
            />
            <ResumePreview
              resumeContent={resumeContent}
              isUpdating={isUpdating}
            />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Powered by Polished AI</p>
      </footer>
    </div>
  )
}

export default AppPage
