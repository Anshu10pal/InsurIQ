import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend
} from 'recharts'
import { AlertCircle, TrendingUp, Shield, AlertTriangle, RefreshCw } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { api } from '../api/client'

const NAV_LINKS = [
  { label: 'Investigate', path: '/' },
  { label: 'Dashboard',   path: '/dashboard' },
  { label: 'Score claim', path: '/score' },
  { label: 'Evaluation',  path: '/eval' },
]

const COLORS = ['#EF4444', '#F59E0B', '#22C55E', '#3B82F6', '#8B5CF6', '#EC4899']

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-gray-100 rounded-lg px-3 py-2 shadow-sm">
      <p className="text-[11px] font-semibold text-slate-700 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-[11px]" style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' && p.name?.includes('%') ? `${p.value}%` : p.value?.toLocaleString()}
        </p>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const [stats, setStats]     = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  const loadStats = () => {
    setLoading(true)
    setError(null)
    api.getDashboardStats()
      .then(r => setStats(r.data))
      .catch(() => setError('Failed to load dashboard stats'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadStats() }, [])

  const riskDist = stats ? [
    { name: 'High risk',   value: stats.summary.high_risk_count,   color: '#EF4444' },
    { name: 'Medium risk', value: stats.summary.medium_risk_count, color: '#F59E0B' },
    { name: 'Low risk',    value: stats.summary.low_risk_count,    color: '#22C55E' },
  ] : []

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden"
      style={{ fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif' }}>

      {/* NAV */}
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

      <div className="flex-1 overflow-y-auto p-5">
        <div className="max-w-6xl mx-auto">

          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div>
              <h1 className="text-lg font-semibold text-slate-800">Fraud analytics dashboard</h1>
              <p className="text-[12px] text-slate-500 mt-0.5">Overview of all 15,420 claims across the dataset</p>
            </div>
            <button onClick={loadStats} disabled={loading}
              className="flex items-center gap-1.5 text-[11px] text-slate-500 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors disabled:opacity-40">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-3" />
              <span className="text-[12px] text-slate-500">Loading dashboard data...</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-100 rounded-xl mb-4">
              <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
              <p className="text-[12px] text-red-600">{error}</p>
            </div>
          )}

          {stats && (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-4 gap-3 mb-5">
                {[
                  { label: 'Total claims',  value: stats.summary.total_claims.toLocaleString(),   icon: Shield,        color: 'text-blue-600',  bg: 'bg-blue-50'  },
                  { label: 'Fraud rate',    value: `${stats.summary.fraud_rate}%`,                 icon: TrendingUp,    color: 'text-red-600',   bg: 'bg-red-50'   },
                  { label: 'High risk',     value: stats.summary.high_risk_count.toLocaleString(), icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50' },
                  { label: 'Fraud claims',  value: stats.summary.fraud_claims.toLocaleString(),    icon: AlertCircle,   color: 'text-red-600',   bg: 'bg-red-50'   },
                ].map(item => (
                  <div key={item.label} className="bg-white border border-gray-100 rounded-xl p-4">
                    <div className={`w-8 h-8 rounded-lg ${item.bg} flex items-center justify-center mb-2`}>
                      <item.icon className={`w-4 h-4 ${item.color}`} />
                    </div>
                    <div className={`text-xl font-bold ${item.color}`}>{item.value}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5 font-medium">{item.label}</div>
                  </div>
                ))}
              </div>

              {/* Row 1 — area + risk distribution */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-white border border-gray-100 rounded-xl p-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Fraud rate by accident area</p>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={stats.fraud_by_area}>
                      <XAxis dataKey="area" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="fraud_rate" name="Fraud %" fill="#EF4444" radius={[4,4,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-white border border-gray-100 rounded-xl p-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Risk level distribution</p>
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie data={riskDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70}
                        label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
                        labelLine={false}>
                        {riskDist.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Row 2 — agent type + day of week */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-white border border-gray-100 rounded-xl p-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Fraud rate by agent type</p>
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={stats.fraud_by_agent} layout="vertical">
                      <XAxis type="number" tick={{ fontSize: 11 }} unit="%" />
                      <YAxis dataKey="agent" type="category" tick={{ fontSize: 11 }} width={65} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="fraud_rate" name="Fraud %" fill="#8B5CF6" radius={[0,4,4,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-[10px] text-slate-400 mt-2 text-center">External agents show 2× higher fraud rate than internal</p>
                </div>

                <div className="bg-white border border-gray-100 rounded-xl p-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Fraud rate by day of week</p>
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={stats.fraud_by_day}>
                      <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="fraud_rate" name="Fraud %" radius={[4,4,0,0]}>
                        {stats.fraud_by_day.map((_: any, i: number) => (
                          <Cell key={i} fill={['Sat','Sun'].includes(stats.fraud_by_day[i]?.day) ? '#EF4444' : '#3B82F6'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-[10px] text-slate-400 mt-2 text-center">Weekends (red) show elevated fraud patterns</p>
                </div>
              </div>

              {/* Row 3 — vehicle + policy duration */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-white border border-gray-100 rounded-xl p-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Fraud rate by vehicle category</p>
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={stats.fraud_by_vehicle}>
                      <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="fraud_rate" name="Fraud %" radius={[4,4,0,0]}>
                        {stats.fraud_by_vehicle.map((_: any, i: number) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-white border border-gray-100 rounded-xl p-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Fraud rate by policy duration before accident</p>
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={stats.fraud_by_policy_duration}>
                      <XAxis dataKey="duration" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="fraud_rate" name="Fraud %" radius={[4,4,0,0]}>
                        {stats.fraud_by_policy_duration.map((d: any, i: number) => (
                          <Cell key={i} fill={d.fraud_rate > 10 ? '#EF4444' : d.fraud_rate > 6 ? '#F59E0B' : '#22C55E'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-[10px] text-slate-400 mt-2 text-center">New policies (none/1-7 days) have highest fraud rates</p>
                </div>
              </div>

              {/* Row 4 — top signals + claims by year */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-white border border-gray-100 rounded-xl p-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Top fraud signals across confirmed fraud cases</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={stats.top_fraud_signals} layout="vertical">
                      <XAxis type="number" tick={{ fontSize: 10 }} />
                      <YAxis dataKey="signal" type="category" tick={{ fontSize: 9 }} width={140} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="count" name="Count" fill="#EF4444" radius={[0,4,4,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-white border border-gray-100 rounded-xl p-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Claims and fraud trend by year</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={stats.claims_by_year}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                      <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Line yAxisId="left" type="monotone" dataKey="total" name="Total claims" stroke="#3B82F6" strokeWidth={2} dot={{ r: 3 }} />
                      <Line yAxisId="right" type="monotone" dataKey="fraud_rate" name="Fraud %" stroke="#EF4444" strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Top high risk claims */}
              <div className="bg-white border border-gray-100 rounded-xl p-4">
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Top high risk claims</p>
                <div className="flex flex-col">
                  {stats.high_risk_claims.slice(0, 8).map((claim: any, i: number) => (
                    <div key={claim.policy_number}
                      className={`flex items-center gap-3 py-2 ${i < 7 ? 'border-b border-gray-50' : ''}`}>
                      <span className="text-[11px] font-semibold text-slate-600 min-w-[90px]">Policy #{claim.policy_number}</span>
                      <span className="text-[10px] text-slate-400 flex-1">{claim.vehicle_category} · {claim.accident_area}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-medium flex-shrink-0 ${claim.fraud_found_p === 1 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-700'}`}>
                        {claim.fraud_found_p === 1 ? 'Fraud' : 'Legit'}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full bg-red-500 rounded-full"
                            style={{ width: `${claim.fraud_risk_score}%` }} />
                        </div>
                        <span className="text-[11px] font-bold text-red-600 min-w-[28px]">{claim.fraud_risk_score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
