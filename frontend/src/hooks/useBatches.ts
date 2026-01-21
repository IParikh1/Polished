import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as batchApi from '../api/batchClient'

export function useBatches(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ['batches', limit, offset],
    queryFn: () => batchApi.listBatches(limit, offset),
  })
}

export function useBatch(batchId: string | undefined) {
  return useQuery({
    queryKey: ['batch', batchId],
    queryFn: () => batchApi.getBatch(batchId!),
    enabled: !!batchId,
  })
}

export function useCreateBatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: batchApi.createBatch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
  })
}

export function useUpdateBatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ batchId, data }: { batchId: string; data: Partial<batchApi.CreateBatchRequest> }) =>
      batchApi.updateBatch(batchId, data),
    onSuccess: (_, { batchId }) => {
      queryClient.invalidateQueries({ queryKey: ['batch', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
  })
}

export function useDeleteBatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: batchApi.deleteBatch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
  })
}

export function useProcessBatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: batchApi.processBatch,
    onSuccess: (_, batchId) => {
      queryClient.invalidateQueries({ queryKey: ['batch', batchId] })
    },
  })
}

export function useProcessingStatus(batchId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ['processing-status', batchId],
    queryFn: () => batchApi.getProcessingStatus(batchId!),
    enabled: enabled && !!batchId,
    refetchInterval: (data) => {
      // Poll every 2 seconds while processing
      if (data?.status === 'processing') {
        return 2000
      }
      return false
    },
  })
}
