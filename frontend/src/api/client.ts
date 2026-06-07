import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = {
  investigate: (query: string, filters?: Record<string, string>, useQueryRewriting = false) =>
    axios.post(`${BASE_URL}/claims/investigate`, { query, filters, use_query_rewriting: useQueryRewriting }),

  getDashboardStats: () => axios.get(`${BASE_URL}/dashboard/stats`),

  submitFeedback: (policyNumber: number, traceId: string, wasCorrect: boolean, notes?: string) =>
    axios.post(`${BASE_URL}/claims/feedback`, {
      policy_number: policyNumber, trace_id: traceId, was_correct: wasCorrect, analyst_notes: notes,
    }),

  scoreNewClaim: (claimData: Record<string, any>) =>
    axios.post(`${BASE_URL}/fraud/score-new-claim`, claimData),

  searchClaims: (q: string, topK = 5) =>
    axios.get(`${BASE_URL}/retrieve/search`, { params: { q, top_k: topK } }),

  runEval: () => axios.post(`${BASE_URL}/eval/run`),
  getEvalResults: () => axios.get(`${BASE_URL}/eval/results`),
  getEvalStatus: (runId: string) => axios.get(`${BASE_URL}/eval/status/${runId}`),
}
