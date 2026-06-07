import { useState, useCallback, useEffect } from 'react'
import { Search, Loader2, AlertCircle, Wand2, ChevronDown, Check, ChevronRight, X, BarChart2, Download, Clock } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useInvestigation } from '../hooks/useInvestigation'
import { api } from '../api/client'

const SAMPLE_QUERIES = {
  high: [
    'No police report, external agent, urban area, high vehicle price',
    'New policy claims filed within a week of inception',
    'Multiple prior claims, address changes near claim, no witnesses',
  ],
  medium: [
    'Policy holder at fault, weekend accident, excess supplements filed',
    'Old vehicle high price claim, no witnesses, external agent handling',
    'Urban collision, prior claims history, rapid filing after accident',
  ],
  low: [
    'Rural collision, police report filed, witnesses present, internal agent',
    'Single vehicle accident, police report filed, internal agent, no supplements',
    'Internal agent, no prior claims, no address changes, rural area',
  ],
}

type RiskFilter = 'high' | 'medium' | 'low'

const DOT_COLORS: Record<RiskFilter, string> = {
  high: '#EF4444', medium: '#F59E0B', low: '#22C55E',
}

const TAB_STYLES: Record<RiskFilter, { base: string; active: string }> = {
  high:   { base: 'text-red-600 bg-red-50 border-red-200',     active: 'bg-red-600 text-white border-red-600' },
  medium: { base: 'text-amber-600 bg-amber-50 border-amber-200', active: 'bg-amber-600 text-white border-amber-600' },
  low:    { base: 'text-green-700 bg-green-50 border-green-200', active: 'bg-green-700 text-white border-green-700' },
}

const STEPS = [
  { key: 'retrieval',         label: 'Retrieving claims',  sub: 'Hybrid semantic + keyword' },
  { key: 'fraud_analysis',    label: 'Fraud analysis',     sub: 'Rule engine + stats' },
  { key: 'policy_validation', label: 'Policy validation',  sub: 'Compliance checks' },
  { key: 'recommendation',    label: 'Recommendation',     sub: 'GPT-4o-mini synthesis' },
]

const NAV_LINKS = [
  { label: 'Investigate', path: '/' },
  { label: 'Dashboard',   path: '/dashboard' },
  { label: 'Score claim', path: '/score' },
  { label: 'Evaluation',  path: '/eval' },
]

const HISTORY_KEY = 'insuriq_investigation_history'
const MAX_HISTORY = 5

interface HistoryItem {
  query: string
  risk_score: number
  risk_level: string
  timestamp: string
}

// ── Animated Risk Ring ────────────────────────────────────────────────────────
function AnimatedRing({ score, level }: { score: number; level: string }) {
  const [displayed, setDisplayed] = useState(0)

  useEffect(() => {
    setDisplayed(0)
    let start = 0
    const step = score / 40
    const timer = setInterval(() => {
      start += step
      if (start >= score) {
        setDisplayed(score)
        clearInterval(timer)
      } else {
        setDisplayed(Math.round(start))
      }
    }, 16)
    return () => clearInterval(timer)
  }, [score])

  const getRingColor = (l: string) =>
    l === 'HIGH' ? 'border-red-500' : l === 'MEDIUM' ? 'border-amber-500' : 'border-green-500'
  const getTextColor = (l: string) =>
    l === 'HIGH' ? 'text-red-600' : l === 'MEDIUM' ? 'text-amber-600' : 'text-green-700'

  return (
    <div className={`w-16 h-16 rounded-full border-[5px] flex flex-col items-center justify-center transition-all duration-300 ${getRingColor(level)}`}
      style={{ boxShadow: level === 'HIGH' ? '0 0 12px rgba(239,68,68,0.2)' : level === 'MEDIUM' ? '0 0 12px rgba(245,158,11,0.2)' : '0 0 12px rgba(34,197,94,0.2)' }}>
      <span className={`text-xl font-bold leading-none ${getTextColor(level)}`}>{displayed}</span>
      <span className="text-[9px] text-slate-400">/100</span>
    </div>
  )
}

// ── Loading Skeleton ──────────────────────────────────────────────────────────
function SkeletonPulse({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-gray-100 rounded ${className}`} />
  )
}

function InvestigationSkeleton() {
  return (
    <div className="flex flex-col gap-2.5">
      <div className="bg-white border border-gray-100 rounded-xl p-3">
        <SkeletonPulse className="h-3 w-32 mb-3" />
        <SkeletonPulse className="h-4 w-full mb-1.5" />
        <SkeletonPulse className="h-4 w-3/4" />
        <div className="flex gap-2 mt-3">
          {[1,2,3,4].map(i => <SkeletonPulse key={i} className="h-3 w-16" />)}
        </div>
      </div>
      <div className="bg-white border border-gray-100 rounded-xl p-3">
        <SkeletonPulse className="h-3 w-40 mb-3" />
        {[1,2,3,4,5].map(i => (
          <div key={i} className="flex items-center gap-2 py-1.5 border-b border-gray-50 last:border-0">
            <SkeletonPulse className="h-3 w-20" />
            <SkeletonPulse className="h-3 flex-1" />
            <SkeletonPulse className="h-3 w-12" />
            <SkeletonPulse className="h-3 w-16" />
            <SkeletonPulse className="h-3 w-8" />
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Claim Detail Drawer ───────────────────────────────────────────────────────
function ClaimDrawer({ claim, onClose }: { claim: any; onClose: () => void }) {
  const isfraud = claim.fraud_found_p === 1
  const fields = [
    { label: 'Policy number',    value: claim.policy_number },
    { label: 'Make',             value: claim.make },
    { label: 'Vehicle category', value: claim.vehicle_category },
    { label: 'Vehicle price',    value: claim.vehicle_price },
    { label: 'Age of vehicle',   value: claim.age_of_vehicle },
    { label: 'Accident area',    value: claim.accident_area },
    { label: 'Base policy',      value: claim.base_policy },
    { label: 'Fault',            value: claim.fault },
    { label: 'Police report',    value: claim.police_report_filed },
    { label: 'Witness present',  value: claim.witness_present },
    { label: 'Agent type',       value: claim.agent_type },
    { label: 'Past claims',      value: claim.past_number_of_claims },
    { label: 'Supplements',      value: claim.number_of_suppliments },
    { label: 'Address change',   value: claim.address_change_claim },
    { label: 'Days policy→accident', value: claim.days_policy_accident },
    { label: 'Fraud risk score', value: claim.fraud_risk_score },
    { label: 'Relevance',        value: claim.final_relevance_score ? `${Math.round(claim.final_relevance_score * 100)}%` : '-' },
  ]

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 mt-1 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[12px] font-semibold text-slate-700">Policy #{claim.policy_number} — Full details</span>
          <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${isfraud ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-700'}`}>
            {isfraud ? 'Fraud confirmed' : 'Legitimate'}
          </span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="grid grid-cols-3 gap-2 mb-3">
        {fields.map(f => (
          <div key={f.label} className="bg-gray-50 rounded-lg px-2.5 py-2">
            <div className="text-[9px] text-slate-400 font-medium uppercase tracking-wide mb-0.5">{f.label}</div>
            <div className="text-[11px] text-slate-700 font-medium">{f.value ?? '—'}</div>
          </div>
        ))}
      </div>
      {claim.fraud_signals?.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">Fraud signals</p>
          <div className="flex flex-wrap gap-1.5">
            {claim.fraud_signals.map((sig: string) => (
              <span key={sig} className="text-[9px] px-1.5 py-0.5 rounded bg-red-50 text-red-600 font-medium">{sig}</span>
            ))}
          </div>
        </div>
      )}
      {claim.claim_narrative && (
        <div>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">Claim narrative</p>
          <p className="text-[11px] text-slate-500 leading-relaxed bg-gray-50 rounded-lg p-3">{claim.claim_narrative}</p>
        </div>
      )}
    </div>
  )
}

// ── Query Intelligence Charts ─────────────────────────────────────────────────
function QueryIntelligenceCharts({ result }: { result: any }) {
  if (!result?.retrieved_claims?.length) return null
  const claims = result.retrieved_claims
  const sigFreq: Record<string, number> = {}
  claims.forEach((c: any) => {
    (c.fraud_signals || []).forEach((s: string) => {
      sigFreq[s] = (sigFreq[s] || 0) + 1
    })
  })
  const topSignals = Object.entries(sigFreq).sort(([,a],[,b]) => b - a).slice(0, 6)
  const total = claims.length
  const fraudCount = claims.filter((c: any) => c.fraud_found_p === 1).length
  const maxFreq = topSignals[0]?.[1] || 1

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-3">
      <div className="flex items-center gap-1.5 mb-3">
        <BarChart2 className="w-3.5 h-3.5 text-slate-400" />
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest">Query intelligence</p>
      </div>
      <div className="grid grid-cols-3 gap-3 mb-3">
        {[
          { val: `${fraudCount}/${total}`, label: 'Fraud confirmed', color: fraudCount === total ? 'text-red-600' : fraudCount === 0 ? 'text-green-700' : 'text-amber-600' },
          { val: result.risk_score, label: 'Risk score', color: result.risk_score >= 70 ? 'text-red-600' : result.risk_score >= 40 ? 'text-amber-600' : 'text-green-700' },
          { val: result.fraud_signals?.length || 0, label: 'Signals detected', color: 'text-slate-700' },
        ].map(item => (
          <div key={item.label} className="bg-gray-50 rounded-lg p-2 text-center">
            <div className={`text-lg font-bold ${item.color}`}>{item.val}</div>
            <div className="text-[9px] text-slate-400 mt-0.5">{item.label}</div>
          </div>
        ))}
      </div>
      {topSignals.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Signal frequency across retrieved claims</p>
          <div className="flex flex-col gap-1.5">
            {topSignals.map(([sig, freq]) => (
              <div key={sig} className="flex items-center gap-2">
                <div className="text-[9px] text-slate-500 font-medium" style={{ minWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {sig.replace(/_/g, ' ')}
                </div>
                <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                  <div className="h-full rounded-full bg-red-400 transition-all duration-700"
                    style={{ width: `${(freq / maxFreq) * 100}%` }} />
                </div>
                <div className="text-[10px] text-slate-500 font-medium min-w-[24px] text-right">{freq}/{total}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="mt-3">
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">Retrieved claim outcomes</p>
        <div className="flex h-4 rounded-full overflow-hidden gap-0.5">
          {claims.map((c: any, i: number) => (
            <div key={i} className={`flex-1 rounded-sm ${c.fraud_found_p === 1 ? 'bg-red-400' : 'bg-green-400'}`}
              title={`Policy #${c.policy_number}: ${c.fraud_found_p === 1 ? 'Fraud' : 'Legit'}`} />
          ))}
        </div>
        <div className="flex items-center gap-3 mt-1.5">
          <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-sm bg-red-400" /><span className="text-[9px] text-slate-400">Fraud confirmed ({fraudCount})</span></div>
          <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-sm bg-green-400" /><span className="text-[9px] text-slate-400">Legitimate ({total - fraudCount})</span></div>
        </div>
      </div>
    </div>
  )
}

// ── Export PDF ────────────────────────────────────────────────────────────────
function ExportButton({ result }: { result: any }) {
  const handleExport = () => {
    const content = `
InsurIQ — Investigation Report
================================
Generated: ${new Date().toLocaleString()}
Query: ${result.query}

RISK ASSESSMENT
---------------
Risk Score:  ${result.risk_score}/100
Risk Level:  ${result.risk_level}
Confidence:  ${Math.round((result.confidence || 0) * 100)}%

FRAUD SIGNALS DETECTED (${result.fraud_signals?.length || 0})
------------------------------
${(result.fraud_signals || []).map((s: string) => `• ${s}`).join('\n')}

STATISTICAL ANOMALIES
---------------------
${(result.statistical_flags || []).map((f: string) => `• ${f}`).join('\n')}

POLICY ISSUES
-------------
${(result.policy_issues || []).map((i: string) => `• ${i}`).join('\n')}

AI RECOMMENDATION
-----------------
${result.recommendation}

ACTION STEPS
------------
${(result.action_steps || []).map((s: string, i: number) => `${i+1}. ${s}`).join('\n')}

SIMILAR HISTORICAL CLAIMS
--------------------------
${(result.retrieved_claims || []).map((c: any) =>
  `Policy #${c.policy_number} | ${c.vehicle_category} | ${c.accident_area} | Score: ${c.fraud_risk_score} | ${c.fraud_found_p === 1 ? 'FRAUD' : 'LEGIT'}`
).join('\n')}

---
Trace ID: ${result.trace_id}
InsurIQ v1.0.0 — AI-Powered Insurance Claims Intelligence System
    `.trim()

    const blob = new Blob([content], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `insuriq-report-${result.trace_id?.slice(0,8)}-${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <button onClick={handleExport}
      className="flex items-center gap-1.5 text-[11px] text-slate-500 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 hover:text-slate-700 transition-colors">
      <Download className="w-3.5 h-3.5" />
      Export report
    </button>
  )
}

// ── Score History ─────────────────────────────────────────────────────────────
function ScoreHistory({ onSelect }: { onSelect: (q: string) => void }) {
  const [history, setHistory] = useState<HistoryItem[]>([])

  useEffect(() => {
    try {
      const stored = localStorage.getItem(HISTORY_KEY)
      if (stored) setHistory(JSON.parse(stored))
    } catch {}
  }, [])

  if (!history.length) return null

  const getRiskColor = (level: string) =>
    level === 'HIGH' ? 'text-red-600 bg-red-50' : level === 'MEDIUM' ? 'text-amber-600 bg-amber-50' : 'text-green-700 bg-green-50'

  return (
    <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
      <div className="flex items-center px-3 py-2 border-b border-gray-50">
        <Clock className="w-3.5 h-3.5 text-slate-400 mr-1.5" />
        <span className="text-[11px] font-semibold text-slate-500">Recent investigations</span>
        <button onClick={() => { localStorage.removeItem(HISTORY_KEY); setHistory([]) }}
          className="ml-auto text-[10px] text-slate-400 hover:text-slate-600">Clear</button>
      </div>
      <div className="flex flex-col">
        {history.map((item, i) => (
          <button key={i} onClick={() => onSelect(item.query)}
            className={`flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 transition-colors ${i < history.length - 1 ? 'border-b border-gray-50' : ''}`}>
            <span className="text-[11px] text-slate-600 flex-1 truncate">{item.query}</span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium flex-shrink-0 ${getRiskColor(item.risk_level)}`}>
              {item.risk_score}
            </span>
            <span className="text-[9px] text-slate-400 flex-shrink-0">{item.timestamp}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function saveToHistory(query: string, risk_score: number, risk_level: string) {
  try {
    const stored = localStorage.getItem(HISTORY_KEY)
    const history: HistoryItem[] = stored ? JSON.parse(stored) : []
    const newItem: HistoryItem = {
      query,
      risk_score,
      risk_level,
      timestamp: new Date().toLocaleTimeString(),
    }
    const updated = [newItem, ...history.filter(h => h.query !== query)].slice(0, MAX_HISTORY)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated))
  } catch {}
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function InvestigationPage() {
  const navigate  = useNavigate()
  const location  = useLocation()

  const [query, setQuery]               = useState('')
  const [regionFilter, setRegionFilter] = useState('')
  const [policyFilter, setPolicyFilter] = useState('')
  const [useRewriting, setUseRewriting] = useState(false)
  const [samplesOpen, setSamplesOpen]   = useState(false)
  const [riskFilter, setRiskFilter]     = useState<RiskFilter>('high')
  const [feedbackSent, setFeedbackSent] = useState(false)
  const [expandedClaim, setExpandedClaim] = useState<number | null>(null)

  const { investigate, result, progress, isInvestigating, error } = useInvestigation()

  // Save to history when result arrives
  useEffect(() => {
    if (result?.risk_score !== undefined && result?.query) {
      saveToHistory(result.query, result.risk_score, result.risk_level)
    }
  }, [result])

  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!query.trim() || isInvestigating) return
    const filters: Record<string, string> = {}
    if (regionFilter) filters.accident_area = regionFilter
    if (policyFilter) filters.base_policy   = policyFilter
    setFeedbackSent(false)
    setSamplesOpen(false)
    setExpandedClaim(null)
    await investigate(query, Object.keys(filters).length ? filters : undefined, useRewriting)
  }, [query, regionFilter, policyFilter, useRewriting, isInvestigating, investigate])

  const handleSampleClick = (q: string) => { setQuery(q); setSamplesOpen(false) }
  const handleHistoryClick = (q: string) => { setQuery(q) }

  const handleTabClick = (f: RiskFilter, e: React.MouseEvent) => {
    e.stopPropagation()
    setRiskFilter(f)
    setSamplesOpen(true)
  }

  const handleFeedback = async (wasCorrect: boolean) => {
    if (!result || feedbackSent) return
    try {
      const first = result.retrieved_claims?.[0]
      if (first) await api.submitFeedback(first.policy_number, result.trace_id, wasCorrect)
      setFeedbackSent(true)
    } catch {}
  }

  const toggleClaim = (policyNum: number) => {
    setExpandedClaim(prev => prev === policyNum ? null : policyNum)
  }

  const getRiskColor = (l: string) => l === 'HIGH' ? 'text-red-600 bg-red-50 border-red-200' : l === 'MEDIUM' ? 'text-amber-600 bg-amber-50 border-amber-200' : 'text-green-700 bg-green-50 border-green-200'

  const completedAgents = result
    ? ['retrieval', 'fraud_analysis', 'policy_validation', 'recommendation']
    : progress?.completed_agents || []

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden"
      style={{ fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif' }}>

      {/* TOP NAV */}
      <nav className="h-11 bg-slate-900 flex items-center px-5 gap-0 flex-shrink-0 border-b border-slate-800">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 mr-6 hover:opacity-80 transition-opacity">
          <div className="w-2 h-2 rounded-full bg-blue-500" />
          <span className="text-sm font-semibold text-slate-100 tracking-tight">InsurIQ</span>
        </button>
        {NAV_LINKS.map(link => (
          <button key={link.path} onClick={() => navigate(link.path)}
            className={`text-xs px-3 py-1.5 rounded-md transition-colors ${
              location.pathname === link.path
                ? 'text-slate-100 bg-slate-700 font-medium'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}>
            {link.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-1.5 text-xs text-green-400">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
          15,420 claims indexed · live
        </div>
      </nav>

      {/* BODY */}
      <div className="flex-1 grid min-h-0 overflow-hidden" style={{ gridTemplateColumns: '196px 1fr 210px' }}>

        {/* LEFT */}
        <div className="bg-white border-r border-gray-100 p-3.5 flex flex-col overflow-hidden">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2.5">Investigation pipeline</p>
          <div className="flex flex-col mb-4">
            {STEPS.map((step, i) => {
              const done   = completedAgents.includes(step.key)
              const active = !done && isInvestigating && progress?.current_agent === step.key
              return (
                <div key={step.key} className="flex items-start gap-2.5 py-1.5 relative">
                  {i < STEPS.length - 1 && <div className="absolute left-[10px] top-7 w-px h-[calc(100%-14px)] bg-gray-100" />}
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 z-10 ${
                    done   ? 'bg-green-50 border-[1.5px] border-green-400' :
                    active ? 'bg-blue-50 border-[1.5px] border-blue-400'  :
                             'bg-gray-50 border border-gray-200'}`}>
                    {done   ? <Check className="w-2.5 h-2.5 text-green-600" /> :
                     active ? <Loader2 className="w-2.5 h-2.5 text-blue-500 animate-spin" /> :
                              <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />}
                  </div>
                  <div className="flex-1">
                    <p className={`text-[11px] font-semibold leading-tight ${done ? 'text-slate-700' : 'text-slate-400'}`}>{step.label}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">{step.sub}</p>
                  </div>
                </div>
              )
            })}
          </div>

          {result && (
            <>
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Query intelligence</p>
              <div className="grid grid-cols-2 gap-1.5 mb-4">
                {[
                  { val: `${result.retrieved_claims?.filter((c:any)=>c.fraud_found_p===1).length||0}/${result.retrieved_claims?.length||0}`, label:'Fraud confirmed', color:'text-red-600' },
                  { val: result.risk_score,                    label:'Risk score',    color:'text-slate-800' },
                  { val: result.fraud_signals?.length||0,      label:'Signals found', color:'text-slate-800' },
                  { val: result.retrieved_claims?.length||0,   label:'Retrieved',     color:'text-blue-600'  },
                ].map(item => (
                  <div key={item.label} className="bg-gray-50 border border-gray-100 rounded-lg p-2">
                    <div className={`text-base font-bold leading-none ${item.color}`}>{item.val}</div>
                    <div className="text-[9px] text-slate-400 mt-1 font-medium">{item.label}</div>
                  </div>
                ))}
              </div>
              <div className="mt-auto bg-gray-50 border border-gray-100 rounded-lg p-2.5">
                {[{k:'Trace ID',v:result.trace_id?.slice(0,12)+'...'},{k:'Cache',v:result.cache_hit?'hit':'miss'}].map(r=>(
                  <div key={r.k} className="flex justify-between mb-1 last:mb-0">
                    <span className="text-[10px] text-slate-400 font-medium">{r.k}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{r.v}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* CENTRE */}
        <div className="bg-gray-50 p-3.5 flex flex-col gap-2.5 overflow-y-auto overflow-x-hidden">

          {/* Query input */}
          <div className="bg-white border border-gray-100 rounded-xl p-3">
            <p className="text-[11px] font-semibold text-slate-500 mb-2 tracking-wide">Investigation query</p>
            <textarea value={query} onChange={e=>setQuery(e.target.value)}
              onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();handleSubmit()}}}
              placeholder="Describe the fraud pattern you want to investigate..."
              rows={2} disabled={isInvestigating}
              className="w-full bg-gray-50 border border-gray-100 rounded-lg px-3 py-2.5 text-[12px] text-slate-600 leading-relaxed resize-none focus:outline-none focus:border-blue-200 placeholder-slate-300" />
            <div className="flex items-center gap-2 mt-2.5 flex-nowrap">
              <select value={regionFilter} onChange={e=>setRegionFilter(e.target.value)} disabled={isInvestigating}
                className="bg-gray-50 border border-gray-100 rounded-md px-2 py-1 text-[11px] text-slate-500 focus:outline-none flex-shrink-0">
                <option value="">All areas</option>
                <option value="Urban">Urban</option>
                <option value="Rural">Rural</option>
              </select>
              <select value={policyFilter} onChange={e=>setPolicyFilter(e.target.value)} disabled={isInvestigating}
                className="bg-gray-50 border border-gray-100 rounded-md px-2 py-1 text-[11px] text-slate-500 focus:outline-none flex-shrink-0">
                <option value="">All policies</option>
                <option value="Collision">Collision</option>
                <option value="Liability">Liability</option>
                <option value="All Perils">All Perils</option>
              </select>
              <label className="flex items-center gap-1.5 cursor-pointer select-none flex-shrink-0">
                <div onClick={()=>setUseRewriting(!useRewriting)}
                  className={`w-7 h-4 rounded-full relative transition-colors cursor-pointer flex-shrink-0 ${useRewriting?'bg-blue-500':'bg-gray-200'}`}>
                  <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full shadow-sm transition-all ${useRewriting?'right-0.5':'left-0.5'}`} />
                </div>
                <span className="text-[11px] text-slate-500 flex items-center gap-1 whitespace-nowrap">
                  <Wand2 className="w-3 h-3" />AI rewriting
                </span>
              </label>
              <button onClick={()=>handleSubmit()} disabled={isInvestigating||query.trim().length<5}
                className="ml-auto flex-shrink-0 flex items-center gap-1.5 bg-slate-900 text-white text-[12px] font-semibold px-4 py-1.5 rounded-lg disabled:opacity-40 hover:bg-slate-800 transition-colors">
                {isInvestigating?<Loader2 className="w-3.5 h-3.5 animate-spin"/>:<Search className="w-3.5 h-3.5"/>}
                Investigate
              </button>
            </div>
          </div>

          {/* Sample queries */}
          <div className="relative z-20">
            <div className="bg-white border border-gray-100 rounded-xl">
              <div className="flex items-center px-3 py-2 cursor-pointer gap-2" onClick={()=>setSamplesOpen(!samplesOpen)}>
                <span className="text-[11px] font-semibold text-slate-500">Sample queries</span>
                <div className="flex gap-1.5 ml-2" onClick={e=>e.stopPropagation()}>
                  {(['high','medium','low'] as RiskFilter[]).map(f=>(
                    <button key={f} onClick={e=>handleTabClick(f,e)}
                      className={`text-[10px] font-semibold px-2.5 py-1 rounded border transition-all capitalize ${riskFilter===f&&samplesOpen?TAB_STYLES[f].active:TAB_STYLES[f].base}`}>
                      {f.charAt(0).toUpperCase()+f.slice(1)}
                    </button>
                  ))}
                </div>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-300 ml-auto transition-transform duration-200 ${samplesOpen?'rotate-180':''}`} />
              </div>
              {samplesOpen && (
                <div className="px-3 pb-3 flex flex-col gap-1.5 bg-white rounded-b-xl border-t border-gray-50 shadow-md">
                  {SAMPLE_QUERIES[riskFilter].map((q,i)=>(
                    <button key={i} onClick={()=>handleSampleClick(q)}
                      className="flex items-center gap-2 text-left text-[11px] text-slate-500 px-3 py-2 rounded-lg bg-gray-50 border border-gray-100 hover:border-slate-200 hover:text-slate-700 transition-all w-full">
                      <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{background:DOT_COLORS[riskFilter]}} />
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Score history — shown when no active investigation */}
          {!isInvestigating && !result && (
            <ScoreHistory onSelect={handleHistoryClick} />
          )}

          {error && (
            <div className="flex items-start gap-2.5 p-3 bg-red-50 border border-red-100 rounded-xl">
              <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-red-600">{error}</p>
            </div>
          )}

          {/* Loading skeleton */}
          {isInvestigating && <InvestigationSkeleton />}

          {/* Query intelligence charts */}
          {result && <QueryIntelligenceCharts result={result} />}

          {/* AI Recommendation */}
          {result && (
            <div className="bg-white border border-gray-100 rounded-xl p-3">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest">AI recommendation</p>
                <ExportButton result={result} />
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed mb-2.5">{result.recommendation}</p>
              {result.action_steps?.length>0 && (
                <>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">Action steps</p>
                  {result.action_steps.slice(0,4).map((step:string,i:number)=>(
                    <div key={i} className="flex items-start gap-2 py-0.5">
                      <div className="w-4 h-4 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-[9px] text-slate-400 font-semibold">{i+1}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 leading-snug">{step}</p>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}

          {/* Retrieved claims */}
          {result?.retrieved_claims?.length>0 && (
            <div className="bg-white border border-gray-100 rounded-xl p-3">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[11px] font-semibold text-slate-700">Similar historical claims</p>
                <p className="text-[10px] text-slate-400">{result.retrieved_claims.length} retrieved · click to expand</p>
              </div>
              {result.retrieved_claims.map((claim:any,i:number)=>(
                <div key={claim.policy_number}>
                  <div onClick={()=>toggleClaim(claim.policy_number)}
                    className={`flex items-center gap-1.5 py-1.5 cursor-pointer rounded px-1 transition-colors ${
                      expandedClaim===claim.policy_number ? 'bg-blue-50 border border-blue-100' : 'hover:bg-gray-50 border border-transparent'
                    } ${i<result.retrieved_claims.length-1&&expandedClaim!==claim.policy_number?'border-b border-gray-50':''}`}>
                    <ChevronRight className={`w-3 h-3 text-slate-400 flex-shrink-0 transition-transform ${expandedClaim===claim.policy_number?'rotate-90':''}`} />
                    <span className="text-[11px] font-semibold text-slate-600 min-w-[80px]">Policy #{claim.policy_number}</span>
                    <span className="text-[10px] text-slate-400 flex-1 whitespace-nowrap overflow-hidden">{claim.vehicle_category} · {claim.accident_area} · {Math.round((claim.final_relevance_score||0)*100)}%</span>
                    <div className="flex gap-1 overflow-hidden" style={{maxWidth:'160px'}}>
                      {(claim.fraud_signals||[]).slice(0,2).map((sig:string)=>(
                        <span key={sig} className="text-[9px] px-1.5 py-0.5 rounded bg-red-50 text-red-600 font-medium whitespace-nowrap">{sig}</span>
                      ))}
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-medium flex-shrink-0 ${claim.fraud_found_p===1?'bg-red-50 text-red-600':'bg-green-50 text-green-700'}`}>
                      {claim.fraud_found_p===1?'Fraud':'Legit'}
                    </span>
                    <span className="text-[10px] text-slate-400 min-w-[36px] text-right flex-shrink-0">{claim.fraud_risk_score}</span>
                  </div>
                  {expandedClaim===claim.policy_number && (
                    <ClaimDrawer claim={claim} onClose={()=>setExpandedClaim(null)} />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT */}
        <div className="bg-white border-l border-gray-100 p-3.5 flex flex-col gap-3 overflow-y-auto">
          <div>
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Fraud risk score</p>
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-3 text-center">
              {result ? (
                <>
                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded border uppercase tracking-wide inline-block mb-2 ${getRiskColor(result.risk_level)}`}>
                    {result.risk_level} risk
                  </span>
                  {/* ANIMATED RING */}
                  <div className="flex justify-center my-2">
                    <AnimatedRing score={result.risk_score} level={result.risk_level} />
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 mt-2">
                    {[{v:`${Math.round((result.confidence||0)*100)}%`,l:'Confidence'},{v:result.fraud_signals?.length||0,l:'Signals'}].map(item=>(
                      <div key={item.l} className="bg-white border border-gray-100 rounded-lg py-1.5 text-center">
                        <div className="text-sm font-bold text-slate-700">{item.v}</div>
                        <div className="text-[9px] text-slate-400 mt-0.5">{item.l}</div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="py-4">
                  <div className="w-16 h-16 rounded-full border-[5px] border-gray-200 flex items-center justify-center mx-auto mb-2">
                    <span className="text-slate-300 text-lg font-bold">—</span>
                  </div>
                  <p className="text-[11px] text-slate-300">Run investigation</p>
                </div>
              )}
            </div>
          </div>

          {result?.fraud_signals?.length>0 && (
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">Fraud signals</p>
              <div className="flex flex-wrap gap-1">
                {result.fraud_signals.map((sig:string)=>(
                  <span key={sig} className="text-[9px] px-1.5 py-0.5 rounded bg-red-50 text-red-600 font-medium">{sig}</span>
                ))}
              </div>
            </div>
          )}

          {result?.statistical_flags?.length>0 && (
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">Statistical anomalies</p>
              {result.statistical_flags.slice(0,4).map((flag:string,i:number)=>(
                <div key={i} className={`text-[10px] text-slate-500 py-1.5 ${i<3?'border-b border-gray-50':''}`}>{flag}</div>
              ))}
            </div>
          )}

          {result?.policy_issues?.length>0 && (
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">Policy issues</p>
              <div className="bg-amber-50 border border-amber-100 rounded-lg p-2">
                {result.policy_issues.map((issue:string,i:number)=>(
                  <div key={i} className="flex items-start gap-1.5 py-0.5">
                    <AlertCircle className="w-2.5 h-2.5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <span className="text-[10px] text-amber-700">{issue}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result?.rewritten_query && (
            <div className="bg-purple-50 border border-purple-100 rounded-lg p-2.5">
              <p className="text-[10px] font-semibold text-purple-600 mb-1 flex items-center gap-1">
                <Wand2 className="w-3 h-3" />AI rewrote query
              </p>
              <p className="text-[10px] text-purple-500 italic leading-snug">"{result.rewritten_query}"</p>
            </div>
          )}

          <div className="mt-auto">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Analyst feedback</p>
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-2.5">
              <p className="text-[11px] text-slate-500 font-medium mb-2">Was this recommendation accurate?</p>
              {feedbackSent ? (
                <div className="flex items-center gap-1.5 text-[11px] text-green-600 font-medium">
                  <Check className="w-3.5 h-3.5" />Feedback recorded
                </div>
              ) : (
                <div className="flex gap-2">
                  <button onClick={()=>handleFeedback(true)} disabled={!result}
                    className="flex-1 py-1.5 rounded-lg border-[1.5px] border-green-300 bg-green-50 text-green-700 text-[11px] font-semibold disabled:opacity-30 hover:bg-green-100 transition-colors">
                    Yes, accurate
                  </button>
                  <button onClick={()=>handleFeedback(false)} disabled={!result}
                    className="flex-1 py-1.5 rounded-lg border-[1.5px] border-red-200 bg-red-50 text-red-600 text-[11px] font-semibold disabled:opacity-30 hover:bg-red-100 transition-colors">
                    No, incorrect
                  </button>
                </div>
              )}
              {result && <p className="text-[9px] text-slate-300 mt-1.5">Trace: {result.trace_id?.slice(0,16)}...</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
