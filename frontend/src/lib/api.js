// Central API client. Base URL is configurable so the same build works
// locally and on Render/Railway (set VITE_API_URL at build time).
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch (_) {}
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

const qs = (params) => {
  const clean = Object.fromEntries(
    Object.entries(params || {}).filter(([, v]) => v !== '' && v != null)
  )
  const s = new URLSearchParams(clean).toString()
  return s ? `?${s}` : ''
}

export const api = {
  base: BASE,
  // Dashboard
  summary: () => request('/dashboard/summary'),
  projectUtilization: () => request('/dashboard/project-utilization'),
  floorUtilization: () => request('/dashboard/floor-utilization'),
  // Employees
  employees: (params) => request(`/employees${qs(params)}`),
  employee: (id) => request(`/employees/${id}`),
  createEmployee: (data) =>
    request('/employees', { method: 'POST', body: JSON.stringify(data) }),
  updateEmployee: (id, data) =>
    request(`/employees/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deactivateEmployee: (id) => request(`/employees/${id}`, { method: 'DELETE' }),
  // Projects
  projects: () => request('/projects'),
  projectEmployees: (id) => request(`/projects/${id}/employees`),
  // Seats
  seats: (params) => request(`/seats${qs(params)}`),
  availableSeats: (params) => request(`/seats/available${qs(params)}`),
  allocate: (data) =>
    request('/seats/allocate', { method: 'POST', body: JSON.stringify(data) }),
  release: (data) =>
    request('/seats/release', { method: 'POST', body: JSON.stringify(data) }),
  // AI
  aiQuery: (query) =>
    request('/ai/query', { method: 'POST', body: JSON.stringify({ query }) }),
}
