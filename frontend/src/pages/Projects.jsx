import { useEffect, useState } from 'react'
import { FolderKanban, Users, Armchair, UserCircle2 } from 'lucide-react'
import { api } from '../lib/api'
import { Spinner, Modal, Badge } from '../components/ui'

const GRADIENTS = [
  'from-indigo-500 to-violet-600',
  'from-sky-500 to-blue-600',
  'from-emerald-500 to-teal-600',
  'from-amber-500 to-orange-600',
  'from-rose-500 to-pink-600',
  'from-fuchsia-500 to-purple-600',
  'from-cyan-500 to-sky-600',
  'from-lime-500 to-green-600',
]

export default function Projects() {
  const [projects, setProjects] = useState(null)
  const [util, setUtil] = useState({})
  const [active, setActive] = useState(null)
  const [members, setMembers] = useState(null)

  useEffect(() => {
    api.projects().then(setProjects)
    api.projectUtilization().then((rows) => {
      const map = {}
      rows.forEach((r) => (map[r.project_id] = r))
      setUtil(map)
    })
  }, [])

  const open = async (p) => {
    setActive(p)
    setMembers(null)
    const res = await api.projectEmployees(p.id)
    setMembers(res.items)
  }

  if (!projects) return <Spinner label="Loading projects…" />

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-800">Projects</h1>
        <p className="text-sm text-slate-500">{projects.length} active projects at Ethara.</p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((p, i) => {
          const u = util[p.id] || { employees: 0, allocated_seats: 0 }
          return (
            <button
              key={p.id}
              onClick={() => open(p)}
              className="card group p-5 text-left transition hover:shadow-soft"
            >
              <div className="flex items-center justify-between">
                <div className={`grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br ${GRADIENTS[i % GRADIENTS.length]} text-white shadow-soft`}>
                  <FolderKanban size={20} />
                </div>
                <Badge status="Active">{p.status}</Badge>
              </div>
              <h3 className="mt-4 text-lg font-bold text-slate-800 group-hover:text-brand-700">{p.name}</h3>
              <p className="text-xs text-slate-400">Manager · {p.manager_name}</p>
              <div className="mt-4 flex gap-4 border-t border-slate-100 pt-3 text-sm">
                <span className="inline-flex items-center gap-1.5 text-slate-600">
                  <Users size={15} className="text-brand-500" /> {u.employees.toLocaleString()} <span className="text-slate-400">emp</span>
                </span>
                <span className="inline-flex items-center gap-1.5 text-slate-600">
                  <Armchair size={15} className="text-emerald-500" /> {u.allocated_seats.toLocaleString()} <span className="text-slate-400">seats</span>
                </span>
              </div>
            </button>
          )
        })}
      </div>

      <Modal open={!!active} onClose={() => setActive(null)} title={active ? `${active.name} · Team` : ''} width="max-w-2xl">
        {active && (
          <div>
            <p className="mb-3 text-sm text-slate-500">{active.description}</p>
            {members === null ? (
              <Spinner label="Loading team…" />
            ) : (
              <div className="max-h-[55vh] overflow-y-auto">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  {members.length} members
                </p>
                <ul className="divide-y divide-slate-50">
                  {members.slice(0, 100).map((m) => (
                    <li key={m.id} className="flex items-center justify-between py-2.5">
                      <div className="flex items-center gap-3">
                        <UserCircle2 size={30} className="text-slate-300" />
                        <div>
                          <p className="text-sm font-semibold text-slate-700">{m.name}</p>
                          <p className="text-xs text-slate-400">{m.role}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        {m.seat ? (
                          <p className="text-xs font-semibold text-brand-600">
                            F{m.seat.floor}·{m.seat.zone}·{m.seat.seat_number}
                          </p>
                        ) : (
                          <Badge status="Pending" />
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
                {members.length > 100 && (
                  <p className="pt-3 text-center text-xs text-slate-400">
                    Showing first 100 of {members.length} members.
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
