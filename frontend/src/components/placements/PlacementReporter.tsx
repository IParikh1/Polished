import { useState } from 'react'
import { DollarSign, Building, User, Calendar, Loader2, CheckCircle2 } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

interface PlacementReporterProps {
  batchId: string
  resumeId: string
  candidateName?: string
  onSuccess?: () => void
}

export default function PlacementReporter({
  batchId,
  resumeId,
  candidateName,
  onSuccess,
}: PlacementReporterProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [formData, setFormData] = useState({
    company_name: '',
    position: '',
    candidate_name: candidateName || '',
    placement_date: '',
    notes: '',
  })

  const queryClient = useQueryClient()

  const createPlacement = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await axios.post('/api/v1/placements', {
        batch_id: batchId,
        resume_id: resumeId,
        ...data,
        placement_date: data.placement_date || undefined,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['placements'] })
      setIsOpen(false)
      setFormData({
        company_name: '',
        position: '',
        candidate_name: candidateName || '',
        placement_date: '',
        notes: '',
      })
      onSuccess?.()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.company_name || !formData.position) return
    createPlacement.mutate(formData)
  }

  if (!isOpen) {
    return (
      <button onClick={() => setIsOpen(true)} className="btn-success gap-2">
        <DollarSign className="w-4 h-4" />
        Report Placement
      </button>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg bg-white rounded-xl shadow-xl">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-success-50 rounded-lg">
              <DollarSign className="w-5 h-5 text-success-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Report Placement</h2>
              <p className="text-sm text-gray-500">Earn $250 for verified placements</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="label flex items-center gap-2">
              <Building className="w-4 h-4 text-gray-400" />
              Company Name *
            </label>
            <input
              type="text"
              required
              value={formData.company_name}
              onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
              placeholder="e.g., Acme Corporation"
              className="input"
            />
          </div>

          <div>
            <label className="label flex items-center gap-2">
              <User className="w-4 h-4 text-gray-400" />
              Position *
            </label>
            <input
              type="text"
              required
              value={formData.position}
              onChange={(e) => setFormData({ ...formData, position: e.target.value })}
              placeholder="e.g., Senior Software Engineer"
              className="input"
            />
          </div>

          <div>
            <label className="label">Candidate Name</label>
            <input
              type="text"
              value={formData.candidate_name}
              onChange={(e) => setFormData({ ...formData, candidate_name: e.target.value })}
              placeholder="e.g., John Doe"
              className="input"
            />
          </div>

          <div>
            <label className="label flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-400" />
              Placement Date
            </label>
            <input
              type="date"
              value={formData.placement_date}
              onChange={(e) => setFormData({ ...formData, placement_date: e.target.value })}
              className="input"
            />
          </div>

          <div>
            <label className="label">Notes (optional)</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Any additional information..."
              className="input min-h-[80px]"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="flex-1 btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createPlacement.isPending || !formData.company_name || !formData.position}
              className="flex-1 btn-success gap-2"
            >
              {createPlacement.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : createPlacement.isSuccess ? (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  Submitted!
                </>
              ) : (
                <>
                  <DollarSign className="w-4 h-4" />
                  Submit Placement
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
