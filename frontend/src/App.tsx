import React, { useState } from 'react'
import ResumeUpload from './components/ResumeUpload'
import ChatInterface from './components/ChatInterface'
import ResumePreview from './components/ResumePreview'
import './App.css'

interface SessionData {
  sessionId: string
  initialAnalysis: string
}

function App() {
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
    // Small delay for visual feedback
    setTimeout(() => {
      setResumeContent(content)
      setIsUpdating(false)
    }, 300)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Polished</h1>
        <p>Expert AI with 20 years of tech hiring experience</p>
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

export default App
