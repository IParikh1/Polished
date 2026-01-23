import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import * as batchApi from '../api/batchClient'
import type { SalesRole } from '../api/batchClient'

export interface UploadState {
  isUploading: boolean
  progress: number
  uploadedCount: number
  totalCount: number
  errors: Array<{ filename: string; error: string }>
}

export function useUpload(batchId: string) {
  const queryClient = useQueryClient()
  const [state, setState] = useState<UploadState>({
    isUploading: false,
    progress: 0,
    uploadedCount: 0,
    totalCount: 0,
    errors: [],
  })

  const uploadMutation = useMutation({
    mutationFn: ({ files, targetRole }: { files: File[]; targetRole?: SalesRole }) =>
      batchApi.uploadMultipleResumes(batchId, files, targetRole),
    onSuccess: (data) => {
      setState((prev) => ({
        ...prev,
        isUploading: false,
        uploadedCount: data.uploaded,
        errors: data.results
          .filter((r) => r.status === 'error')
          .map((r) => ({ filename: r.filename, error: r.error || 'Unknown error' })),
      }))
      // Invalidate all relevant queries to sync resume counts in real-time
      queryClient.invalidateQueries({ queryKey: ['batch', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batch-resumes', batchId] })
      queryClient.invalidateQueries({ queryKey: ['rankings', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
    onError: (error) => {
      setState((prev) => ({
        ...prev,
        isUploading: false,
        errors: [{ filename: 'Upload failed', error: error instanceof Error ? error.message : 'Unknown error' }],
      }))
    },
  })

  const upload = useCallback(
    (files: File[], targetRole?: SalesRole) => {
      setState({
        isUploading: true,
        progress: 0,
        uploadedCount: 0,
        totalCount: files.length,
        errors: [],
      })
      uploadMutation.mutate({ files, targetRole })
    },
    [uploadMutation]
  )

  const reset = useCallback(() => {
    setState({
      isUploading: false,
      progress: 0,
      uploadedCount: 0,
      totalCount: 0,
      errors: [],
    })
  }, [])

  return {
    ...state,
    upload,
    reset,
    isLoading: uploadMutation.isPending,
  }
}

export function useSingleUpload(batchId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => batchApi.uploadResume(batchId, file),
    onSuccess: () => {
      // Invalidate all relevant queries to sync resume counts in real-time
      queryClient.invalidateQueries({ queryKey: ['batch', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batch-resumes', batchId] })
      queryClient.invalidateQueries({ queryKey: ['rankings', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
  })
}
