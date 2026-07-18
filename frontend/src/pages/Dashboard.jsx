import { useEffect, useState } from 'react'
import {
  Users,
  Armchair,
  CheckCircle2,
  CircleSlash,
  Bookmark,
  Wrench,
  UserPlus,
  Gauge,
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts'
import { api } from '../lib/api'
import { StatCard, Spinner } from '../components/ui'

const SEAT_COLORS = {
  Occupied: '#6366f1',
  Available: '#10b981',
  Reserved: '#f59e0b',
  Maintenance: '#f43f5e',
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [projects, setProjects] = useState([])
  const [floors, setFloors] = useState([])
  const [err, setErr] = useState(null)

  useEffect(() => {
    Promise.all([
      api.summary(),
      api.projectUtilization(),
      api.floorUtilization(),
    ])
      .then(([s, p, f]) => {
        setSummary(s)
        setProjects(p)
        setFloors(f)
      })
      .catch((e) => setErr(e.message))
  }, [])

  if (err)
    return (
      <div className="card p-6 text-rose-600">
        Could not reach the API at <code>{api.base}</code>. Is the backend running? ({err})
      </div>
    )
  if (!summary) return <Spinner label="Loading dashboard…" />

  const donut = [
    { name: 'Occupied', value: summary.occupied_seats },
    { name: 'Available', value: summary.available_seats },
    { name: 'Reserved', value: summary.reserved_seats },
    { name: 'Maintenance', value: summary.maintenance_seats },
  ]

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-800">
          Dashboard
        </h1>
        <p className="text-sm text-slate-500">
          Live overview of Ethara seating, projects and utilization.
        </p>
      </header>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <StatCard icon={Users} label="Total Employees" value={summary.total_employees.toLocaleString()} sub={`${summary.active_employees.toLocaleString()} active`} accent="brand" />
        <StatCard icon={Armchair} label="Total Seats" value={summary.total_seats.toLocaleString()} sub={`${summary.utilization_pct}% utilized`} accent="slate" />
        <StatCard icon={CheckCircle2} label="Available Seats" value={summary.available_seats.toLocaleString()} sub="Ready to allocate" accent="emerald" />
        <StatCard icon={CircleSlash} label="Occupied Seats" value={summary.occupied_seats.toLocaleString()} accent="brand" />
        <StatCard icon={Bookmark} label="Reserved" value={summary.reserved_seats.toLocaleString()} accent="amber" />
        <StatCard icon={Wrench} label="Maintenance" value={summary.maintenance_seats.toLocaleString()} accent="rose" />
        <StatCard icon={UserPlus} label="Pending Allocation" value={summary.pending_allocation.toLocaleString()} sub="New joiners" accent="amber" />
        <StatCard icon={Gauge} label="Utilization" value={`${summary.utilization_pct}%`} accent="emerald" />
      </div>

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Seat status donut */}
        <div className="card p-6">
          <h3 className="text-base font-bold text-slate-800">Seat Status</h3>
          <p className="text-xs text-slate-400">Breakdown of all seats</p>
          <div className="mt-2 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={donut} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2} isAnimationActive={false}>
                  {donut.map((d) => (
                    <Cell key={d.name} fill={SEAT_COLORS[d.name]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => v.toLocaleString()} />
                <Legend iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Project utilization */}
        <div className="card p-6 lg:col-span-2">
          <h3 className="text-base font-bold text-slate-800">Project-wise Allocation</h3>
          <p className="text-xs text-slate-400">Employees & allocated seats per project</p>
          <div className="mt-2 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={projects} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef2f7" />
                <XAxis dataKey="project" tick={{ fontSize: 11 }} interval={0} angle={-25} textAnchor="end" height={54} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend iconType="circle" />
                <Bar dataKey="employees" name="Employees" fill="#818cf8" radius={[4, 4, 0, 0]} isAnimationActive={false} />
                <Bar dataKey="allocated_seats" name="Allocated Seats" fill="#4f46e5" radius={[4, 4, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Floor occupancy */}
      <div className="card p-6">
        <h3 className="text-base font-bold text-slate-800">Floor-wise Occupancy</h3>
        <p className="text-xs text-slate-400">Seat status distribution across floors</p>
        <div className="mt-4 space-y-4">
          {floors.map((f) => (
            <div key={f.floor}>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="font-semibold text-slate-700">Floor {f.floor}</span>
                <span className="text-slate-400">
                  {f.Occupied.toLocaleString()} / {f.total.toLocaleString()} occupied · {f.occupancy_pct}%
                </span>
              </div>
              <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100">
                {['Occupied', 'Available', 'Reserved', 'Maintenance'].map((k) => (
                  <div
                    key={k}
                    style={{ width: `${(f[k] / f.total) * 100}%`, backgroundColor: SEAT_COLORS[k] }}
                    title={`${k}: ${f[k]}`}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-5 flex flex-wrap gap-4 text-xs text-slate-500">
          {Object.entries(SEAT_COLORS).map(([k, c]) => (
            <span key={k} className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: c }} />
              {k}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
