import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import * as batchApi from '../api/batchClient'

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
    mutationFn: (files: File[]) => batchApi.uploadMultipleResumes(batchId, files),
    onSuccess: (data) => {
      setState((prev) => ({
        ...prev,
        isUploading: false,
        uploadedCount: data.uploaded,
        errors: data.results
          .filter((r) => r.status === 'error')
          .map((r) => ({ filename: r.filename, error: r.error || 'Unknown error' })),
      }))
      queryClient.invalidateQueries({ queryKey: ['batch', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batch-resumes', batchId] })
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
    (files: File[]) => {
      setState({
        isUploading: true,
        progress: 0,
        uploadedCount: 0,
        totalCount: files.length,
        errors: [],
      })
      uploadMutation.mutate(files)
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
      queryClient.invalidateQueries({ queryKey: ['batch', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batch-resumes', batchId] })
    },
  })
}
