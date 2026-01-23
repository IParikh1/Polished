import { useMutation, useQuery } from '@tanstack/react-query'
import {
  matchJobDescription,
  matchResumeToJD,
  tailorResume,
  setResumeRole,
  parseJobDescription,
  type JDMatchRequest,
  type JDMatchResult,
  type TailoredResumeRequest,
  type TailoredResumeResponse,
  type SalesRole,
  type SetRoleResponse,
} from '../api/batchClient'

/**
 * Hook to match a resume against a job description using the general endpoint.
 * Requires batch_id and resume_id in the request.
 */
export function useMatchJD() {
  return useMutation<JDMatchResult, Error, JDMatchRequest>({
    mutationFn: matchJobDescription,
  })
}

/**
 * Hook to match a specific resume against a job description.
 * Uses the path-based endpoint with batch_id and resume_id.
 */
export function useMatchResumeToJD() {
  return useMutation<
    JDMatchResult,
    Error,
    {
      batchId: string
      resumeId: string
      jobDescription: string
      jobTitle?: string
      targetRole?: SalesRole
    }
  >({
    mutationFn: ({ batchId, resumeId, jobDescription, jobTitle, targetRole }) =>
      matchResumeToJD(batchId, resumeId, jobDescription, jobTitle, targetRole),
  })
}

/**
 * Hook to generate a JD-tailored version of a resume.
 */
export function useTailorResume() {
  return useMutation<TailoredResumeResponse, Error, TailoredResumeRequest>({
    mutationFn: tailorResume,
  })
}

/**
 * Hook to set the target sales role for a resume.
 */
export function useSetResumeRole() {
  return useMutation<
    SetRoleResponse,
    Error,
    {
      batchId: string
      resumeId: string
      role: SalesRole
    }
  >({
    mutationFn: ({ batchId, resumeId, role }) =>
      setResumeRole(batchId, resumeId, role),
  })
}

/**
 * Hook to parse a job description and extract requirements.
 * Useful for debugging or showing users what requirements were detected.
 */
export function useParseJD(jobDescription: string, enabled = false) {
  return useQuery({
    queryKey: ['parse-jd', jobDescription],
    queryFn: () => parseJobDescription(jobDescription),
    enabled: enabled && jobDescription.length >= 50,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  })
}
