import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { api } from '../api/client'

const NAV_LINKS = [
  { label: 'Investigate', path: '/' },
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Score claim', path: '/score' },
  { label: 'Evaluation', path: '/eval' },
]

const CLEAN_PRESET = {
  vehicle_category: 'Sedan', vehicle_price: 'less than 20000', age_of_vehicle: '4 years',
  accident_area: 'Rural', fault: 'Third Party', base_policy: 'Liability',
  police_report_filed: 'Yes', witness_present: 'Yes', agent_type: 'Internal',
  days_policy_accident: 'more than 30', days_policy_claim: 'more than 30',
  past_number_of_claims: 'none', number_of_supplements: 'none',
  address_change_claim: 'no change', number_of_cars: '1 vehicle',
  day_of_week: 'Wednesday', driver_rating: 1, deductible: 400,
}

const SUSPICIOUS_PRESET = {
  vehicle_category: 'Utility', vehicle_price: 'more than 69000', age_of_vehicle: 'more than 7',
  accident_area: 'Urban', fault: 'Policy Holder', base_policy: 'All Perils',
  police_report_filed: 'No', witness_present: 'No', agent_type: 'External',
  days_policy_accident: '1 to 7', days_policy_claim: '1 to 7',
  past_number_of_claims: 'more than 4', number_of_supplements: 'more than 5',
  address_change_claim: 'under 6 months', number_of_cars: '3 to 4',
  day_of_week: 'Saturday', driver_rating: 4, deductible: 300,
}

export default function ScoreClaimPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState<any>(CLEAN_PRESET)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleScore = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.scoreNewClaim(form)
      setResult(resp.data)
    } catch (e: any) {
      setError(e.message || 'Scoring failed')
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (level: string) =>
    level === 'HIGH' ? 'text-red-600' : level === 'MEDIUM' ? 'text-amber-600' : 'text-green-700'

  const selectClass = "bg-gray-50 border border-gray-100 rounded-md px-2 py-1.5 text-[11px] text-slate-600 focus:outline-none w-full"

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden"
      style={{ fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif' }}>
      <nav className="h-11 bg-slate-900 flex items-center px-5 gap-0 flex-shrink-0 border-b border-slate-800">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 mr-6 hover:opacity-80">
          <div className="w-2 h-2 rounded-full bg-blue-500" />
          <span className="text-sm font-semibold text-slate-100">InsurIQ</span>
        </button>
        {NAV_LINKS.map(link => (
          <button key={link.path} onClick={() => navigate(link.path)}
            className={`text-xs px-3 py-1.5 rounded-md transition-colors ${
              location.pathname === link.path ? 'text-slate-100 bg-slate-700 font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}>{link.label}</button>
        ))}
      </nav>

      <div className="flex-1 overflow-y-auto p-5">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h1 className="text-lg font-semibold text-slate-800">Score a new claim</h1>
              <p className="text-[12px] text-slate-500 mt-0.5">Instant deterministic scoring — no API required</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => { setForm(CLEAN_PRESET); setResult(null) }}
                className="text-[11px] px-3 py-1.5 rounded-lg border border-green-200 bg-green-50 text-green-700 hover:bg-green-100">
                Load clean preset
              </button>
              <button onClick={() => { setForm(SUSPICIOUS_PRESET); setResult(null) }}
                className="text-[11px] px-3 py-1.5 rounded-lg border border-red-200 bg-red-50 text-red-600 hover:bg-red-100">
                Load suspicious preset
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white border border-gray-100 rounded-xl p-4">
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Vehicle & Policy</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ['vehicle_category', 'Vehicle category', ['Sedan','Utility','Sport']],
                  ['vehicle_price', 'Vehicle price', ['less than 20000','20000 to 29000','30000 to 39000','40000 to 59000','60000 to 69000','more than 69000']],
                  ['age_of_vehicle', 'Age of vehicle', ['new','2 years','3 years','4 years','5 years','6 years','7 years','more than 7']],
                  ['base_policy', 'Base policy', ['Collision','Liability','All Perils']],
                  ['fault', 'Fault', ['Policy Holder','Third Party']],
                  ['accident_area', 'Accident area', ['Urban','Rural']],
                ].map(([key, label, options]) => (
                  <div key={key as string}>
                    <label className="text-[10px] text-slate-400 font-medium mb-0.5 block">{label as string}</label>
                    <select value={form[key as string]} onChange={e => setForm({...form, [key as string]: e.target.value})} className={selectClass}>
                      {(options as string[]).map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white border border-gray-100 rounded-xl p-4">
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Claim Details</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ['police_report_filed', 'Police report', ['Yes','No']],
                  ['witness_present', 'Witness present', ['Yes','No']],
                  ['agent_type', 'Agent type', ['Internal','External']],
                  ['days_policy_accident', 'Days policy→accident', ['none','1 to 7','8 to 15','15 to 30','more than 30']],
                  ['past_number_of_claims', 'Past claims', ['none','1','2 to 4','more than 4']],
                  ['number_of_supplements', 'Supplements', ['none','1 to 2','3 to 5','more than 5']],
                  ['address_change_claim', 'Address change', ['no change','under 6 months','1 year','2 to 3 years','4 to 8 years']],
                  ['day_of_week', 'Day of week', ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']],
                ].map(([key, label, options]) => (
                  <div key={key as string}>
                    <label className="text-[10px] text-slate-400 font-medium mb-0.5 block">{label as string}</label>
                    <select value={form[key as string]} onChange={e => setForm({...form, [key as string]: e.target.value})} className={selectClass}>
                      {(options as string[]).map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-4 flex justify-center">
            <button onClick={handleScore} disabled={loading}
              className="bg-slate-900 text-white text-[12px] font-semibold px-8 py-2.5 rounded-lg disabled:opacity-40 hover:bg-slate-800 transition-colors">
              {loading ? 'Scoring...' : 'Calculate fraud risk score'}
            </button>
          </div>

          {error && <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-xl text-[12px] text-red-600">{error}</div>}

          {result && (
            <div className="mt-4 bg-white border border-gray-100 rounded-xl p-4">
              <div className="flex items-center gap-4 mb-4">
                <div className={`text-3xl font-bold ${getRiskColor(result.risk_level)}`}>{result.risk_score}/100</div>
                <div>
                  <div className={`text-sm font-semibold px-3 py-1 rounded-full border ${
                    result.risk_level === 'HIGH' ? 'bg-red-50 text-red-600 border-red-200' :
                    result.risk_level === 'MEDIUM' ? 'bg-amber-50 text-amber-600 border-amber-200' :
                    'bg-green-50 text-green-700 border-green-200'
                  }`}>{result.risk_level} RISK</div>
                </div>
              </div>
              {result.fraud_signals?.length > 0 && (
                <div className="mb-3">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">Fraud signals</p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.fraud_signals.map((s: string) => (
                      <span key={s} className="text-[9px] px-2 py-0.5 rounded bg-red-50 text-red-600 font-medium">{s}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
