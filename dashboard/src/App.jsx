import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence, animate } from 'framer-motion'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import * as api from './services/api.js'

// ─── API RESPONSE SHAPES (actual backend) ──────────────────────────────────────
// GET /api/v1/analytics/top-posts  → { posts: [{ rank, competitor_name, platform, rank_score, views_count, likes_count, comments_count }] }
// GET /api/v1/analytics/sentiment-overview → { by_competitor: [{ competitor_name, overall_sentiment, post_count }], sentiment_distribution: { positive, neutral, negative } }
// GET /api/v1/insights → { items: [{ id, insight_type, title, body, generated_at }] }
// GET /api/v1/competitors → { items: [{ id, name, platform, handle, is_active }] }  ← one record per platform
// GET /api/v1/posts → { items: [{ competitor_name, platform, posted_at, metrics: { rank_score } }], total }

// ─── DESIGN TOKENS ─────────────────────────────────────────────────────────────
const T = {
  dark:    '#09180E',
  deep:    '#102318',
  primary: '#1B6038',
  mid:     '#237548',
  accent:  '#2E9E60',
  light:   '#4DBF7F',
  pale:    '#A3DEB9',
  bg:      '#EFF8F2',
  surface: '#FFFFFF',
  border:  '#CAE8D5',
  text:    '#0C2016',
  muted:   '#4A7260',
  blue:    '#2563EB',
  yellow:  '#F59E0B',
  orange:  '#F97316',
  red:     '#EF4444',
}

const PALETTE   = [T.accent, '#2563EB', '#F59E0B', '#EF4444', '#8B5CF6']
const PIE_COLS  = [T.accent, '#E1306C']

// ─── MOCK FALLBACK DATA ────────────────────────────────────────────────────────
const MOCK = {
  kpis: {
    totalPosts: 2847, postsChange: 12.4,
    avgEngagement: 84.3, engagementChange: -2.1,
    topScore: 97.2, topScoreChange: 5.3,
    sentimentIndex: 78, sentimentChange: 3.8,
  },
  timeline: [
    { date: 'Apr 7',  clarifresh: 82, dole: 74, zespri: 68, driscoll: 91 },
    { date: 'Apr 8',  clarifresh: 79, dole: 80, zespri: 72, driscoll: 85 },
    { date: 'Apr 9',  clarifresh: 91, dole: 71, zespri: 85, driscoll: 78 },
    { date: 'Apr 10', clarifresh: 87, dole: 83, zespri: 79, driscoll: 92 },
    { date: 'Apr 11', clarifresh: 94, dole: 77, zespri: 88, driscoll: 76 },
    { date: 'Apr 12', clarifresh: 89, dole: 85, zespri: 91, driscoll: 88 },
    { date: 'Apr 13', clarifresh: 96, dole: 79, zespri: 86, driscoll: 94 },
  ],
  platform: [
    { name: 'TikTok',    value: 1642, pct: 57.7 },
    { name: 'Instagram', value: 1205, pct: 42.3 },
  ],
  rankings: [
    { rank: 1, competitor: "Driscoll's",   platform: 'tiktok',    score: 97.2, views: 2400000, likes: 186000, comments: 4200, sentiment: 'positive' },
    { rank: 2, competitor: 'Clarifresh',   platform: 'instagram', score: 94.8, views: 1850000, likes: 142000, comments: 3100, sentiment: 'positive' },
    { rank: 3, competitor: 'Zespri',       platform: 'tiktok',    score: 91.4, views: 1620000, likes: 128000, comments: 2800, sentiment: 'positive' },
    { rank: 4, competitor: 'Dole',         platform: 'instagram', score: 85.7, views: 1240000, likes: 94000,  comments: 1900, sentiment: 'neutral'  },
    { rank: 5, competitor: 'Fresh Del Monte', platform: 'tiktok', score: 82.1, views: 980000,  likes: 76000,  comments: 1600, sentiment: 'positive' },
    { rank: 6, competitor: "Driscoll's",   platform: 'instagram', score: 79.3, views: 840000,  likes: 65000,  comments: 1200, sentiment: 'positive' },
    { rank: 7, competitor: 'Zespri',       platform: 'instagram', score: 74.8, views: 720000,  likes: 54000,  comments: 980,  sentiment: 'neutral'  },
    { rank: 8, competitor: 'Dole',         platform: 'tiktok',    score: 71.2, views: 620000,  likes: 48000,  comments: 840,  sentiment: 'positive' },
  ],
  sentiment: [
    { competitor: 'Clarifresh',      positive: 82, neutral: 14, negative: 4 },
    { competitor: "Driscoll's",      positive: 76, neutral: 18, negative: 6 },
    { competitor: 'Zespri',          positive: 71, neutral: 22, negative: 7 },
    { competitor: 'Dole',            positive: 68, neutral: 24, negative: 8 },
    { competitor: 'Fresh Del Monte', positive: 64, neutral: 28, negative: 8 },
  ],
  insights: [
    {
      id: 1, type: 'trend',
      title: 'TikTok Outperforms Instagram This Week',
      body: 'TikTok posts are averaging 34% higher engagement scores than Instagram across all tracked competitors. Short-form video featuring produce preparation and farm-to-table stories is driving the highest interaction rates.',
      date: 'Apr 13, 2026',
    },
    {
      id: 2, type: 'alert',
      title: "Sentiment Spike for Driscoll's",
      body: "Driscoll's experienced a +12% increase in positive sentiment following their \"Berry Season Launch\" campaign. User-generated content reshared by the brand appears to be the primary driver.",
      date: 'Apr 12, 2026',
    },
    {
      id: 3, type: 'recommendation',
      title: 'Recommendation: Increase Video Frequency',
      body: 'Based on 2-week performance data, competitors posting 4+ videos per week show 28% higher average ranking scores. Clarifresh currently posts 2.3 videos/week — there is a clear opportunity to close this gap.',
      date: 'Apr 11, 2026',
    },
  ],
  competitors: [
    { id: 1, name: "Driscoll's",    handle: '@driscolls',     platforms: ['tiktok', 'instagram'], status: 'active',   posts: 284 },
    { id: 2, name: 'Zespri',        handle: '@zesprikiwi',    platforms: ['tiktok', 'instagram'], status: 'active',   posts: 196 },
    { id: 3, name: 'Dole',          handle: '@dole',          platforms: ['instagram'],           status: 'active',   posts: 178 },
    { id: 4, name: 'Fresh Del Monte', handle: '@freshdelmonte', platforms: ['tiktok'],            status: 'scraping', posts: 0   },
  ],
}

// ─── API ADAPTERS ──────────────────────────────────────────────────────────────

// /api/v1/analytics/top-posts → { posts: [...] }
function adaptRankings(raw = {}) {
  const posts = Array.isArray(raw) ? raw : (raw.posts ?? [])
  return posts.map((r, i) => ({
    rank:       r.rank            ?? i + 1,
    competitor: r.competitor_name ?? '',
    platform:   String(r.platform ?? '').toLowerCase(),
    score:      Number(r.rank_score ?? 0),
    views:      Number(r.views_count   ?? 0),
    likes:      Number(r.likes_count   ?? 0),
    comments:   Number(r.comments_count ?? 0),
    sentiment:  'positive',
  }))
}

// /api/v1/analytics/sentiment-overview → { by_competitor: [{ competitor_name, overall_sentiment }] }
const SENT_PCTS = {
  positive: { positive: 74, neutral: 19, negative: 7 },
  neutral:  { positive: 40, neutral: 45, negative: 15 },
  negative: { positive: 20, neutral: 30, negative: 50 },
}
function adaptSentiment(raw = {}) {
  const items = Array.isArray(raw) ? raw : (raw.by_competitor ?? [])
  return items
    .filter(r => r.competitor_name)
    .map(r => ({
      competitor: r.competitor_name,
      ...(SENT_PCTS[(r.overall_sentiment ?? 'neutral').toLowerCase()] ?? SENT_PCTS.neutral),
    }))
}

// /api/v1/insights → { items: [{ id, insight_type, title, body, generated_at }] }
function adaptInsights(raw = {}) {
  const items = Array.isArray(raw) ? raw : (raw.items ?? [])
  return items.map((r, i) => {
    const t = String(r.insight_type ?? '').toLowerCase()
    const type = t.includes('recommend') ? 'recommendation' : t.includes('alert') ? 'alert' : 'trend'
    return {
      id:    r.id ?? i + 1,
      type,
      title: r.title ?? '',
      body:  r.body  ?? '',
      date:  r.generated_at
        ? new Date(r.generated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
        : '',
    }
  })
}

// /api/v1/competitors → { items: [{ id, name, platform, handle, is_active }] }
// Backend stores one record per platform — group by name for the UI
function adaptCompetitors(raw = {}) {
  const items = Array.isArray(raw) ? raw : (raw.items ?? [])
  const byName = new Map()
  for (const r of items) {
    if (!byName.has(r.name)) {
      byName.set(r.name, { id: r.id, name: r.name, handle: r.handle ?? '', platforms: [], status: r.is_active ? 'active' : 'inactive', posts: 0 })
    }
    const entry = byName.get(r.name)
    const p = String(r.platform ?? '').toLowerCase()
    if (p && !entry.platforms.includes(p)) entry.platforms.push(p)
  }
  return Array.from(byName.values())
}

// Derive KPIs from posts total + top-posts scores
function deriveKpis(postsData = {}, topPostsData = {}) {
  const total  = postsData.total ?? 0
  const posts  = Array.isArray(topPostsData) ? topPostsData : (topPostsData.posts ?? [])
  const scores = posts.map(p => Number(p.rank_score ?? 0)).filter(v => v > 0)
  const avg    = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0
  const top    = scores.length ? Math.max(...scores) : 0
  return {
    totalPosts: total, postsChange: 0,
    avgEngagement: Math.round(avg * 10) / 10, engagementChange: 0,
    topScore: Math.round(top * 10) / 10, topScoreChange: 0,
    sentimentIndex: 0, sentimentChange: 0,
  }
}

// Derive platform split from top-posts data
function derivePlatform(topPostsData = {}) {
  const posts  = Array.isArray(topPostsData) ? topPostsData : (topPostsData.posts ?? [])
  const counts = {}
  for (const p of posts) {
    const k = String(p.platform ?? '').toLowerCase()
    counts[k] = (counts[k] ?? 0) + 1
  }
  const total = Object.values(counts).reduce((a, b) => a + b, 0)
  if (!total) return []
  return Object.entries(counts).map(([k, v]) => ({
    name:  k === 'tiktok' ? 'TikTok' : 'Instagram',
    value: v,
    pct:   Math.round((v / total) * 1000) / 10,
  }))
}

// Build timeline from /api/v1/posts items: group by date → avg rank_score per competitor
function buildTimeline(postsData = {}) {
  const items = Array.isArray(postsData) ? postsData : (postsData.items ?? [])
  if (!items.length) return null
  const byDate = {}
  for (const p of items) {
    const rawDate = p.posted_at ?? p.ingested_at
    if (!rawDate) continue
    const date = new Date(rawDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    const name = (p.competitor_name ?? '').toLowerCase().replace(/['\s]/g, '')
    if (!name) continue
    const score = Number(p.metrics?.rank_score ?? 0)
    if (!byDate[date]) byDate[date] = {}
    if (!byDate[date][name]) byDate[date][name] = { total: 0, count: 0 }
    byDate[date][name].total += score
    byDate[date][name].count += 1
  }
  const entries = Object.entries(byDate)
    .sort(([a], [b]) => new Date(a) - new Date(b))
    .map(([date, comps]) => {
      const entry = { date }
      for (const [k, { total, count }] of Object.entries(comps)) entry[k] = Math.round(total / count)
      return entry
    })
  return entries.length ? entries : null
}

// ─── UTILS ────────────────────────────────────────────────────────────────────
const fmt = n =>
  n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' :
  n >= 1e3 ? (n / 1e3).toFixed(0) + 'K' : String(n)

// ─── ANIMATION VARIANTS ───────────────────────────────────────────────────────
const stagger = {
  hidden:  { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.05 } },
}
const fadeUp = {
  hidden:  { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.33, 1, 0.68, 1] } },
}
const fadeIn = {
  hidden:  { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.25, ease: 'easeOut' } },
}

// ─── ANIMATED NUMBER (count-up) ───────────────────────────────────────────────
function AnimatedNumber({ to, decimals = 0, prefix = '', suffix = '' }) {
  const ref = useRef(null)
  useEffect(() => {
    const ctrl = animate(0, to, {
      duration: 1.6,
      ease: [0.33, 1, 0.68, 1],
      onUpdate(v) {
        if (ref.current) ref.current.textContent = prefix + v.toFixed(decimals) + suffix
      },
    })
    return ctrl.stop
  }, [to, decimals, prefix, suffix])
  return <span ref={ref}>{prefix}0{suffix}</span>
}

// ─── KPI CARD ─────────────────────────────────────────────────────────────────
function KPICard({ title, to, decimals = 0, prefix = '', suffix = '', icon, change, accent }) {
  const pos = change >= 0
  return (
    <motion.div
      variants={fadeUp}
      whileHover={{ y: -3, boxShadow: `0 16px 48px ${accent}28` }}
      style={{
        background: T.surface, border: `1px solid ${T.border}`, borderRadius: 16,
        padding: '22px 20px', position: 'relative', overflow: 'hidden', cursor: 'default',
        transition: 'box-shadow 0.2s',
      }}
    >
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 3,
        background: `linear-gradient(90deg, ${accent}, ${accent}44)`,
      }} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <span style={{ fontSize: 24 }}>{icon}</span>
        <span style={{
          fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 100,
          background: pos ? '#E3F9ED' : '#FEF0EE', color: pos ? T.accent : T.red,
        }}>
          {pos ? '↑' : '↓'} {Math.abs(change)}%
        </span>
      </div>

      <div style={{ fontSize: 32, fontWeight: 800, color: T.text, lineHeight: 1 }}>
        <AnimatedNumber to={to} decimals={decimals} prefix={prefix} suffix={suffix} />
      </div>
      <div style={{ fontSize: 11, color: T.muted, marginTop: 6, fontWeight: 500 }}>{title}</div>
    </motion.div>
  )
}

// ─── SIDEBAR NAV ──────────────────────────────────────────────────────────────
const NAV = [
  { id: 'overview',    label: 'Overview',    icon: '▦' },
  { id: 'rankings',    label: 'Rankings',    icon: '◎' },
  { id: 'sentiment',   label: 'Sentiment',   icon: '◉' },
  { id: 'insights',    label: 'AI Insights', icon: '✦' },
  { id: 'competitors', label: 'Competitors', icon: '◐' },
]

function Sidebar({ active, setActive, platforms, setPlatforms, dateRange, setDateRange, onIngest, ingesting }) {
  return (
    <motion.aside
      initial={{ x: -260, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.45, ease: [0.33, 1, 0.68, 1] }}
      style={{
        width: 236, minWidth: 236, background: T.dark,
        display: 'flex', flexDirection: 'column',
        padding: '24px 12px', overflowY: 'auto',
      }}
    >
      <div style={{ padding: '0 8px 28px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: `linear-gradient(135deg, ${T.accent}, ${T.mid})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 800, color: '#fff',
        }}>C</div>
        <div>
          <div style={{ color: '#fff', fontWeight: 700, fontSize: 14, lineHeight: 1.1 }}>Clarifresh</div>
          <div style={{ color: '#ffffff44', fontSize: 10, marginTop: 2 }}>Analytics</div>
        </div>
      </div>

      <div style={{ marginBottom: 4 }}>
        <div style={{ color: '#ffffff28', fontSize: 9, fontWeight: 700, letterSpacing: 2, padding: '0 10px 8px', textTransform: 'uppercase' }}>
          Navigation
        </div>
        {NAV.map(item => (
          <motion.button
            key={item.id}
            onClick={() => setActive(item.id)}
            whileHover={{ x: 3 }}
            whileTap={{ scale: 0.97 }}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 9,
              padding: '9px 12px', borderRadius: 9, border: 'none', cursor: 'pointer',
              background: active === item.id ? `${T.accent}20` : 'transparent',
              color: active === item.id ? T.light : '#ffffff44',
              fontFamily: 'Poppins, sans-serif', fontSize: 13,
              fontWeight: active === item.id ? 600 : 400,
              textAlign: 'left', transition: 'color 0.15s, background 0.15s',
              marginBottom: 2,
            }}
          >
            <span style={{ fontSize: 14, width: 18, textAlign: 'center' }}>{item.icon}</span>
            {item.label}
            {active === item.id && (
              <motion.div
                layoutId="nav-dot"
                style={{ marginLeft: 'auto', width: 5, height: 5, borderRadius: '50%', background: T.light }}
                transition={{ type: 'spring', stiffness: 500, damping: 35 }}
              />
            )}
          </motion.button>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      <div style={{ borderTop: '#ffffff0c solid 1px', paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div>
          <div style={{ color: '#ffffff28', fontSize: 9, fontWeight: 700, letterSpacing: 2, marginBottom: 8, padding: '0 2px', textTransform: 'uppercase' }}>
            Platform
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            {[{ id: 'tiktok', label: '🎵 TT' }, { id: 'instagram', label: '📸 IG' }].map(p => (
              <button
                key={p.id}
                onClick={() => setPlatforms(prev =>
                  prev.includes(p.id) ? prev.filter(x => x !== p.id) : [...prev, p.id]
                )}
                style={{
                  flex: 1, padding: '7px 0', borderRadius: 7, border: 'none', cursor: 'pointer',
                  background: platforms.includes(p.id) ? T.primary : '#ffffff0c',
                  color: platforms.includes(p.id) ? '#fff' : '#ffffff33',
                  fontSize: 10, fontWeight: 700, fontFamily: 'Poppins, sans-serif',
                  transition: 'all 0.15s',
                }}
              >{p.label}</button>
            ))}
          </div>
        </div>

        <div>
          <div style={{ color: '#ffffff28', fontSize: 9, fontWeight: 700, letterSpacing: 2, marginBottom: 8, padding: '0 2px', textTransform: 'uppercase' }}>
            Date Range
          </div>
          <div style={{ display: 'flex', gap: 5 }}>
            {['24h', '7d', '14d'].map(d => (
              <button
                key={d}
                onClick={() => setDateRange(d)}
                style={{
                  flex: 1, padding: '6px 0', borderRadius: 6, border: 'none', cursor: 'pointer',
                  background: dateRange === d ? T.primary : '#ffffff0c',
                  color: dateRange === d ? '#fff' : '#ffffff33',
                  fontSize: 11, fontWeight: 700, fontFamily: 'Poppins, sans-serif',
                  transition: 'all 0.15s',
                }}
              >{d}</button>
            ))}
          </div>
        </div>

        <motion.button
          onClick={onIngest}
          whileTap={{ scale: 0.97 }}
          style={{
            width: '100%', padding: '10px', borderRadius: 9,
            border: `1px solid ${T.primary}77`,
            background: ingesting ? T.primary : 'transparent',
            cursor: ingesting ? 'not-allowed' : 'pointer',
            color: ingesting ? '#fff' : T.light,
            fontSize: 12, fontWeight: 600, fontFamily: 'Poppins, sans-serif',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
            transition: 'all 0.2s',
          }}
        >
          {ingesting ? (
            <>
              <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 0.85, ease: 'linear' }}>⟳</motion.span>
              Ingesting…
            </>
          ) : '↻ Trigger Ingest'}
        </motion.button>
      </div>
    </motion.aside>
  )
}

// ─── CHART TOOLTIP ────────────────────────────────────────────────────────────
function ChartTip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: T.deep, border: `1px solid ${T.primary}`,
      borderRadius: 10, padding: '10px 14px', fontSize: 12, color: '#fff',
      boxShadow: '0 8px 24px #00000033',
    }}>
      <div style={{ fontWeight: 700, color: T.light, marginBottom: 7 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 3 }}>
          <div style={{ width: 7, height: 7, borderRadius: '50%', background: p.color }} />
          <span style={{ color: '#ffffff55' }}>{p.name}:</span>
          <span style={{ fontWeight: 600 }}>
            {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

// ─── CARD SHELL ───────────────────────────────────────────────────────────────
function Card({ title, subtitle, children, style: s = {} }) {
  return (
    <div style={{
      background: T.surface, border: `1px solid ${T.border}`,
      borderRadius: 16, padding: 22, ...s,
    }}>
      {(title || subtitle) && (
        <div style={{ marginBottom: 18 }}>
          {title    && <div style={{ fontSize: 14, fontWeight: 700, color: T.text }}>{title}</div>}
          {subtitle && <div style={{ fontSize: 11, color: T.muted, marginTop: 3 }}>{subtitle}</div>}
        </div>
      )}
      {children}
    </div>
  )
}

// ─── PLATFORM DONUT ───────────────────────────────────────────────────────────
function PlatformDonut({ data }) {
  const [hov, setHov] = useState(null)
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: T.text }}>Platform Split</div>
      <div style={{ fontSize: 11, color: T.muted, marginBottom: 10 }}>Distribution by platform</div>
      <div style={{ flex: 1, minHeight: 170 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data} cx="50%" cy="50%"
              innerRadius={50} outerRadius={78} dataKey="value"
              onMouseEnter={(_, i) => setHov(i)}
              onMouseLeave={() => setHov(null)}
            >
              {data.map((_, i) => (
                <Cell
                  key={i} fill={PIE_COLS[i]}
                  opacity={hov === null || hov === i ? 1 : 0.3}
                  style={{ transition: 'opacity 0.2s', cursor: 'pointer' }}
                />
              ))}
            </Pie>
            <Tooltip content={<ChartTip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      {data.map((item, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 7 }}>
          <div style={{ width: 9, height: 9, borderRadius: '50%', background: PIE_COLS[i], flexShrink: 0 }} />
          <span style={{ fontSize: 12, color: T.muted, flex: 1 }}>
            {item.name === 'TikTok' ? '🎵' : '📸'} {item.name}
          </span>
          <span style={{ fontSize: 12, fontWeight: 700, color: T.text }}>{item.pct}%</span>
          <span style={{ fontSize: 11, color: T.muted }}>{item.value.toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}

// ─── RANKINGS TABLE ───────────────────────────────────────────────────────────
function RankingsTable({ data }) {
  const [sort, setSort] = useState({ key: 'score', dir: 'desc' })
  const rows = [...data].sort((a, b) =>
    sort.dir === 'desc' ? b[sort.key] - a[sort.key] : a[sort.key] - b[sort.key]
  )

  const Col = ({ label, k, w }) => (
    <th
      onClick={() => setSort(s => ({ key: k, dir: s.key === k && s.dir === 'desc' ? 'asc' : 'desc' }))}
      style={{
        padding: '10px 12px', textAlign: 'left', fontWeight: 600, color: T.muted,
        cursor: 'pointer', fontSize: 10, letterSpacing: 0.5, textTransform: 'uppercase',
        borderBottom: `2px solid ${T.border}`, whiteSpace: 'nowrap', userSelect: 'none',
        width: w, background: T.bg,
      }}
    >
      {label}{sort.key === k ? (sort.dir === 'desc' ? ' ↓' : ' ↑') : ''}
    </th>
  )

  const sentBadge = s => {
    const map = { positive: [T.accent, '#E3F9ED'], neutral: [T.yellow, '#FFF8E6'], negative: [T.red, '#FEF0EE'] }
    const [c, bg] = map[s] || [T.muted, T.bg]
    return (
      <span style={{ fontSize: 10, padding: '3px 9px', borderRadius: 100, fontWeight: 700, background: bg, color: c }}>
        {s}
      </span>
    )
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr>
            <Col label="#"         k="rank"       w={44} />
            <Col label="Account"   k="competitor" w={130} />
            <Col label="Platform"  k="platform"   w={110} />
            <Col label="Score"     k="score"      w={90} />
            <Col label="Views"     k="views"      w={85} />
            <Col label="Likes"     k="likes"      w={80} />
            <Col label="Comments"  k="comments"   w={90} />
            <th style={{ padding: '10px 12px', fontSize: 10, fontWeight: 600, color: T.muted, textTransform: 'uppercase', letterSpacing: 0.5, borderBottom: `2px solid ${T.border}`, background: T.bg }}>
              Sentiment
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <motion.tr
              key={`${row.rank}-${row.competitor}`}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04, duration: 0.3 }}
              style={{ borderBottom: `1px solid ${T.border}`, cursor: 'pointer' }}
              whileHover={{ backgroundColor: '#E3F9ED33' }}
            >
              <td style={{ padding: '12px' }}>
                <span style={{ fontWeight: 800, fontSize: i < 3 ? 20 : 13, color: i < 3 ? T.accent : T.muted }}>
                  {i < 3 ? ['🥇', '🥈', '🥉'][i] : row.rank}
                </span>
              </td>
              <td style={{ padding: '12px', fontWeight: 600, color: T.text }}>{row.competitor}</td>
              <td style={{ padding: '12px' }}>
                <span style={{
                  fontSize: 10, padding: '3px 9px', borderRadius: 100, fontWeight: 700,
                  background: row.platform === 'tiktok' ? '#F2F2F2' : '#FFF0F7',
                  color: row.platform === 'tiktok' ? '#111' : '#BE185D',
                }}>
                  {row.platform === 'tiktok' ? '🎵 TikTok' : '📸 Instagram'}
                </span>
              </td>
              <td style={{ padding: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: '50%',
                    background: `conic-gradient(${T.accent} ${row.score * 3.6}deg, ${T.border} 0)`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%', background: T.surface,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 9, fontWeight: 800, color: T.text,
                    }}>
                      {row.score.toFixed(0)}
                    </div>
                  </div>
                </div>
              </td>
              <td style={{ padding: '12px', color: T.text, fontWeight: 500 }}>{fmt(row.views)}</td>
              <td style={{ padding: '12px', color: T.text, fontWeight: 500 }}>{fmt(row.likes)}</td>
              <td style={{ padding: '12px', color: T.text, fontWeight: 500 }}>{fmt(row.comments)}</td>
              <td style={{ padding: '12px' }}>{sentBadge(row.sentiment)}</td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── SENTIMENT BARS ───────────────────────────────────────────────────────────
function SentimentBars({ data }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {data.map((item, i) => (
        <motion.div
          key={item.competitor}
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.08, duration: 0.35, ease: 'easeOut' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 7, fontSize: 12 }}>
            <span style={{ fontWeight: 600, color: T.text }}>{item.competitor}</span>
            <span style={{ color: T.muted, fontWeight: 500 }}>{item.positive}% positive</span>
          </div>
          <div style={{ height: 8, borderRadius: 100, background: T.border, overflow: 'hidden', display: 'flex' }}>
            {[
              { pct: item.positive, color: T.accent },
              { pct: item.neutral,  color: T.yellow },
              { pct: item.negative, color: T.red },
            ].map((seg, j) => (
              <motion.div
                key={j}
                initial={{ width: 0 }}
                animate={{ width: `${seg.pct}%` }}
                transition={{ delay: i * 0.08 + j * 0.06 + 0.2, duration: 0.75, ease: [0.33, 1, 0.68, 1] }}
                style={{ background: seg.color, height: '100%' }}
              />
            ))}
          </div>
        </motion.div>
      ))}
      <div style={{ display: 'flex', gap: 16, marginTop: 4 }}>
        {[['Positive', T.accent], ['Neutral', T.yellow], ['Negative', T.red]].map(([l, c]) => (
          <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: T.muted }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: c }} />
            {l}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── AI INSIGHTS ──────────────────────────────────────────────────────────────
const INSIGHT_META = {
  trend:          { icon: '📈', color: '#2563EB', bg: '#EFF6FF' },
  alert:          { icon: '⚡', color: T.orange,  bg: '#FFF7ED' },
  recommendation: { icon: '💡', color: T.accent,  bg: '#F0FDF4' },
}

function InsightsPanel({ data }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {data.map((ins, i) => {
        const meta = INSIGHT_META[ins.type] ?? INSIGHT_META.trend
        return (
          <motion.div
            key={ins.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1, duration: 0.35, ease: 'easeOut' }}
            whileHover={{ x: 2 }}
            style={{
              background: T.surface, border: `1px solid ${T.border}`, borderRadius: 12,
              padding: '16px 18px', borderLeft: `3px solid ${meta.color}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 9 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8, background: meta.bg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 15, flexShrink: 0,
              }}>
                {meta.icon}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13, color: T.text, lineHeight: 1.35 }}>{ins.title}</div>
                <div style={{ fontSize: 10, color: T.muted, marginTop: 2 }}>{ins.date}</div>
              </div>
            </div>
            <p style={{ fontSize: 12, color: T.muted, lineHeight: 1.7, margin: 0 }}>{ins.body}</p>
          </motion.div>
        )
      })}
    </div>
  )
}

// ─── COMPETITOR MANAGER ───────────────────────────────────────────────────────
function CompetitorManager({ competitors, onAdd, onRemove, onDiscover }) {
  const [form, setForm]         = useState({ name: '', handle: '', platforms: [] })
  const [scanning, setScanning] = useState(false)

  const handleAdd = () => {
    if (!form.name.trim() || !form.handle.trim()) return
    onAdd({ ...form, id: Date.now(), status: 'scraping', posts: 0 })
    setForm({ name: '', handle: '', platforms: [] })
  }

  const handleScan = async () => {
    setScanning(true)
    try {
      await onDiscover()
    } finally {
      setScanning(false)
    }
  }

  const togglePlatform = p =>
    setForm(f => ({
      ...f,
      platforms: f.platforms.includes(p) ? f.platforms.filter(x => x !== p) : [...f.platforms, p],
    }))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <Card title="Add Competitor" subtitle="Track a new social account or use AI to auto-discover competitors">
        <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
          {[['name', 'Company name'], ['handle', '@handle or username']].map(([k, ph]) => (
            <input
              key={k}
              value={form[k]}
              onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
              placeholder={ph}
              style={{
                flex: 1, minWidth: 160, padding: '10px 14px', borderRadius: 9,
                border: `1px solid ${T.border}`, fontSize: 13, color: T.text,
                outline: 'none', background: T.bg, fontFamily: 'Poppins, sans-serif',
              }}
            />
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          {['tiktok', 'instagram'].map(p => {
            const on = form.platforms.includes(p)
            return (
              <button
                key={p}
                onClick={() => togglePlatform(p)}
                style={{
                  padding: '8px 16px', borderRadius: 8, cursor: 'pointer',
                  border: `1px solid ${on ? T.accent : T.border}`,
                  background: on ? '#E3F9ED' : T.surface,
                  color: on ? T.accent : T.muted,
                  fontSize: 12, fontWeight: 700, fontFamily: 'Poppins, sans-serif',
                  transition: 'all 0.15s',
                }}
              >
                {p === 'tiktok' ? '🎵 TikTok' : '📸 Instagram'}
              </button>
            )
          })}
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <motion.button
            onClick={handleAdd}
            whileTap={{ scale: 0.97 }}
            style={{
              padding: '10px 22px', borderRadius: 9, border: 'none',
              background: T.primary, color: '#fff', fontSize: 13, fontWeight: 700,
              fontFamily: 'Poppins, sans-serif', cursor: 'pointer',
            }}
          >
            + Add Competitor
          </motion.button>
          <motion.button
            onClick={handleScan}
            whileTap={{ scale: 0.97 }}
            style={{
              padding: '10px 22px', borderRadius: 9,
              border: `1px solid ${T.border}`, background: T.surface,
              color: T.text, fontSize: 13, fontWeight: 600,
              fontFamily: 'Poppins, sans-serif', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 8,
            }}
          >
            {scanning ? (
              <>
                <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 0.85, ease: 'linear' }}>✦</motion.span>
                AI Scanning…
              </>
            ) : '✦ AI Auto-Discover'}
          </motion.button>
        </div>
      </Card>

      <motion.div variants={stagger} initial="hidden" animate="visible" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {competitors.map(c => (
          <motion.div
            key={c.id}
            variants={fadeUp}
            style={{
              background: T.surface, border: `1px solid ${T.border}`,
              borderRadius: 12, padding: '14px 18px',
              display: 'flex', alignItems: 'center', gap: 14,
            }}
          >
            <div style={{
              width: 42, height: 42, borderRadius: 10, flexShrink: 0,
              background: `linear-gradient(135deg, ${T.primary}, ${T.accent})`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 18, fontWeight: 800, color: '#fff',
            }}>
              {c.name[0]}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 700, color: T.text, fontSize: 13 }}>{c.name}</div>
              <div style={{ fontSize: 11, color: T.muted }}>{c.handle}</div>
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              {c.platforms.map(p => <span key={p} style={{ fontSize: 16 }}>{p === 'tiktok' ? '🎵' : '📸'}</span>)}
            </div>
            <span style={{
              fontSize: 10, padding: '3px 9px', borderRadius: 100, fontWeight: 700, flexShrink: 0,
              background: c.status === 'active' ? '#E3F9ED' : '#FFF8E6',
              color: c.status === 'active' ? T.accent : T.yellow,
            }}>
              {c.status === 'scraping' ? '⟳ scraping' : '● active'}
            </span>
            <span style={{ fontSize: 11, color: T.muted, minWidth: 55, textAlign: 'right', flexShrink: 0 }}>
              {c.posts} posts
            </span>
            <button
              onClick={() => onRemove(c.id)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: T.red, fontSize: 20, padding: '0 2px', lineHeight: 1 }}
            >×</button>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}

// ─── LOADING SCREEN ───────────────────────────────────────────────────────────
function LoadingScreen() {
  return (
    <motion.div
      key="loading"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: T.bg }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
        <motion.div
          animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ repeat: Infinity, duration: 1.4 }}
          style={{
            width: 56, height: 56, borderRadius: 14,
            background: `linear-gradient(135deg, ${T.accent}, ${T.mid})`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 26, fontWeight: 800, color: '#fff',
          }}
        >C</motion.div>
        <div style={{ fontSize: 12, color: T.muted, fontWeight: 600 }}>Loading dashboard…</div>
        <div style={{ width: 130, height: 3, borderRadius: 100, background: T.border, overflow: 'hidden' }}>
          <motion.div
            animate={{ x: ['-100%', '200%'] }}
            transition={{ repeat: Infinity, duration: 1.1, ease: 'easeInOut' }}
            style={{ width: '50%', height: '100%', background: T.accent, borderRadius: 100 }}
          />
        </div>
      </div>
    </motion.div>
  )
}

// ─── OVERVIEW PAGE ────────────────────────────────────────────────────────────
function OverviewPage({ data }) {
  // Derive timeline keys dynamically from actual data
  const tlKeys   = data.timeline.length > 0 ? Object.keys(data.timeline[0]).filter(k => k !== 'date') : []
  const tlLabels = Object.fromEntries(tlKeys.map(k => [k, k.charAt(0).toUpperCase() + k.slice(1)]))

  return (
    <motion.div
      key="overview"
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
    >
      {/* KPIs */}
      <motion.div
        variants={stagger} initial="hidden" animate="visible"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}
      >
        <KPICard title="Posts Tracked"        to={data.kpis.totalPosts}      change={data.kpis.postsChange}      icon="📊" accent={T.accent} />
        <KPICard title="Avg Engagement Score" to={data.kpis.avgEngagement}   change={data.kpis.engagementChange} icon="⚡" accent="#2563EB" decimals={1} />
        <KPICard title="Top Ranking Score"    to={data.kpis.topScore}        change={data.kpis.topScoreChange}   icon="🏆" accent={T.yellow} decimals={1} />
        <KPICard title="Sentiment Index"      to={data.kpis.sentimentIndex}  change={data.kpis.sentimentChange}  icon="💚" accent={T.orange} suffix="%" />
      </motion.div>

      {/* Area chart + donut */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14 }}>
        <Card title="Engagement Over Time" subtitle="Composite ranking score by competitor">
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.timeline}>
                <defs>
                  {tlKeys.map((k, i) => (
                    <linearGradient key={k} id={`g-${k}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={PALETTE[i % PALETTE.length]} stopOpacity={0.18} />
                      <stop offset="95%" stopColor={PALETTE[i % PALETTE.length]} stopOpacity={0}    />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={T.border} vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: T.muted, fontFamily: 'Poppins' }} axisLine={false} tickLine={false} />
                <YAxis domain={[50, 100]} tick={{ fontSize: 11, fill: T.muted, fontFamily: 'Poppins' }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTip />} />
                {tlKeys.map((k, i) => (
                  <Area
                    key={k} type="monotone" dataKey={k} name={tlLabels[k]}
                    stroke={PALETTE[i % PALETTE.length]} strokeWidth={2.5}
                    fill={`url(#g-${k})`} dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card style={{ display: 'flex', flexDirection: 'column' }}>
          <PlatformDonut data={data.platform} />
        </Card>
      </div>

      {/* Rankings + Sentiment */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 14 }}>
        <Card title="Top Ranked Posts" subtitle="Sorted by composite engagement score">
          <RankingsTable data={data.rankings.slice(0, 5)} />
        </Card>
        <Card title="Sentiment Breakdown" subtitle="Positive / Neutral / Negative per account">
          <SentimentBars data={data.sentiment} />
        </Card>
      </div>

      {/* AI Insights */}
      <Card title="AI Weekly Insights" subtitle="Powered by Claude · auto-generated every Sunday 02:00 UTC">
        <InsightsPanel data={data.insights} />
      </Card>
    </motion.div>
  )
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab]                 = useState('overview')
  const [platforms, setPlatforms]     = useState(['tiktok', 'instagram'])
  const [dateRange, setDateRange]     = useState('7d')
  const [ingesting, setIngesting]     = useState(false)
  const [loading, setLoading]         = useState(true)
  const [data, setData]               = useState(MOCK)
  const [competitors, setCompetitors] = useState(MOCK.competitors)
  const [updated, setUpdated]         = useState(new Date())
  const [apiError, setApiError]       = useState(false)

  const fetchAll = useCallback(async () => {
    try {
      const [topPostsRes, sentimentRes, insightsRes, compsRes, postsRes] =
        await Promise.allSettled([
          api.getTopPosts({ limit: 20 }),
          api.getSentimentOverview(),
          api.getInsights({ page_size: 10 }),
          api.getCompetitors(),
          api.getPosts({ page_size: 100, sort_by: 'posted_at', order: 'desc' }),
        ])

      const val = (r, fallback) => r.status === 'fulfilled' ? r.value : fallback

      const topPostsData  = val(topPostsRes,  {})
      const sentimentData = val(sentimentRes, {})
      const insightsData  = val(insightsRes,  {})
      const compsData     = val(compsRes,     {})
      const postsData     = val(postsRes,     {})

      const rnk      = adaptRankings(topPostsData)
      const plt      = derivePlatform(topPostsData)
      const sent     = adaptSentiment(sentimentData)
      const ins      = adaptInsights(insightsData)
      const cmpList  = adaptCompetitors(compsData)
      const kpis     = deriveKpis(postsData, topPostsData)
      const timeline = buildTimeline(postsData) ?? MOCK.timeline

      setData({
        kpis:      kpis.totalPosts > 0 ? kpis : MOCK.kpis,
        timeline,
        platform:  plt.length  > 0 ? plt  : MOCK.platform,
        rankings:  rnk.length  > 0 ? rnk  : MOCK.rankings,
        sentiment: sent.length > 0 ? sent : MOCK.sentiment,
        insights:  ins.length  > 0 ? ins  : MOCK.insights,
      })
      if (cmpList.length > 0) setCompetitors(cmpList)
      setApiError(false)
      setUpdated(new Date())
    } catch (err) {
      console.error('Dashboard fetch error:', err)
      setApiError(true)
    }
  }, [])

  useEffect(() => {
    fetchAll().finally(() => setLoading(false))
  }, [fetchAll])

  const handleIngest = useCallback(async () => {
    setIngesting(true)
    try {
      await api.triggerIngest({})
      await fetchAll()
    } catch (err) {
      console.error('Ingest failed:', err)
    } finally {
      setIngesting(false)
    }
  }, [fetchAll])

  const handleAddCompetitor = useCallback(async (competitor) => {
    // Backend stores one record per platform — create one per selected platform
    const platforms = competitor.platforms.length ? competitor.platforms : ['tiktok']
    const optimistic = { ...competitor, id: Date.now() }
    setCompetitors(prev => [...prev, optimistic])
    try {
      await Promise.all(platforms.map(platform =>
        api.addCompetitor({ name: competitor.name, handle: competitor.handle, platform })
      ))
      await fetchAll()
    } catch (err) {
      console.error('Add competitor failed:', err)
    }
  }, [fetchAll])

  const handleRemoveCompetitor = useCallback(async (id) => {
    setCompetitors(prev => prev.filter(c => c.id !== id))
    try {
      await api.removeCompetitor(id)
    } catch (err) {
      console.error('Remove competitor failed:', err)
    }
  }, [])

  const handleDiscover = useCallback(async () => {
    // No backend endpoint for auto-discover yet
  }, [])

  // Derive timeline keys for sentiment page bar chart
  const tlKeys   = data.timeline.length > 0 ? Object.keys(data.timeline[0]).filter(k => k !== 'date') : []
  const tlLabels = Object.fromEntries(tlKeys.map(k => [k, k.charAt(0).toUpperCase() + k.slice(1)]))

  return (
    <AnimatePresence mode="wait">
      {loading ? (
        <LoadingScreen key="loading" />
      ) : (
        <motion.div
          key="app"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          style={{
            display: 'flex', height: '100vh',
            fontFamily: 'Poppins, sans-serif',
            background: T.bg, overflow: 'hidden',
          }}
        >
          <Sidebar
            active={tab}          setActive={setTab}
            platforms={platforms}  setPlatforms={setPlatforms}
            dateRange={dateRange}  setDateRange={setDateRange}
            onIngest={handleIngest} ingesting={ingesting}
          />

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {/* Top bar */}
            <div style={{
              background: T.surface, borderBottom: `1px solid ${T.border}`,
              padding: '14px 26px',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              flexShrink: 0,
            }}>
              <div>
                <div style={{ fontSize: 17, fontWeight: 700, color: T.text }}>
                  {NAV.find(n => n.id === tab)?.label}
                </div>
                <div style={{ fontSize: 10, color: T.muted, marginTop: 2 }}>
                  {apiError
                    ? '⚠ Backend unreachable — showing cached data'
                    : `Last synced ${updated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {platforms.map(p => (
                  <span key={p} style={{
                    fontSize: 10, padding: '4px 10px', borderRadius: 100, fontWeight: 700,
                    background: p === 'tiktok' ? '#F2F2F2' : '#FFF0F7',
                    color: p === 'tiktok' ? '#111' : '#BE185D',
                  }}>
                    {p === 'tiktok' ? '🎵 TikTok' : '📸 Instagram'}
                  </span>
                ))}
                <span style={{ fontSize: 10, padding: '4px 10px', borderRadius: 100, background: '#E3F9ED', color: T.accent, fontWeight: 700 }}>
                  {dateRange}
                </span>
              </div>
            </div>

            {/* Page content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '22px 26px' }}>
              <AnimatePresence mode="wait">
                {tab === 'overview' && (
                  <OverviewPage key="ov" data={data} />
                )}

                {tab === 'rankings' && (
                  <motion.div key="rk"
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25, ease: 'easeOut' }}
                  >
                    <Card title="Full Rankings" subtitle="All tracked posts — sortable by any column">
                      <RankingsTable data={data.rankings} />
                    </Card>
                  </motion.div>
                )}

                {tab === 'sentiment' && (
                  <motion.div key="se"
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25, ease: 'easeOut' }}
                    style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
                  >
                    <Card title="Sentiment Analysis" subtitle="Positive / Neutral / Negative breakdown by account">
                      <SentimentBars data={data.sentiment} />
                    </Card>
                    <Card title="Engagement Comparison" subtitle="Score comparison by competitor — bar view">
                      <div style={{ height: 260 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={data.timeline} barSize={12} barGap={3}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} vertical={false} />
                            <XAxis dataKey="date" tick={{ fontSize: 11, fill: T.muted, fontFamily: 'Poppins' }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fontSize: 11, fill: T.muted, fontFamily: 'Poppins' }} axisLine={false} tickLine={false} />
                            <Tooltip content={<ChartTip />} />
                            <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'Poppins', paddingTop: 12 }} />
                            {tlKeys.map((k, i) => (
                              <Bar key={k} dataKey={k} name={tlLabels[k]} fill={PALETTE[i % PALETTE.length]} radius={[4, 4, 0, 0]} />
                            ))}
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </Card>
                  </motion.div>
                )}

                {tab === 'insights' && (
                  <motion.div key="in"
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25, ease: 'easeOut' }}
                  >
                    <Card title="AI Weekly Insights" subtitle="Powered by Claude · updated every Sunday 02:00 UTC">
                      <InsightsPanel data={data.insights} />
                    </Card>
                  </motion.div>
                )}

                {tab === 'competitors' && (
                  <motion.div key="co"
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25, ease: 'easeOut' }}
                  >
                    <CompetitorManager
                      competitors={competitors}
                      onAdd={handleAddCompetitor}
                      onRemove={handleRemoveCompetitor}
                      onDiscover={handleDiscover}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
