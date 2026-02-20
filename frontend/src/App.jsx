import { useState } from 'react'
import ModelOptimizer from './components/ModelOptimizer'
import EngagementAnalyzer from './components/EngagementAnalyzer'

export default function App() {
  const [activeTab, setActiveTab] = useState('optimizer')

  const navItems = [
    {
      id: 'optimizer',
      label: 'Model Optimizer',
      icon: '⚡',
      description: 'Optimize PyTorch models'
    },
    {
      id: 'engagement',
      label: 'Engagement Analyzer',
      icon: '📊',
      description: 'Analyze student engagement'
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Top Navbar */}
      <nav className="bg-slate-900 border-b border-slate-700 sticky top-0 z-50">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-xl">
              🚀
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">EdgeLite</h1>
              <p className="text-xs text-slate-400">Edge AI Suite</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="px-3 py-1 bg-green-500/20 border border-green-500/50 rounded-full">
              <span className="text-xs font-semibold text-green-400">● ONLINE</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex flex-1">
        {/* Left Sidebar Navigation */}
        <aside className="w-64 bg-slate-900 border-r border-slate-700 overflow-y-auto">
          <div className="p-6 space-y-4">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Tools</h2>
            
            <nav className="space-y-2">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-all duration-200 group ${
                    activeTab === item.id
                      ? 'bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-500/50 text-white'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{item.icon}</span>
                    <div className="flex-1">
                      <div className="font-semibold text-sm">{item.label}</div>
                      <div className="text-xs text-slate-500 group-hover:text-slate-400">
                        {item.description}
                      </div>
                    </div>
                    {activeTab === item.id && (
                      <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
                    )}
                  </div>
                </button>
              ))}
            </nav>

            {/* Sidebar Footer Info */}
            <div className="pt-6 mt-6 border-t border-slate-700">
              <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4 space-y-2">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Backend Status</p>
                  <p className="text-sm text-green-400 font-semibold flex items-center gap-2 mt-1">
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                    Connected
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Version</p>
                  <p className="text-sm text-slate-300 mt-1">v1.0.0</p>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-6xl mx-auto px-8 py-12">
              {activeTab === 'optimizer' && <ModelOptimizer />}
              {activeTab === 'engagement' && <EngagementAnalyzer />}
            </div>
          </div>

          {/* Footer */}
          <footer className="bg-slate-900 border-t border-slate-700 mt-auto">
            <div className="max-w-6xl mx-auto px-8 py-8">
              <div className="grid grid-cols-3 gap-8 mb-8">
                <div>
                  <h3 className="font-bold text-white mb-3">About</h3>
                  <p className="text-sm text-slate-400">EdgeLite is a comprehensive suite for edge AI optimization and analysis.</p>
                </div>
                <div>
                  <h3 className="font-bold text-white mb-3">Tools</h3>
                  <ul className="text-sm text-slate-400 space-y-2">
                    <li>⚡ Model Optimization</li>
                    <li>📊 Engagement Analysis</li>
                    <li>🎯 Real-time Inference</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-bold text-white mb-3">Status</h3>
                  <p className="text-sm text-slate-400">Backend: <span className="text-green-400 font-semibold">Connected</span></p>
                  <p className="text-sm text-slate-400">FastAPI: <span className="text-green-400 font-semibold">Ready</span></p>
                </div>
              </div>
              <div className="border-t border-slate-700 pt-6 text-center text-sm text-slate-400">
                <p>&copy; 2026 EdgeLite. Built for on-device optimization and analysis.</p>
              </div>
            </div>
          </footer>
        </main>
      </div>
    </div>
  )
}
