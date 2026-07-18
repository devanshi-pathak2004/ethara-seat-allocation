import { X } from 'lucide-react'

export const STATUS_STYLES = {
  Available: 'bg-emerald-100 text-emerald-700',
  Occupied: 'bg-brand-100 text-brand-700',
  Reserved: 'bg-amber-100 text-amber-700',
  Maintenance: 'bg-rose-100 text-rose-700',
  Allocated: 'bg-emerald-100 text-emerald-700',
  Pending: 'bg-amber-100 text-amber-700',
  Active: 'bg-emerald-100 text-emerald-700',
  Inactive: 'bg-slate-200 text-slate-600',
}

export function Badge({ status, children }) {
  const cls = STATUS_STYLES[status] || 'bg-slate-100 text-slate-600'
  return <span className={`badge ${cls}`}>{children || status}</span>
}

export function StatCard({ icon: Icon, label, value, sub, accent = 'brand' }) {
  const accents = {
    brand: 'from-brand-500 to-brand-600',
    emerald: 'from-emerald-500 to-emerald-600',
    amber: 'from-amber-500 to-amber-600',
    rose: 'from-rose-500 to-rose-600',
    slate: 'from-slate-600 to-slate-700',
  }
  return (
    <div className="card p-5 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-1 text-3xl font-extrabold tracking-tight text-slate-800">
            {value}
          </p>
          {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
        </div>
        <div
          className={`grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br ${accents[accent]} text-white shadow-soft`}
        >
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}

export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-slate-400">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
      <span className="text-sm font-medium">{label}</span>
    </div>
  )
}

export function EmptyState({ title, subtitle }) {
  return (
    <div className="py-16 text-center">
      <p className="text-sm font-semibold text-slate-500">{title}</p>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  )
}

export function Modal({ open, onClose, title, children, width = 'max-w-lg' }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className={`card relative z-10 w-full ${width} animate-fade-in`}>
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <h3 className="text-lg font-bold text-slate-800">{title}</h3>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  )
}

export function Toast({ toast }) {
  if (!toast) return null
  const styles =
    toast.type === 'error'
      ? 'bg-rose-600'
      : toast.type === 'info'
        ? 'bg-slate-800'
        : 'bg-emerald-600'
  return (
    <div className="fixed bottom-6 right-6 z-[60] animate-fade-in">
      <div className={`${styles} rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-soft`}>
        {toast.message}
      </div>
    </div>
  )
}
