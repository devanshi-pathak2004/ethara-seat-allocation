import { useEffect, useState, useCallback } from 'react'
import { Search, Armchair } from 'lucide-react'
import { api } from '../lib/api'
import { Badge, Spinner, EmptyState, Toast, STATUS_STYLES } from '../components/ui'

const ZONES = ['A', 'B', 'C', 'D']
const STATUSES = ['Available', 'Occupied', 'Reserved', 'Maintenance']

export default function Seats() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [filters, setFilters] = useState({ search: '', floor: '', zone: '', status: '' })

  const notify = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 2600)
  }

  const load = useCallback(() => {
    setLoading(true)
    api
      .seats({ ...filters, limit: 120 })
      .then(setData)
      .catch((e) => notify(e.message, 'error'))
      .finally(() => setLoading(false))
  }, [filters])

  useEffect(() => {
    const t = setTimeout(load, 250)
    return () => clearTimeout(t)
  }, [load])

  const setF = (k, v) => setFilters((f) => ({ ...f, [k]: v }))

  const release = async (seatId, seatNo) => {
    try {
      await api.release({ seat_id: seatId })
      notify(`Seat ${seatNo} released.`)
      load()
    } catch (e) { notify(e.message, 'error') }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-800">Seats</h1>
        <p className="text-sm text-slate-500">
          Browse and manage {data ? data.total.toLocaleString() : '…'} seats across 5 floors.
        </p>
      </header>

      <div className="card p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input className="input pl-9" placeholder="Seat number…" value={filters.search} onChange={(e) => setF('search', e.target.value)} />
          </div>
          <select className="input" value={filters.floor} onChange={(e) => setF('floor', e.target.value)}>
            <option value="">All floors</option>
            {[1, 2, 3, 4, 5].map((f) => <option key={f} value={f}>Floor {f}</option>)}
          </select>
          <select className="input" value={filters.zone} onChange={(e) => setF('zone', e.target.value)}>
            <option value="">All zones</option>
            {ZONES.map((z) => <option key={z} value={z}>Zone {z}</option>)}
          </select>
          <select className="input" value={filters.status} onChange={(e) => setF('status', e.target.value)}>
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {loading ? (
        <Spinner label="Loading seats…" />
      ) : !data || data.items.length === 0 ? (
        <div className="card"><EmptyState title="No seats found" subtitle="Adjust your filters." /></div>
      ) : (
        <>
          <p className="text-xs text-slate-400">
            Showing {data.items.length} of {data.total.toLocaleString()} matching seats.
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
            {data.items.map((s) => (
              <div key={s.id} className="card p-4 transition hover:shadow-soft">
                <div className="flex items-start justify-between">
                  <div className="grid h-9 w-9 place-items-center rounded-lg bg-slate-100 text-slate-500">
                    <Armchair size={18} />
                  </div>
                  <span className={`badge ${STATUS_STYLES[s.status]}`}>{s.status}</span>
                </div>
                <p className="mt-3 text-lg font-extrabold text-slate-800">{s.seat_number}</p>
                <p className="text-xs text-slate-400">Floor {s.floor} · Zone {s.zone} · Bay {s.bay}</p>
                {s.employee_name ? (
                  <div className="mt-3 border-t border-slate-100 pt-2">
                    <p className="truncate text-xs font-semibold text-slate-700">{s.employee_name}</p>
                    <p className="truncate text-[11px] text-slate-400">{s.project_name}</p>
                    <button
                      onClick={() => release(s.id, s.seat_number)}
                      className="mt-2 text-[11px] font-semibold text-rose-500 hover:text-rose-700"
                    >
                      Release seat
                    </button>
                  </div>
                ) : (
                  <div className="mt-3 border-t border-slate-100 pt-2">
                    <p className="text-[11px] text-slate-300">Unassigned</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      <Toast toast={toast} />
    </div>
  )
}
