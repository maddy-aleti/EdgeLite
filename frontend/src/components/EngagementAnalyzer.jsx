import { useState, useEffect, useRef } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts'

export default function EngagementAnalyzer() {
  const [sessionRunning, setSessionRunning] = useState(false)
  const [loading, setLoading] = useState(false)
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)
  const [activeNav, setActiveNav] = useState('live')
  const [timelineData, setTimelineData] = useState([])
  const pollIntervalRef = useRef(null)

  const API_BASE = 'http://localhost:8001'

  // Poll metrics when session is running
  useEffect(() => {
    if (sessionRunning) {
      const poll = async () => {
        try {
          const response = await fetch(`${API_BASE}/metrics`)
          if (!response.ok) throw new Error('Failed to fetch metrics')
          const data = await response.json()
          setMetrics(data)
          setError(null)
          // Append to timeline (keep last 60 samples)
          setTimelineData(prev => {
            const now = new Date().toLocaleTimeString('en-US', { hour12: false })
            const next = [...prev, { time: now, engagement: data.engagement_score, confusion: data.confusion_score }]
            return next.length > 60 ? next.slice(-60) : next
          })
        } catch (err) {
          setError(err.message)
        }
      }

      poll()
      pollIntervalRef.current = setInterval(poll, 3000)
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [sessionRunning])

  const handleStartSession = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to start session')
      }

      setSessionRunning(true)
      setTimelineData([])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleStopSession = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/session/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to stop session')
      }

      setSessionRunning(false)
      setMetrics(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Derived values
  const engagement = metrics?.engagement_score ?? 0
  const confusion = metrics?.confusion_score ?? 0
  const attentive = Math.max(0, engagement)
  const distracted = Math.max(0, 100 - engagement - confusion)
  const status = engagement >= 65 ? 'ATTENTIVE' : engagement >= 35 ? 'NEUTRAL' : 'DISTRACTED'
  const statusColor = engagement >= 65 ? 'text-green-400' : engagement >= 35 ? 'text-yellow-400' : 'text-red-400'
  const now = new Date().toLocaleTimeString('en-US', { hour12: false })

  const pieData = [
    { name: 'Attentive', value: attentive },
    { name: 'Confused', value: confusion },
    { name: 'Distracted', value: distracted },
  ]
  const PIE_COLORS = ['#22c55e', '#f59e0b', '#ef4444']

  const barData = [
    { name: 'Engagement', value: engagement, fill: '#22c55e' },
    { name: 'Confusion', value: confusion, fill: '#06b6d4' },
    { name: 'Attention', value: metrics?.contact_ratio ? metrics.contact_ratio * 100 : 0, fill: '#38bdf8' },
  ]

  const navItems = [
    { id: 'live', label: 'Live Dashboard', icon: '●' },
    { id: 'signals', label: 'Detailed Signals', icon: '✎' },
    { id: 'report', label: 'Session Report', icon: '■' },
    { id: 'system', label: 'System Metrics', icon: '○' },
  ]

  return (
    <div className="flex flex-col gap-0 -mx-8 -my-12">
      {/* ── Top Header Bar ────────────────────────────────────────── */}
      <div className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
            <span className="text-white text-sm font-bold">E</span>
          </div>
          <div>
            <h1 className="text-base font-bold text-white leading-tight">Edge AI Classroom Monitor</h1>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest">MediaPipe · Edge Only · Port 8001 · MJPEG</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {metrics?.face_detected && (
            <span className="px-2 py-0.5 bg-red-500/20 border border-red-500/50 rounded text-[11px] font-bold text-red-400">● Face</span>
          )}
          {metrics && (
            <>
              <span className="px-2 py-0.5 bg-cyan-500/20 border border-cyan-500/50 rounded text-[11px] font-bold text-cyan-400">{metrics.fps.toFixed(0)} FPS</span>
              <span className="px-2 py-0.5 bg-yellow-500/20 border border-yellow-500/50 rounded text-[11px] font-bold text-yellow-300">{metrics.inference_ms.toFixed(0)}ms</span>
            </>
          )}
          <span className="px-2 py-0.5 bg-green-500/20 border border-green-500/50 rounded text-[11px] font-bold text-green-400">● OFFLINE MODE</span>
          <span className="px-2 py-0.5 bg-slate-700 rounded text-[11px] font-bold text-slate-300">{now}</span>
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* ── Left Sidebar Navigation ─────────────────────────────── */}
        <aside className="w-48 bg-slate-900 border-r border-slate-700 py-6 px-4 flex flex-col justify-between shrink-0">
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-4 px-2">Navigation</p>
            <nav className="space-y-1">
              {navItems.map(item => (
                <button
                  key={item.id}
                  onClick={() => setActiveNav(item.id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 transition-colors ${
                    activeNav === item.id
                      ? 'bg-cyan-500/10 border border-cyan-500/40 text-cyan-400 font-semibold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <span className="text-[10px]">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </nav>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 mt-6">
            <p className="text-[10px] font-bold text-amber-400 mb-1">🔒 Privacy First</p>
            <p className="text-[10px] text-green-400 leading-tight">● Offline · On-Device</p>
            <p className="text-[10px] text-red-400 leading-tight">● No Cloud Upload</p>
          </div>
        </aside>

        {/* ── Main Content ─────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto p-6 space-y-5">

          {/* Controls */}
          <div className="flex items-center gap-3">
            {!sessionRunning ? (
              <button
                onClick={handleStartSession}
                disabled={loading}
                className="px-5 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-bold rounded-md transition-colors flex items-center gap-2"
              >
                {loading ? '⏳ Starting...' : '▶ Start Analysis'}
              </button>
            ) : (
              <button
                onClick={handleStopSession}
                disabled={loading}
                className="px-5 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-bold rounded-md transition-colors flex items-center gap-2"
              >
                {loading ? '⏳ Stopping...' : '■ Stop Analysis'}
              </button>
            )}
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${sessionRunning ? 'bg-green-500/20 border border-green-500/50 text-green-400' : 'bg-slate-700 border border-slate-600 text-slate-400'}`}>
              {sessionRunning ? '● Backend Connected' : '○ Disconnected'}
            </span>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3">
              <p className="text-red-400 text-xs font-semibold">Error: {error}</p>
            </div>
          )}

          {/* ── Live Dashboard View ───────────────────────────────── */}
          {activeNav === 'live' && (
            <>
              {/* Video Feed */}
              {sessionRunning && (
                <div className="bg-slate-800/60 rounded-xl border border-slate-700 overflow-hidden">
                  <div className="px-4 py-2 border-b border-slate-700 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400 text-xs">📹</span>
                      <span className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Live AI Camera Feed</span>
                      {metrics && (
                        <span className="text-[10px] text-slate-500 ml-2">Frame #{metrics.frame_number} · {metrics.fps.toFixed(0)} FPS · Annotated by Backend</span>
                      )}
                    </div>
                    <span className="px-2 py-0.5 bg-green-500/20 border border-green-500/50 rounded text-[10px] font-bold text-green-400">● Pipeline Active</span>
                  </div>
                  <div className="relative bg-black">
                    <img
                      src={`${API_BASE}/video_feed`}
                      alt="Live camera feed"
                      className="w-full max-h-[420px] object-contain"
                    />
                    <div className="absolute top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-red-600/90 rounded text-[11px] text-white font-bold">
                      ● LIVE AI
                    </div>
                  </div>
                </div>
              )}

              {/* Metric Cards Row 1 */}
              {metrics && sessionRunning && (
                <>
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Status</p>
                      <p className={`text-xl font-black mt-1 ${statusColor}`}>{status}</p>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Engagement</p>
                      <p className="text-xl font-black text-yellow-400 mt-1">{engagement.toFixed(0)}%</p>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Confusion</p>
                      <p className="text-xl font-black text-green-400 mt-1">{confusion.toFixed(0)}%</p>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">EAR Avg</p>
                      <p className="text-xl font-black text-cyan-400 mt-1">{metrics.ear_avg.toFixed(3)}</p>
                    </div>
                  </div>

                  {/* Metric Cards Row 2 */}
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Eye Contact</p>
                      <p className="text-xl font-black text-cyan-400 mt-1">{(metrics.contact_ratio * 100).toFixed(0)}%</p>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Head Tilt</p>
                      <p className="text-xl font-black text-cyan-400 mt-1">{metrics.tilt_angle_deg.toFixed(1)}°</p>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Blinks/Min</p>
                      <p className="text-xl font-black text-cyan-400 mt-1">{metrics.blinks_per_minute.toFixed(1)}</p>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Blink Count</p>
                      <p className="text-xl font-black text-cyan-400 mt-1">{metrics.blink_count}</p>
                    </div>
                  </div>

                  {/* Score Cards */}
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-5">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Engagement</p>
                      <p className="text-3xl font-black text-green-400 mt-2">{engagement.toFixed(0)}<span className="text-lg">%</span></p>
                      <div className="w-full bg-slate-700 rounded-full h-1 mt-3">
                        <div className="bg-green-400 h-1 rounded-full transition-all" style={{ width: `${Math.min(engagement, 100)}%` }} />
                      </div>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-5">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Attentive</p>
                      <p className="text-3xl font-black text-blue-400 mt-2">{attentive.toFixed(0)}<span className="text-lg">%</span></p>
                      <div className="w-full bg-slate-700 rounded-full h-1 mt-3">
                        <div className="bg-blue-400 h-1 rounded-full transition-all" style={{ width: `${Math.min(attentive, 100)}%` }} />
                      </div>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-5">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Confused</p>
                      <p className="text-3xl font-black text-orange-400 mt-2">{confusion.toFixed(0)}<span className="text-lg">%</span></p>
                      <div className="w-full bg-slate-700 rounded-full h-1 mt-3">
                        <div className="bg-orange-400 h-1 rounded-full transition-all" style={{ width: `${Math.min(confusion, 100)}%` }} />
                      </div>
                    </div>
                    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-5">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Distracted</p>
                      <p className="text-3xl font-black text-red-400 mt-2">{distracted.toFixed(0)}<span className="text-lg">%</span></p>
                      <div className="w-full bg-slate-700 rounded-full h-1 mt-3">
                        <div className="bg-red-400 h-1 rounded-full transition-all" style={{ width: `${Math.min(distracted, 100)}%` }} />
                      </div>
                    </div>
                  </div>

                  {/* Real-time Engagement Timeline */}
                  <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-[11px] text-slate-400 uppercase tracking-wider font-bold">Real-Time Engagement Timeline</p>
                      <p className="text-[10px] text-slate-500">{timelineData.length} samples</p>
                    </div>
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={timelineData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#64748b' }} interval="preserveStartEnd" />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#64748b' }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px', fontSize: '11px' }}
                          labelStyle={{ color: '#94a3b8' }}
                        />
                        <Line type="monotone" dataKey="engagement" stroke="#22d3ee" strokeWidth={2} dot={false} name="Engagement" />
                        <Line type="monotone" dataKey="confusion" stroke="#f59e0b" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Confusion" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* State Distribution & Score Breakdown */}
                  <div className="grid grid-cols-2 gap-4">
                    {/* Pie Chart */}
                    <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5">
                      <p className="text-[11px] text-slate-400 uppercase tracking-wider font-bold mb-2">State Distribution</p>
                      <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                          <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            outerRadius={75}
                            dataKey="value"
                            label={({ name, value }) => `${name} ${value.toFixed(0)}%`}
                            labelLine={false}
                          >
                            {pieData.map((_, i) => (
                              <Cell key={i} fill={PIE_COLORS[i]} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="flex items-center justify-center gap-4 mt-2">
                        {pieData.map((entry, i) => (
                          <span key={i} className="flex items-center gap-1 text-[10px] text-slate-400">
                            <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: PIE_COLORS[i] }} />
                            {entry.name}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Bar Chart */}
                    <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5">
                      <p className="text-[11px] text-slate-400 uppercase tracking-wider font-bold mb-2">Score Breakdown</p>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={barData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} />
                          <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#64748b' }} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px', fontSize: '11px' }}
                          />
                          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                            {barData.map((entry, i) => (
                              <Cell key={i} fill={entry.fill} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}
            </>
          )}

          {/* ── Detailed Signals View ────────────────────────────── */}
          {activeNav === 'signals' && metrics && sessionRunning && (
            <div className="space-y-4">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider font-bold">Detailed Signals</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5 space-y-3">
                  <p className="text-sm font-bold text-white">Eye Metrics</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-slate-400">EAR Left</span><span className="text-cyan-400 font-bold">{metrics.ear_left.toFixed(3)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">EAR Right</span><span className="text-cyan-400 font-bold">{metrics.ear_right.toFixed(3)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">EAR Average</span><span className="text-cyan-400 font-bold">{metrics.ear_avg.toFixed(3)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Blinking</span><span className={metrics.is_blinking ? 'text-yellow-400 font-bold' : 'text-green-400 font-bold'}>{metrics.is_blinking ? 'Yes' : 'No'}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Sleeping</span><span className={metrics.is_sleeping ? 'text-red-400 font-bold' : 'text-green-400 font-bold'}>{metrics.is_sleeping ? '⚠ Yes' : 'No'}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Eye Contact</span><span className="text-blue-400 font-bold">{metrics.eye_contact ? 'Yes' : 'No'}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Contact Ratio</span><span className="text-blue-400 font-bold">{(metrics.contact_ratio * 100).toFixed(1)}%</span></div>
                  </div>
                </div>
                <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5 space-y-3">
                  <p className="text-sm font-bold text-white">Head & Gesture</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-slate-400">Tilt Angle</span><span className="text-cyan-400 font-bold">{metrics.tilt_angle_deg.toFixed(1)}°</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Is Tilted</span><span className={metrics.is_tilted ? 'text-yellow-400 font-bold' : 'text-green-400 font-bold'}>{metrics.is_tilted ? 'Yes' : 'No'}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Head Nod</span><span className="text-green-400 font-bold">{metrics.head_nod ? '✓ Detected' : '–'}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Head Shake</span><span className="text-orange-400 font-bold">{metrics.head_shake ? '✓ Detected' : '–'}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Blinks</span><span className="text-cyan-400 font-bold">{metrics.blink_count}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Blinks/Min</span><span className="text-cyan-400 font-bold">{metrics.blinks_per_minute.toFixed(1)}</span></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Session Report View ──────────────────────────────── */}
          {activeNav === 'report' && (
            <div className="space-y-4">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider font-bold">Session Report</p>
              {timelineData.length > 0 ? (
                <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5 space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase">Samples Collected</p>
                      <p className="text-2xl font-black text-white">{timelineData.length}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase">Avg Engagement</p>
                      <p className="text-2xl font-black text-green-400">
                        {(timelineData.reduce((a, b) => a + b.engagement, 0) / timelineData.length).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase">Avg Confusion</p>
                      <p className="text-2xl font-black text-orange-400">
                        {(timelineData.reduce((a, b) => a + b.confusion, 0) / timelineData.length).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={timelineData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#64748b' }} interval="preserveStartEnd" />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#64748b' }} />
                      <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px', fontSize: '11px' }} />
                      <Line type="monotone" dataKey="engagement" stroke="#22d3ee" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="confusion" stroke="#f59e0b" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-8 text-center">
                  <p className="text-slate-400">No session data yet. Start analysis to collect metrics.</p>
                </div>
              )}
            </div>
          )}

          {/* ── System Metrics View ──────────────────────────────── */}
          {activeNav === 'system' && metrics && sessionRunning && (
            <div className="space-y-4">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider font-bold">System Metrics</p>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5 text-center">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider">FPS</p>
                  <p className="text-3xl font-black text-cyan-400 mt-2">{metrics.fps.toFixed(1)}</p>
                </div>
                <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5 text-center">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider">Inference</p>
                  <p className="text-3xl font-black text-yellow-300 mt-2">{metrics.inference_ms.toFixed(1)}<span className="text-lg">ms</span></p>
                </div>
                <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5 text-center">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider">Frames</p>
                  <p className="text-3xl font-black text-purple-400 mt-2">{metrics.frame_number}</p>
                </div>
              </div>
              <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-5">
                <p className="text-sm font-bold text-white mb-3">Detection Status</p>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-slate-400">Face Detected</span><span className={metrics.face_detected ? 'text-green-400 font-bold' : 'text-red-400 font-bold'}>{metrics.face_detected ? '✓ Yes' : '✗ No'}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Pipeline</span><span className="text-green-400 font-bold">● Running</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Backend</span><span className="text-green-400 font-bold">Port 8001</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Mode</span><span className="text-cyan-400 font-bold">Edge / Offline</span></div>
                </div>
              </div>
            </div>
          )}

          {/* Idle state */}
          {!sessionRunning && !metrics && activeNav === 'live' && (
            <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-12 text-center space-y-3">
              <p className="text-4xl">📹</p>
              <p className="text-lg text-slate-300 font-semibold">Edge AI Classroom Monitor</p>
              <p className="text-sm text-slate-400">Click "Start Analysis" to begin real-time engagement monitoring</p>
            </div>
          )}

          {(activeNav !== 'live' && activeNav !== 'report') && !sessionRunning && (
            <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-8 text-center">
              <p className="text-slate-400">Start analysis to see {activeNav === 'signals' ? 'detailed signals' : 'system metrics'}.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
