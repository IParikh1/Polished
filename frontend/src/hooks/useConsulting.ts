import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as consultApi from '../api/consultClient'

export function useConsultingSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['consulting-session', sessionId],
    queryFn: () => consultApi.getSession(sessionId!),
    enabled: !!sessionId,
  })
}

export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: consultApi.createSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['consulting-sessions'] })
    },
  })
}

export function useAnalyzeResume() {
  return useMutation({
    mutationFn: ({
      sessionId,
      analysisType,
    }: {
      sessionId: string
      analysisType?: 'comprehensive' | 'quick' | 'targeted'
    }) => consultApi.analyzeResume(sessionId, analysisType),
  })
}

export function useRewriteSection() {
  return useMutation({
    mutationFn: ({
      sessionId,
      section,
      options,
    }: {
      sessionId: string
      section: 'summary' | 'experience' | 'skills'
      options?: { context?: string; tone?: 'professional' | 'creative' | 'technical' }
    }) => consultApi.rewriteSection(sessionId, section, options),
  })
}

export function useChatMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, message }: { sessionId: string; message: string }) =>
      consultApi.sendChatMessage(sessionId, message),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['chat-history', sessionId] })
    },
  })
}

export function useChatHistory(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['chat-history', sessionId],
    queryFn: () => consultApi.getChatHistory(sessionId!),
    enabled: !!sessionId,
  })
}
