import { useEffect, useState, useCallback } from 'react'
import { Search, UserPlus, MapPin, Armchair, X, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { Badge, Spinner, EmptyState, Modal, Toast } from '../components/ui'

export default function Employees() {
  const [data, setData] = useState(null)
  const [projects, setProjects] = useState([])
  const [filters, setFilters] = useState({
    search: '',
    project_id: '',
    status: '',
    allocation_status: '',
  })
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [showAdd, setShowAdd] = useState(false)
  const [detail, setDetail] = useState(null)

  const notify = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 2600)
  }

  const load = useCallback(() => {
    setLoading(true)
    api
      .employees({ ...filters, limit: 50 })
      .then(setData)
      .catch((e) => notify(e.message, 'error'))
      .finally(() => setLoading(false))
  }, [filters])

  useEffect(() => {
    api.projects().then(setProjects).catch(() => {})
  }, [])

  useEffect(() => {
    const t = setTimeout(load, 250) // debounce search
    return () => clearTimeout(t)
  }, [load])

  const setF = (k, v) => setFilters((f) => ({ ...f, [k]: v }))

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-800">Employees</h1>
          <p className="text-sm text-slate-500">
            Search, filter, add and allocate seats for {data ? data.total.toLocaleString() : '…'} employees.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowAdd(true)}>
          <UserPlus size={16} /> Add Employee
        </button>
      </header>

      {/* Filters */}
      <div className="card p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="relative md:col-span-2">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              className="input pl-9"
              placeholder="Search by name, email or employee code…"
              value={filters.search}
              onChange={(e) => setF('search', e.target.value)}
            />
          </div>
          <select className="input" value={filters.project_id} onChange={(e) => setF('project_id', e.target.value)}>
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <select className="input" value={filters.allocation_status} onChange={(e) => setF('allocation_status', e.target.value)}>
            <option value="">Any allocation</option>
            <option value="Allocated">Allocated</option>
            <option value="Pending">Pending</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <Spinner label="Loading employees…" />
        ) : !data || data.items.length === 0 ? (
          <EmptyState title="No employees found" subtitle="Try adjusting your filters." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                  <th className="px-5 py-3 font-semibold">Employee</th>
                  <th className="px-5 py-3 font-semibold">Department / Role</th>
                  <th className="px-5 py-3 font-semibold">Project</th>
                  <th className="px-5 py-3 font-semibold">Seat</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((e) => (
                  <tr key={e.id} className="border-b border-slate-50 hover:bg-slate-50/60">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-3">
                        <div className="grid h-9 w-9 place-items-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
                          {e.name.split(' ').map((n) => n[0]).slice(0, 2).join('')}
                        </div>
                        <div>
                          <p className="font-semibold text-slate-800">{e.name}</p>
                          <p className="text-xs text-slate-400">{e.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <p className="text-slate-700">{e.department}</p>
                      <p className="text-xs text-slate-400">{e.role}</p>
                    </td>
                    <td className="px-5 py-3">{e.project_name || <span className="text-slate-300">—</span>}</td>
                    <td className="px-5 py-3">
                      {e.seat ? (
                        <span className="inline-flex items-center gap-1 font-medium text-slate-700">
                          <MapPin size={13} className="text-brand-500" />
                          F{e.seat.floor}·{e.seat.zone}·{e.seat.seat_number}
                        </span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3"><Badge status={e.allocation_status} /></td>
                    <td className="px-5 py-3 text-right">
                      <button className="text-xs font-semibold text-brand-600 hover:text-brand-800" onClick={() => setDetail(e)}>
                        Manage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showAdd && (
        <AddEmployeeModal
          projects={projects}
          onClose={() => setShowAdd(false)}
          onCreated={() => { setShowAdd(false); notify('Employee created.'); load() }}
          onError={(m) => notify(m, 'error')}
        />
      )}

      {detail && (
        <ManageModal
          employee={detail}
          onClose={() => setDetail(null)}
          notify={notify}
          reload={() => { load(); setDetail(null) }}
        />
      )}

      <Toast toast={toast} />
    </div>
  )
}

function AddEmployeeModal({ projects, onClose, onCreated, onError }) {
  const [form, setForm] = useState({
    name: '', email: '', department: '', role: '', project_id: '',
    joining_date: new Date().toISOString().slice(0, 10),
  })
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { ...form, project_id: form.project_id ? Number(form.project_id) : null }
      await api.createEmployee(payload)
      onCreated()
    } catch (err) {
      onError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal open onClose={onClose} title="Add New Employee">
      <form onSubmit={submit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Full name" required>
            <input className="input" required value={form.name} onChange={(e) => set('name', e.target.value)} />
          </Field>
          <Field label="Email" required>
            <input type="email" className="input" required value={form.email} onChange={(e) => set('email', e.target.value)} />
          </Field>
          <Field label="Department">
            <input className="input" value={form.department} onChange={(e) => set('department', e.target.value)} />
          </Field>
          <Field label="Role">
            <input className="input" value={form.role} onChange={(e) => set('role', e.target.value)} />
          </Field>
          <Field label="Project">
            <select className="input" value={form.project_id} onChange={(e) => set('project_id', e.target.value)}>
              <option value="">Unassigned</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
          <Field label="Joining date">
            <input type="date" className="input" value={form.joining_date} onChange={(e) => set('joining_date', e.target.value)} />
          </Field>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving && <Loader2 size={16} className="animate-spin" />} Create Employee
          </button>
        </div>
      </form>
    </Modal>
  )
}

function ManageModal({ employee, onClose, notify, reload }) {
  const [busy, setBusy] = useState(false)
  const [suggestions, setSuggestions] = useState(null)
  const [prefFloor, setPrefFloor] = useState('')

  const loadSuggestions = async () => {
    try {
      const res = await api.availableSeats({ floor: prefFloor || undefined, limit: 8 })
      setSuggestions(res.items)
    } catch (e) { notify(e.message, 'error') }
  }

  useEffect(() => { if (!employee.seat) loadSuggestions() }, [])
  useEffect(() => { if (!employee.seat) loadSuggestions() }, [prefFloor])

  const allocate = async (seatId) => {
    setBusy(true)
    try {
      const res = await api.allocate({ employee_id: employee.id, seat_id: seatId, preferred_floor: prefFloor ? Number(prefFloor) : undefined })
      notify(`Allocated ${res.seat.seat_number} to ${employee.name}.`)
      reload()
    } catch (e) { notify(e.message, 'error') } finally { setBusy(false) }
  }

  const release = async () => {
    setBusy(true)
    try {
      await api.release({ employee_id: employee.id })
      notify(`Seat released for ${employee.name}.`)
      reload()
    } catch (e) { notify(e.message, 'error') } finally { setBusy(false) }
  }

  return (
    <Modal open onClose={onClose} title={employee.name}>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <Info label="Employee code" value={employee.employee_code} />
          <Info label="Email" value={employee.email} />
          <Info label="Department" value={employee.department || '—'} />
          <Info label="Role" value={employee.role || '—'} />
          <Info label="Project" value={employee.project_name || '—'} />
          <Info label="Status"><Badge status={employee.allocation_status} /></Info>
        </div>

        {employee.seat ? (
          <div className="rounded-xl bg-brand-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-500">Current seat</p>
            <p className="mt-1 text-lg font-bold text-brand-800">
              Floor {employee.seat.floor} · Zone {employee.seat.zone} · Seat {employee.seat.seat_number}
            </p>
            <button className="btn-ghost mt-3" disabled={busy} onClick={release}>
              <X size={16} /> Release seat
            </button>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-200 p-4">
            <p className="mb-2 text-sm font-semibold text-slate-700">Suggested available seats</p>
            <select className="input mb-3" value={prefFloor} onChange={(e) => setPrefFloor(e.target.value)}>
              <option value="">Any floor (auto-suggest near team)</option>
              {[1, 2, 3, 4, 5].map((f) => <option key={f} value={f}>Floor {f}</option>)}
            </select>
            <div className="flex flex-wrap gap-2">
              {suggestions === null ? (
                <span className="text-xs text-slate-400">Finding seats…</span>
              ) : suggestions.length === 0 ? (
                <span className="text-xs text-slate-400">No available seats on this floor.</span>
              ) : (
                suggestions.map((s) => (
                  <button
                    key={s.id}
                    disabled={busy}
                    onClick={() => allocate(s.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700"
                  >
                    <Armchair size={13} /> F{s.floor}·{s.zone}·{s.seat_number}
                  </button>
                ))
              )}
            </div>
            <button className="btn-primary mt-4" disabled={busy} onClick={() => allocate(null)}>
              {busy && <Loader2 size={16} className="animate-spin" />} Auto-allocate best seat
            </button>
          </div>
        )}
      </div>
    </Modal>
  )
}

function Field({ label, required, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold text-slate-500">
        {label} {required && <span className="text-rose-500">*</span>}
      </span>
      {children}
    </label>
  )
}

function Info({ label, value, children }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <div className="mt-0.5 font-medium text-slate-700">{children || value}</div>
    </div>
  )
}
