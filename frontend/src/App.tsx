import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import { SignInPage, SignUpPage, ProtectedRoute } from './components/auth'
import BatchDashboard from './pages/BatchDashboard'
import ConsultingPage from './pages/ConsultingPage'
import WritingPage from './pages/WritingPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'
import HelpPage from './pages/HelpPage'
import PricingPage from './pages/PricingPage'

function App() {
  return (
    <Routes>
      {/* Public auth routes */}
      <Route path="/sign-in/*" element={<SignInPage />} />
      <Route path="/sign-up/*" element={<SignUpPage />} />

      {/* Protected app routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/batches" replace />} />
        <Route path="batches" element={<BatchDashboard />} />
        <Route path="batches/:batchId" element={<BatchDashboard />} />
        <Route path="consulting" element={<ConsultingPage />} />
        <Route path="consulting/:sessionId" element={<ConsultingPage />} />
        <Route path="writing" element={<WritingPage />} />
        <Route path="writing/:batchId/:resumeId" element={<WritingPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="pricing" element={<PricingPage />} />
        <Route path="help" element={<HelpPage />} />
      </Route>
    </Routes>
  )
}

export default App
