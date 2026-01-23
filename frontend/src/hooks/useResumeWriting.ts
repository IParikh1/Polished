import { useMutation, useQuery } from '@tanstack/react-query'
import {
  generateResume,
  rewriteSection,
  generateSummary,
  enhanceBullets,
  exportResume,
  listResumeTemplates,
  listSalesRoles,
  getWritingStatus,
  type ResumeGenerateRequest,
  type ResumeGenerateResponse,
  type RewriteSectionRequest,
  type RewriteSectionResponse,
  type GenerateSummaryRequest,
  type GenerateSummaryResponse,
  type EnhanceBulletsRequest,
  type EnhanceBulletsResponse,
  type ExportResumeRequest,
  type ExportResumeResponse,
} from '../api/batchClient'

/**
 * Hook to generate an optimized resume using AI.
 */
export function useGenerateResume() {
  return useMutation<ResumeGenerateResponse, Error, ResumeGenerateRequest>({
    mutationFn: generateResume,
  })
}

/**
 * Hook to rewrite a specific resume section.
 */
export function useRewriteSection() {
  return useMutation<RewriteSectionResponse, Error, RewriteSectionRequest>({
    mutationFn: rewriteSection,
  })
}

/**
 * Hook to generate professional summary variants.
 */
export function useGenerateSummary() {
  return useMutation<GenerateSummaryResponse, Error, GenerateSummaryRequest>({
    mutationFn: generateSummary,
  })
}

/**
 * Hook to enhance experience bullet points.
 */
export function useEnhanceBullets() {
  return useMutation<EnhanceBulletsResponse, Error, EnhanceBulletsRequest>({
    mutationFn: enhanceBullets,
  })
}

/**
 * Hook to export resume to document format.
 */
export function useExportResume() {
  return useMutation<ExportResumeResponse, Error, ExportResumeRequest>({
    mutationFn: exportResume,
  })
}

/**
 * Hook to get available resume templates.
 */
export function useResumeTemplates() {
  return useQuery({
    queryKey: ['resume-templates'],
    queryFn: listResumeTemplates,
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
  })
}

/**
 * Hook to get available sales roles.
 */
export function useSalesRoles() {
  return useQuery({
    queryKey: ['sales-roles'],
    queryFn: listSalesRoles,
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
  })
}

/**
 * Hook to check resume writing service status.
 */
export function useWritingStatus() {
  return useQuery({
    queryKey: ['writing-status'],
    queryFn: getWritingStatus,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  })
}
