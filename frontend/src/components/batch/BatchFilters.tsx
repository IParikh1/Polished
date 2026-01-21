import { useState } from 'react'
import { Filter, X } from 'lucide-react'

interface BatchFiltersProps {
  filters: {
    minScore: number
    maxScore: number
  }
  onChange: (filters: { minScore: number; maxScore: number }) => void
}

export default function BatchFilters({ filters, onChange }: BatchFiltersProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [localFilters, setLocalFilters] = useState(filters)

  const hasActiveFilters = filters.minScore > 0 || filters.maxScore < 100

  const handleApply = () => {
    onChange(localFilters)
    setIsOpen(false)
  }

  const handleReset = () => {
    const resetFilters = { minScore: 0, maxScore: 100 }
    setLocalFilters(resetFilters)
    onChange(resetFilters)
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`btn-secondary gap-2 ${hasActiveFilters ? 'ring-2 ring-primary-200' : ''}`}
      >
        <Filter className="w-4 h-4" />
        Filters
        {hasActiveFilters && (
          <span className="w-2 h-2 bg-primary-500 rounded-full" />
        )}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-gray-900">Filter Resumes</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Min Score */}
                <div>
                  <label className="label">Minimum Score</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={localFilters.minScore}
                      onChange={(e) =>
                        setLocalFilters((prev) => ({
                          ...prev,
                          minScore: parseInt(e.target.value),
                        }))
                      }
                      className="flex-1"
                    />
                    <span className="w-12 text-sm text-gray-700 text-right">
                      {localFilters.minScore}
                    </span>
                  </div>
                </div>

                {/* Max Score */}
                <div>
                  <label className="label">Maximum Score</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={localFilters.maxScore}
                      onChange={(e) =>
                        setLocalFilters((prev) => ({
                          ...prev,
                          maxScore: parseInt(e.target.value),
                        }))
                      }
                      className="flex-1"
                    />
                    <span className="w-12 text-sm text-gray-700 text-right">
                      {localFilters.maxScore}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 mt-4 pt-4 border-t border-gray-100">
                <button onClick={handleReset} className="flex-1 btn-secondary text-sm">
                  Reset
                </button>
                <button onClick={handleApply} className="flex-1 btn-primary text-sm">
                  Apply
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
