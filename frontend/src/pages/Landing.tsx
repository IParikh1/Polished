import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Sparkles,
  FileCheck,
  MessageSquare,
  Download,
  Zap,
  Shield,
  Target,
  ArrowRight,
  CheckCircle2,
  Star
} from 'lucide-react'
import './Landing.css'

function Landing() {
  const navigate = useNavigate()

  const features = [
    {
      icon: <Sparkles size={28} />,
      title: 'FAANG-Level Expertise',
      description: 'AI trained on best practices from top tech recruiters and hiring managers'
    },
    {
      icon: <FileCheck size={28} />,
      title: 'ATS Optimized',
      description: 'Ensure your resume passes Applicant Tracking Systems and reaches human eyes'
    },
    {
      icon: <MessageSquare size={28} />,
      title: 'Interactive Feedback',
      description: 'Chat naturally to get specific advice, rewrites, and improvements'
    },
    {
      icon: <Download size={28} />,
      title: 'Instant PDF Export',
      description: 'Download your polished resume as a professional PDF anytime'
    },
    {
      icon: <Zap size={28} />,
      title: 'Real-time Preview',
      description: 'See your improvements live with side-by-side comparison'
    },
    {
      icon: <Shield size={28} />,
      title: 'Factually Accurate',
      description: 'AI never invents details - only enhances what you provide'
    }
  ]

  const steps = [
    { number: '01', title: 'Upload', description: 'Drop your current resume (PDF, DOCX, or TXT)' },
    { number: '02', title: 'Review', description: 'Get instant expert analysis with actionable feedback' },
    { number: '03', title: 'Refine', description: 'Chat to improve specific sections or get a full rewrite' },
    { number: '04', title: 'Download', description: 'Export your polished resume as a professional PDF' }
  ]

  const testimonials = [
    { quote: 'Landed interviews at 3 FAANG companies after using Polished', author: 'Software Engineer' },
    { quote: 'The ATS optimization tips alone were worth it', author: 'Data Scientist' },
    { quote: 'Like having a career coach available 24/7', author: 'Product Manager' }
  ]

  return (
    <div className="landing">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="nav-brand">
          <Sparkles size={24} />
          <span>Polished</span>
        </div>
        <button className="nav-cta" onClick={() => navigate('/app')}>
          Get Started
          <ArrowRight size={18} />
        </button>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-badge">
            <Star size={14} />
            <span>AI-Powered Resume Expert</span>
          </div>
          <h1>
            Get Your Resume
            <span className="gradient-text"> Polished</span>
          </h1>
          <p className="hero-subtitle">
            AI trained on FAANG hiring best practices.
            Get instant feedback, ATS optimization, and professional rewrites.
          </p>
          <div className="hero-cta">
            <button className="cta-primary" onClick={() => navigate('/app')}>
              Polish My Resume
              <ArrowRight size={20} />
            </button>
            <p className="cta-note">Free to try. No signup required.</p>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-value">FAANG</span>
              <span className="stat-label">Best Practices</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-value">ATS</span>
              <span className="stat-label">Optimized</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-value">24/7</span>
              <span className="stat-label">Available</span>
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="visual-card">
            <div className="visual-header">
              <div className="visual-dots">
                <span /><span /><span />
              </div>
              <span>Resume Preview</span>
            </div>
            <div className="visual-content">
              <div className="visual-line title" />
              <div className="visual-line subtitle" />
              <div className="visual-section">
                <div className="visual-line heading" />
                <div className="visual-line" />
                <div className="visual-line" />
                <div className="visual-line short" />
              </div>
              <div className="visual-section">
                <div className="visual-line heading" />
                <div className="visual-line" />
                <div className="visual-line" />
              </div>
            </div>
            <div className="visual-badge">
              <CheckCircle2 size={16} />
              <span>ATS Score: 95%</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features" id="features">
        <div className="section-header">
          <h2>Everything You Need to Stand Out</h2>
          <p>Comprehensive resume optimization powered by expert AI</p>
        </div>
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works">
        <div className="section-header">
          <h2>How It Works</h2>
          <p>From upload to job-ready in minutes</p>
        </div>
        <div className="steps">
          {steps.map((step, index) => (
            <div key={index} className="step">
              <div className="step-number">{step.number}</div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials">
        <div className="section-header">
          <h2>Trusted by Job Seekers</h2>
          <p>Join thousands who landed their dream jobs</p>
        </div>
        <div className="testimonials-grid">
          {testimonials.map((testimonial, index) => (
            <div key={index} className="testimonial-card">
              <div className="testimonial-stars">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={16} fill="#667eea" color="#667eea" />
                ))}
              </div>
              <p>"{testimonial.quote}"</p>
              <span className="testimonial-author">— {testimonial.author}</span>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Get Polished?</h2>
          <p>Upload your resume and get expert feedback in seconds</p>
          <button className="cta-primary large" onClick={() => navigate('/app')}>
            Start Now — It's Free
            <ArrowRight size={20} />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-brand">
          <Sparkles size={20} />
          <span>Polished</span>
        </div>
        <p>Powered by Polished AI</p>
      </footer>
    </div>
  )
}

export default Landing
