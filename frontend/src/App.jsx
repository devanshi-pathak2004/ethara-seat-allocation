import { NavLink, Route, Routes } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  Armchair,
  FolderKanban,
  Sparkles,
  Building2,
} from 'lucide-react'
import Dashboard from './pages/Dashboard.jsx'
import Employees from './pages/Employees.jsx'
import Seats from './pages/Seats.jsx'
import Projects from './pages/Projects.jsx'
import Assistant from './pages/Assistant.jsx'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/employees', label: 'Employees', icon: Users },
  { to: '/seats', label: 'Seats', icon: Armchair },
  { to: '/projects', label: 'Projects', icon: FolderKanban },
  { to: '/assistant', label: 'AI Assistant', icon: Sparkles },
]

function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
      <div className="flex items-center gap-3 px-6 py-6">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-soft">
          <Building2 size={22} />
        </div>
        <div>
          <p className="text-base font-extrabold leading-tight text-slate-800">Ethara</p>
          <p className="text-xs text-slate-400">Seat Allocation</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition ${
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-5">
        <div className="rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 p-4 text-white">
          <p className="text-sm font-bold">Need a seat?</p>
          <p className="mt-1 text-xs text-brand-100">
            Ask the AI Assistant anything about seats & projects.
          </p>
        </div>
      </div>
    </aside>
  )
}

function MobileNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 flex justify-around border-t border-slate-200 bg-white/95 backdrop-blur lg:hidden">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[11px] font-semibold ${
              isActive ? 'text-brand-700' : 'text-slate-400'
            }`
          }
        >
          <Icon size={20} />
          {label.split(' ')[0]}
        </NavLink>
      ))}
    </nav>
  )
}

export default function App() {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className="pb-20 lg:pb-8 lg:pl-64">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/seats" element={<Seats />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/assistant" element={<Assistant />} />
          </Routes>
        </div>
      </main>
      <MobileNav />
    </div>
  )
}
