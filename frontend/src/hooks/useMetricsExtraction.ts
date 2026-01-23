import { useMutation } from '@tanstack/react-query'
import {
  extractMetrics,
  formatMetrics,
  type MetricsExtractionRequest,
  type MetricsExtractionResponse,
  type MetricsFormatRequest,
  type MetricsFormatResponse,
} from '../api/batchClient'

/**
 * Hook to extract metrics from a resume.
 */
export function useExtractMetrics() {
  return useMutation<MetricsExtractionResponse, Error, MetricsExtractionRequest>({
    mutationFn: extractMetrics,
  })
}

/**
 * Hook to format collected metrics into resume bullets.
 */
export function useFormatMetrics() {
  return useMutation<MetricsFormatResponse, Error, MetricsFormatRequest>({
    mutationFn: formatMetrics,
  })
}
