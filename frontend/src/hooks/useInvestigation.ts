import { useState, useCallback } from 'react'
import { api } from '../api/client'

export function useInvestigation() {
  const [result, setResult] = useState<any>(null)
  const [progress, setProgress] = useState<any>(null)
  const [isInvestigating, setInvestigating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const investigate = useCallback(async (
    query: string,
    filters?: Record<string, string>,
    useQueryRewriting = false,
  ) => {
    setInvestigating(true)
    setError(null)
    setResult(null)
    setProgress({ completed_agents: [], current_agent: 'starting' })
    try {
      const response = await api.investigate(query, filters, useQueryRewriting)
      setResult(response.data)
      setProgress({
        completed_agents: ['retrieval', 'fraud_analysis', 'policy_validation', 'recommendation'],
        current_agent: 'done',
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Investigation failed')
    } finally {
      setInvestigating(false)
    }
  }, [])

  return { investigate, result, progress, isInvestigating, error }
}
