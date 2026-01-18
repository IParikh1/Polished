import React, { useState, useRef, useEffect } from 'react'
import { Send, RefreshCw, User, Bot, FileText } from 'lucide-react'
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
function detectAndExtractResume(content: string): { resumeContent: string | null; summaryContent: string } {
  // Look for patterns that indicate a full resume rewrite
  const resumePatterns = [
    /^#\s+[A-Z][A-Za-z\s]+\n\*\*Email/m,
    /^#\s+[A-Z][A-Za-z\s]+\n.*@.*\.(com|me|io|org|net)/m,
    /## PROFESSIONAL EXPERIENCE/i,
    /## WORK EXPERIENCE/i,
    /## EXPERIENCE\n/i,
    /## TECHNICAL SKILLS/i,
    /## SKILLS\n/i,
    /## EDUCATION\n/i,
  ]

  // Check if content looks like a resume (has multiple resume sections)
  let matchCount = 0
  for (const pattern of resumePatterns) {
    if (pattern.test(content)) {
      matchCount++
    }
  }

  // If it has 2+ resume-like patterns, it's probably a resume
  if (matchCount >= 2) {
    const lines = content.split('\n')
    let resumeStart = -1
    let resumeEnd = lines.length
    let summaryStart = -1
    let summaryEnd = -1

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]

      // Find start of resume - first # heading that looks like a name
      if (resumeStart === -1 && /^#\s+[A-Z]/.test(line)) {
        resumeStart = i
        // Check if there's content before the resume (summary/intro)
        if (i > 0) {
          summaryEnd = i
        }
      }

      // Find end of resume - look for improvement notes section
      if (resumeStart !== -1 && /^##\s*(KEY IMPROVEMENTS|IMPROVEMENTS MADE|CHANGES MADE|NOTES|SUMMARY OF CHANGES|WHAT I CHANGED)/i.test(line)) {
        resumeEnd = i
        summaryStart = i
        break
      }
    }

    if (resumeStart !== -1) {
      const resumeContent = lines.slice(resumeStart, resumeEnd).join('\n').trim()

      // Build summary content (intro + changes section)
      let summaryParts: string[] = []

      // Add any intro text before the resume
      if (summaryEnd > 0) {
        summaryParts.push(lines.slice(0, summaryEnd).join('\n').trim())
      }

      // Add any changes/notes section after the resume
      if (summaryStart !== -1) {
        summaryParts.push(lines.slice(summaryStart).join('\n').trim())
      }

      // If no summary found, create a default one
      const summaryContent = summaryParts.length > 0
        ? summaryParts.join('\n\n')
        : "✅ **Resume Updated!** I've rewritten your resume with the improvements. Check the preview panel to see the changes, and click 'Download PDF' when you're ready."

      return { resumeContent, summaryContent }
    }
  }

  return { resumeContent: null, summaryContent: content }
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

      // Check if this response contains an improved resume
      const { resumeContent, summaryContent } = detectAndExtractResume(assistantResponse)

      // Show only summary in chat (not the full resume)
      setMessages(prev => [...prev, { role: 'assistant', content: summaryContent }])

      // Send resume content to preview if found
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
    "Rewrite my full resume with ATS optimization",
    "Improve my bullet points with better metrics",
    "What are the top 3 things I should fix?",
    "Make my experience section more impactful"
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
