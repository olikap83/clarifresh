// Use relative paths so Vite's dev proxy forwards /api → localhost:8000
// In production set VITE_API_URL to your deployed backend
const BASE = import.meta.env.VITE_API_URL || ''

async function req(method, path, body, timeoutMs = 8000) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)
  try {
    const res = await fetch(`${BASE}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    })
    if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
    return res.json()
  } finally {
    clearTimeout(timer)
  }
}

// ─── COMPETITORS ──────────────────────────────────────────────────────────────
export const getCompetitors   = ()     => req('GET',    '/api/v1/competitors')
export const addCompetitor    = (data) => req('POST',   '/api/v1/competitors', data)
export const removeCompetitor = (id)   => req('DELETE', `/api/v1/competitors/${id}`)

// ─── POSTS ────────────────────────────────────────────────────────────────────
export const getPosts = (params = {}) => req('GET', `/api/v1/posts?${new URLSearchParams(params)}`)

// ─── ANALYTICS ────────────────────────────────────────────────────────────────
export const getTopPosts         = (params = {}) => req('GET', `/api/v1/analytics/top-posts?${new URLSearchParams(params)}`)
export const getSentimentOverview = ()            => req('GET', '/api/v1/analytics/sentiment-overview')

// ─── INSIGHTS ─────────────────────────────────────────────────────────────────
export const getInsights = (params = {}) => req('GET', `/api/v1/insights?${new URLSearchParams(params)}`)

// ─── INGESTION ────────────────────────────────────────────────────────────────
export const triggerIngest = (body = {}) => req('POST', '/api/v1/ingestion/trigger', body)
