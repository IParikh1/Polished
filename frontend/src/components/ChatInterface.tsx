import React, { useState, useRef, useEffect } from 'react'
import { Send, RefreshCw, User, Bot } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import client from '../api/client'
import './ChatInterface.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  sessionId: string
  initialAnalysis: string
  onNewSession: () => void
  onResumeUpdate?: (content: string) => void
}

// Detect if a message contains an improved/rewritten resume
function detectResumeContent(content: string): string | null {
  // Look for patterns that indicate a full resume rewrite
  const resumePatterns = [
    /^#\s+[A-Z][A-Za-z\s]+\n\*\*Email/m,  // # NAME \n **Email
    /^#\s+[A-Z][A-Za-z\s]+\n.*@.*\.(com|me|io)/m,  // # NAME with email
    /## PROFESSIONAL EXPERIENCE/i,
    /## WORK EXPERIENCE/i,
    /## TECHNICAL SKILLS/i,
    /## EDUCATION\n/i,
  ]

  // Check if content looks like a resume (has multiple resume sections)
  let matchCount = 0
  for (const pattern of resumePatterns) {
    if (pattern.test(content)) {
      matchCount++
    }
  }

  // If it has 3+ resume-like patterns, it's probably a resume
  if (matchCount >= 3) {
    // Extract the resume portion (from the first heading to the end or next non-resume section)
    const lines = content.split('\n')
    let resumeStart = -1
    let resumeEnd = lines.length

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      // Find start - first # heading that looks like a name
      if (resumeStart === -1 && /^#\s+[A-Z]/.test(line)) {
        resumeStart = i
      }
      // Find end - look for improvement notes section
      if (resumeStart !== -1 && /^##\s+(KEY IMPROVEMENTS|IMPROVEMENTS MADE|CHANGES MADE|NOTES:)/i.test(line)) {
        resumeEnd = i
        break
      }
    }

    if (resumeStart !== -1) {
      return lines.slice(resumeStart, resumeEnd).join('\n').trim()
    }
  }

  return null
}

function ChatInterface({ sessionId, initialAnalysis, onNewSession, onResumeUpdate }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: initialAnalysis }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      const response = await client.post('/api/chat', {
        message: userMessage,
        session_id: sessionId
      })

      const assistantResponse = response.data.response
      setMessages(prev => [...prev, { role: 'assistant', content: assistantResponse }])

      // Check if this response contains an improved resume
      const resumeContent = detectResumeContent(assistantResponse)
      if (resumeContent && onResumeUpdate) {
        onResumeUpdate(resumeContent)
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again.'
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const suggestedQuestions = [
    "Improve my resume with better formatting",
    "Rewrite my resume for ATS optimization",
    "What skills should I highlight for FAANG?",
    "Can you rewrite my experience section?"
  ]

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-title">
          <Bot size={24} />
          <span>Resume Expert</span>
        </div>
        <button className="new-session-btn" onClick={onNewSession}>
          <RefreshCw size={18} />
          New Resume
        </button>
      </div>

      <div className="messages-container">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-icon">
              {message.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
            </div>
            <div className="message-content">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-icon">
              <Bot size={20} />
            </div>
            <div className="message-content typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {messages.length === 1 && (
        <div className="suggested-questions">
          {suggestedQuestions.map((q, i) => (
            <button key={i} onClick={() => setInput(q)} className="suggestion">
              {q}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me anything about your resume..."
          rows={1}
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          <Send size={20} />
        </button>
      </div>
    </div>
  )
}

export default ChatInterface
