import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import BatchDashboard from './pages/BatchDashboard'
import ConsultingPage from './pages/ConsultingPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/batches" replace />} />
        <Route path="batches" element={<BatchDashboard />} />
        <Route path="batches/:batchId" element={<BatchDashboard />} />
        <Route path="consulting" element={<ConsultingPage />} />
        <Route path="consulting/:sessionId" element={<ConsultingPage />} />
      </Route>
    </Routes>
  )
}

export default App
