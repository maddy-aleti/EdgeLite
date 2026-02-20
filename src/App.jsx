import { useState, useEffect, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, Legend
} from "recharts";

// ─── Palette ────────────────────────────────────────────────────────────────
const C = {
  bg: "#090e1a",
  surface: "#0f1829",
  card: "#131f33",
  border: "#1e2f4a",
  accent: "#00d4ff",
  green: "#00e676",
  yellow: "#ffeb3b",
  red: "#ff4444",
  orange: "#ff9800",
  muted: "#4a6080",
  text: "#c8ddf5",
  textDim: "#5a7a9a",
};

const PIE_COLORS = [C.green, C.yellow, C.red];

// ─── Helpers ─────────────────────────────────────────────────────────────────
const rand = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const fmt = (n) => (n < 10 ? "0" + n : n);

function useClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return `${fmt(time.getHours())}:${fmt(time.getMinutes())}:${fmt(time.getSeconds())}`;
}

function AnimCounter({ target, duration = 800 }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / (duration / 16);
    const id = setInterval(() => {
      start += step;
      if (start >= target) { setVal(target); clearInterval(id); }
      else setVal(Math.floor(start));
    }, 16);
    return () => clearInterval(id);
  }, [target]);
  return <>{val}</>;
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: "live", label: "Live Dashboard", icon: "⬤" },
  { id: "session", label: "Session Report", icon: "📋" },
  { id: "opt", label: "Optimization Metrics", icon: "⚙" },
  { id: "settings", label: "Settings", icon: "🛠" },
];

function Sidebar({ active, setActive }) {
  return (
    <aside style={{ width: 220, background: C.surface, borderRight: `1px solid ${C.border}`, padding: "32px 0", display: "flex", flexDirection: "column", gap: 4, flexShrink: 0 }}>
      <div style={{ padding: "0 20px 24px", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 11, color: C.muted, letterSpacing: 3, textTransform: "uppercase", marginBottom: 4 }}>Navigation</div>
      </div>
      {NAV_ITEMS.map(item => (
        <button key={item.id} onClick={() => setActive(item.id)}
          style={{
            display: "flex", alignItems: "center", gap: 12, padding: "12px 20px",
            background: active === item.id ? `${C.accent}15` : "transparent",
            border: "none", borderLeft: active === item.id ? `3px solid ${C.accent}` : "3px solid transparent",
            color: active === item.id ? C.accent : C.textDim, cursor: "pointer",
            fontSize: 13, fontFamily: "inherit", textAlign: "left", transition: "all .2s",
          }}>
          <span style={{ fontSize: 10 }}>{item.icon}</span>
          {item.label}
        </button>
      ))}
      <div style={{ marginTop: "auto", padding: "20px", borderTop: `1px solid ${C.border}` }}>
        <div style={{ background: `${C.green}15`, border: `1px solid ${C.green}40`, borderRadius: 8, padding: "10px 12px" }}>
          <div style={{ fontSize: 10, color: C.green, fontWeight: 700, letterSpacing: 1 }}>🔒 NO CLOUD UPLOADS</div>
          <div style={{ fontSize: 10, color: C.muted, marginTop: 4 }}>Fully Offline AI</div>
        </div>
      </div>
    </aside>
  );
}

// ─── Metric Card ─────────────────────────────────────────────────────────────
function MetricCard({ label, value, suffix = "%", color, icon }) {
  return (
    <div style={{
      background: C.card, border: `1px solid ${C.border}`, borderRadius: 16,
      padding: "20px 24px", flex: 1, minWidth: 140,
      boxShadow: `0 0 24px ${color}18`, position: "relative", overflow: "hidden"
    }}>
      <div style={{ position: "absolute", top: -20, right: -10, fontSize: 72, opacity: .05 }}>{icon}</div>
      <div style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: 2, marginBottom: 10 }}>{label}</div>
      <div style={{ fontSize: 42, fontWeight: 800, color, lineHeight: 1 }}>
        <AnimCounter target={value} /><span style={{ fontSize: 20 }}>{suffix}</span>
      </div>
      <div style={{ marginTop: 10, height: 3, background: C.border, borderRadius: 2 }}>
        <div style={{ height: "100%", width: `${Math.min(value, 100)}%`, background: color, borderRadius: 2, transition: "width 1s" }} />
      </div>
    </div>
  );
}

// ─── Heatmap ─────────────────────────────────────────────────────────────────
const STATES = ["attentive", "attentive", "attentive", "confused", "distracted"];
const stateColor = { attentive: C.green, confused: C.yellow, distracted: C.red };

function Heatmap() {
  const [grid, setGrid] = useState(() =>
    Array.from({ length: 5 }, () => Array.from({ length: 5 }, () => STATES[rand(0, 4)]))
  );
  useEffect(() => {
    const id = setInterval(() => {
      setGrid(g => g.map(row => row.map(cell =>
        Math.random() > 0.85 ? STATES[rand(0, 4)] : cell
      )));
    }, 2000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 8 }}>
      {grid.map((row, r) => row.map((state, c) => (
        <div key={`${r}-${c}`} title={`Student ${r * 5 + c + 1}: ${state}`}
          style={{
            aspectRatio: "1", borderRadius: 10, background: stateColor[state],
            opacity: 0.8, transition: "background 0.8s, opacity 0.8s",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16, cursor: "default",
            boxShadow: `0 0 12px ${stateColor[state]}60`
          }}>
          {state === "attentive" ? "😊" : state === "confused" ? "😕" : "😴"}
        </div>
      )))}
    </div>
  );
}

// ─── Progress Bar ─────────────────────────────────────────────────────────────
function ProgressBar({ label, value, max = 100, color = C.accent, unit = "%" }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5, fontSize: 12, color: C.text }}>
        <span>{label}</span>
        <span style={{ color }}>{value}{unit}</span>
      </div>
      <div style={{ height: 6, background: C.border, borderRadius: 3 }}>
        <div style={{ height: "100%", width: `${(value / max) * 100}%`, background: color, borderRadius: 3, transition: "width .8s" }} />
      </div>
    </div>
  );
}

// ─── Confusion Alert ──────────────────────────────────────────────────────────
function ConfusionAlert({ confusion }) {
  if (confusion <= 50) return null;
  return (
    <div style={{
      background: `${C.red}18`, border: `1px solid ${C.red}60`, borderRadius: 12,
      padding: "14px 20px", display: "flex", alignItems: "center", gap: 12,
      animation: "pulse 1.5s infinite", marginBottom: 20
    }}>
      <span style={{ fontSize: 22 }}>⚠️</span>
      <div>
        <div style={{ color: C.red, fontWeight: 700, fontSize: 14 }}>Confusion Spike Detected</div>
        <div style={{ color: C.textDim, fontSize: 12 }}>{confusion}% of students show confusion signals</div>
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
function LiveDashboard() {
  const [metrics, setMetrics] = useState({ attention: 72, attentive: 60, confused: 25, distracted: 15, sleepy: 2 });
  const [timeline, setTimeline] = useState(() => {
    const now = Date.now();
    return Array.from({ length: 20 }, (_, i) => ({
      t: new Date(now - (19 - i) * 3000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      score: rand(55, 90)
    }));
  });
  const [cpu, setCpu] = useState(38);
  const [fps, setFps] = useState(29);

  useEffect(() => {
    const id = setInterval(() => {
      const att = rand(50, 80), conf = rand(15, 35), dist = Math.max(0, 100 - att - conf);
      setMetrics({ attention: rand(55, 90), attentive: att, confused: conf, distracted: dist, sleepy: rand(0, 5) });
      setTimeline(prev => [...prev.slice(-19), {
        t: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
        score: rand(50, 95)
      }]);
      setCpu(rand(25, 65));
      setFps(rand(24, 32));
    }, 2500);
    return () => clearInterval(id);
  }, []);

  const pieData = [
    { name: "Attentive", value: metrics.attentive },
    { name: "Confused", value: metrics.confused },
    { name: "Distracted", value: metrics.distracted },
  ];
  const barData = [
    { topic: "Math", engagement: rand(55, 80) },
    { topic: "Physics", engagement: rand(40, 70) },
    { topic: "Programming", engagement: rand(65, 90) },
  ];

  return (
    <div style={{ padding: "24px", overflowY: "auto", flex: 1 }}>
      <ConfusionAlert confusion={metrics.confused} />

      {/* Hero Cards */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
        <MetricCard label="Attention Score" value={metrics.attention} color={C.accent} icon="🧠" />
        <MetricCard label="Attentive" value={metrics.attentive} color={C.green} icon="✅" />
        <MetricCard label="Confused" value={metrics.confused} color={C.yellow} icon="❓" />
        <MetricCard label="Distracted" value={metrics.distracted} color={C.orange} icon="📱" />
        <MetricCard label="Sleepy" value={metrics.sleepy} suffix="" color={C.red} icon="😴" />
      </div>

      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        {/* Timeline */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 20, gridColumn: "1 / -1" }}>
          <div style={{ fontSize: 13, color: C.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 16 }}>Real-Time Attention Timeline</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="t" tick={{ fill: C.muted, fontSize: 10 }} interval={4} />
              <YAxis domain={[0, 100]} tick={{ fill: C.muted, fontSize: 10 }} />
              <Tooltip contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, color: C.text }} />
              <Line type="monotone" dataKey="score" stroke={C.accent} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pie */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 20 }}>
          <div style={{ fontSize: 13, color: C.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 16 }}>Classroom Mood Distribution</div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={75} dataKey="value" label={({ name, value }) => `${name} ${value}%`}
                labelLine={{ stroke: C.muted }} >
                {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 20 }}>
          <div style={{ fontSize: 13, color: C.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 16 }}>Engagement Trend by Topic</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="topic" tick={{ fill: C.muted, fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: C.muted, fontSize: 10 }} />
              <Tooltip contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8 }} />
              <Bar dataKey="engagement" fill={C.accent} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Heatmap + Optimization */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24 }}>
          <div style={{ fontSize: 13, color: C.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 16 }}>Classroom Heatmap (5×5)</div>
          <Heatmap />
          <div style={{ display: "flex", gap: 16, marginTop: 16, fontSize: 11, color: C.muted }}>
            {[["green", "Attentive"], ["yellow", "Confused"], ["red", "Distracted"]].map(([c, l]) => (
              <span key={l} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: C[c], display: "inline-block" }} />{l}
              </span>
            ))}
          </div>
        </div>

        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24 }}>
          <div style={{ fontSize: 13, color: C.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 16 }}>Optimization Metrics</div>
          <ProgressBar label="Model Size" value={8} max={50} color={C.green} unit=" MB" />
          <ProgressBar label="CPU Usage" value={cpu} color={cpu > 50 ? C.orange : C.accent} />
          <ProgressBar label="FPS" value={fps} max={60} color={C.green} unit=" fps" />
          <ProgressBar label="Memory Usage" value={rand(30, 55)} color={C.accent} />
          <div style={{ marginTop: 20, padding: "12px 16px", background: `${C.green}10`, borderRadius: 10, border: `1px solid ${C.green}30` }}>
            <div style={{ fontSize: 11, color: C.green, fontWeight: 700 }}>🔒 PRIVACY SHIELD ACTIVE</div>
            <div style={{ fontSize: 11, color: C.muted, marginTop: 4 }}>No Cloud Uploads · Fully Offline AI · GDPR Compliant</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Session Report ───────────────────────────────────────────────────────────
const SESSION_DATA = [
  { topic: "Math", confusion: 65, engagement: 55 },
  { topic: "Physics", confusion: 20, engagement: 75 },
  { topic: "Programming", confusion: 15, engagement: 88 },
  { topic: "History", confusion: 42, engagement: 62 },
  { topic: "Chemistry", confusion: 58, engagement: 48 },
];

function SessionReport() {
  return (
    <div style={{ padding: 24, overflowY: "auto", flex: 1 }}>
      <div style={{ fontSize: 22, fontWeight: 800, color: C.text, marginBottom: 24 }}>Session Report</div>
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24, marginBottom: 20 }}>
        <div style={{ fontSize: 13, color: C.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 20 }}>Topic vs Confusion Rate</div>
        {SESSION_DATA.map(d => (
          <div key={d.topic} style={{ marginBottom: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13, color: C.text }}>
              <span>{d.topic}</span>
              <span style={{ color: d.confusion > 50 ? C.red : d.confusion > 30 ? C.yellow : C.green }}>{d.confusion}% confused</span>
            </div>
            <div style={{ height: 8, background: C.border, borderRadius: 4 }}>
              <div style={{ height: "100%", width: `${d.confusion}%`, background: d.confusion > 50 ? C.red : d.confusion > 30 ? C.yellow : C.green, borderRadius: 4, transition: "width 1s" }} />
            </div>
          </div>
        ))}
      </div>
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24 }}>
        <div style={{ fontSize: 13, color: C.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 20 }}>Topic Engagement Rate</div>
        {SESSION_DATA.map(d => (
          <div key={d.topic} style={{ marginBottom: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13, color: C.text }}>
              <span>{d.topic}</span>
              <span style={{ color: C.accent }}>{d.engagement}%</span>
            </div>
            <div style={{ height: 8, background: C.border, borderRadius: 4 }}>
              <div style={{ height: "100%", width: `${d.engagement}%`, background: C.accent, borderRadius: 4 }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Optimization Metrics Page ────────────────────────────────────────────────
function OptimizationMetrics() {
  const [metrics, setMetrics] = useState({ cpu: 38, fps: 29, mem: 42, inf: 24 });
  useEffect(() => {
    const id = setInterval(() => setMetrics({ cpu: rand(20, 70), fps: rand(24, 32), mem: rand(30, 60), inf: rand(18, 35) }), 2000);
    return () => clearInterval(id);
  }, []);
  return (
    <div style={{ padding: 24, overflowY: "auto", flex: 1 }}>
      <div style={{ fontSize: 22, fontWeight: 800, color: C.text, marginBottom: 24 }}>Optimization Metrics</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {[
          { label: "CPU Usage", value: metrics.cpu, max: 100, unit: "%", color: metrics.cpu > 60 ? C.red : C.accent },
          { label: "FPS", value: metrics.fps, max: 60, unit: " fps", color: C.green },
          { label: "Memory Usage", value: metrics.mem, max: 100, unit: "%", color: metrics.mem > 70 ? C.orange : C.accent },
          { label: "Inference Time", value: metrics.inf, max: 100, unit: " ms", color: C.yellow },
          { label: "Model Size", value: 8, max: 50, unit: " MB", color: C.green },
          { label: "Battery Impact", value: 12, max: 100, unit: "%", color: C.green },
        ].map(m => (
          <div key={m.label} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24 }}>
            <div style={{ fontSize: 12, color: C.muted, textTransform: "uppercase", letterSpacing: 2, marginBottom: 10 }}>{m.label}</div>
            <div style={{ fontSize: 36, fontWeight: 800, color: m.color, marginBottom: 12 }}>{m.value}<span style={{ fontSize: 14 }}>{m.unit}</span></div>
            <div style={{ height: 6, background: C.border, borderRadius: 3 }}>
              <div style={{ height: "100%", width: `${(m.value / m.max) * 100}%`, background: m.color, borderRadius: 3, transition: "width .8s" }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Settings ──────────────────────────────────────────────────────────────────
function Settings() {
  const [vals, setVals] = useState({ interval: 3, gridSize: 25, threshold: 50, sound: true });
  return (
    <div style={{ padding: 24, overflowY: "auto", flex: 1 }}>
      <div style={{ fontSize: 22, fontWeight: 800, color: C.text, marginBottom: 24 }}>Settings</div>
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24, maxWidth: 480 }}>
        {[
          { label: "Update Interval (s)", key: "interval", min: 1, max: 10 },
          { label: "Grid Size (students)", key: "gridSize", min: 9, max: 49 },
          { label: "Alert Threshold (%)", key: "threshold", min: 10, max: 90 },
        ].map(s => (
          <div key={s.key} style={{ marginBottom: 24 }}>
            <label style={{ fontSize: 13, color: C.text, display: "block", marginBottom: 8 }}>{s.label}</label>
            <input type="range" min={s.min} max={s.max} value={vals[s.key]}
              onChange={e => setVals(v => ({ ...v, [s.key]: +e.target.value }))}
              style={{ width: "100%", accentColor: C.accent }} />
            <span style={{ color: C.accent, fontSize: 12 }}>{vals[s.key]}</span>
          </div>
        ))}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 13, color: C.text }}>Alert Sound</span>
          <button onClick={() => setVals(v => ({ ...v, sound: !v.sound }))}
            style={{ width: 48, height: 26, borderRadius: 13, background: vals.sound ? C.accent : C.border, border: "none", cursor: "pointer", transition: "all .3s", position: "relative" }}>
            <span style={{ position: "absolute", top: 3, left: vals.sound ? 25 : 3, width: 20, height: 20, borderRadius: "50%", background: "white", transition: "left .3s" }} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [active, setActive] = useState("live");
  const clock = useClock();

  const pages = { live: <LiveDashboard />, session: <SessionReport />, opt: <OptimizationMetrics />, settings: <Settings /> };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Sora:wght@400;600;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${C.bg}; color: ${C.text}; font-family: 'Sora', sans-serif; }
        ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: ${C.surface}; } ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 3px; }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }
        @keyframes blink { 0%,100% { background: ${C.red}30; } 50% { background: ${C.red}60; } }
      `}</style>
      <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
        {/* Navbar */}
        <header style={{
          background: C.surface, borderBottom: `1px solid ${C.border}`,
          padding: "0 24px", height: 60, display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: `linear-gradient(135deg, ${C.accent}, #0066ff)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>🧠</div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 800, color: C.text, letterSpacing: -.3 }}>Offline Classroom Intelligence Dashboard</div>
              <div style={{ fontSize: 10, color: C.muted, letterSpacing: 1 }}>AI-POWERED · EDGE ONLY</div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ background: `${C.green}20`, border: `1px solid ${C.green}50`, borderRadius: 20, padding: "5px 14px", fontSize: 11, color: C.green, fontWeight: 700, letterSpacing: 1, display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: C.green, display: "inline-block", animation: "pulse 2s infinite" }} />
              OFFLINE MODE ACTIVE
            </div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 14, color: C.accent, background: `${C.accent}10`, padding: "4px 12px", borderRadius: 8, border: `1px solid ${C.accent}30` }}>{clock}</div>
          </div>
        </header>

        {/* Body */}
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          <Sidebar active={active} setActive={setActive} />
          <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {pages[active]}
          </main>
        </div>
      </div>
    </>
  );
}
