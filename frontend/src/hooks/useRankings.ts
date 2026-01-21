import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as batchApi from '../api/batchClient'

export function useBatchResumes(batchId: string | undefined, includeDownloadUrls = false) {
  return useQuery({
    queryKey: ['batch-resumes', batchId, includeDownloadUrls],
    queryFn: () => batchApi.getBatchResumes(batchId!, includeDownloadUrls),
    enabled: !!batchId,
  })
}

export function useResume(batchId: string | undefined, resumeId: string | undefined) {
  return useQuery({
    queryKey: ['resume', batchId, resumeId],
    queryFn: () => batchApi.getResume(batchId!, resumeId!),
    enabled: !!batchId && !!resumeId,
  })
}

export function useRankings(
  batchId: string | undefined,
  options?: {
    min_score?: number
    max_score?: number
    limit?: number
    offset?: number
  }
) {
  return useQuery({
    queryKey: ['rankings', batchId, options],
    queryFn: () => batchApi.getRankings(batchId!, options),
    enabled: !!batchId,
  })
}

export function useExportBatch() {
  return useMutation({
    mutationFn: ({ batchId, options }: { batchId: string; options: batchApi.ExportRequest }) =>
      batchApi.exportBatch(batchId, options),
  })
}

export function useBatchExports(batchId: string | undefined) {
  return useQuery({
    queryKey: ['batch-exports', batchId],
    queryFn: () => batchApi.listExports(batchId!),
    enabled: !!batchId,
  })
}
