import { useNavigate, useLocation } from 'react-router-dom'

const NAV_LINKS = [
  { label: 'Investigate', path: '/' },
  { label: 'Dashboard',   path: '/dashboard' },
  { label: 'Score claim', path: '/score' },
  { label: 'Evaluation',  path: '/eval' },
]

export default function NavBar() {
  const navigate = useNavigate()
  const location = useLocation()
  return (
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
  )
}
