import { useMemo } from 'react'

export default function OptimizationMetrics({ result }) {
  const compressionRatio = useMemo(() => {
    if (result.optimizedSize === 0) return 0
    return (result.originalSize / result.optimizedSize).toFixed(2)
  }, [result])

  const metrics = [
    {
      label: 'Original Size',
      value: `${result.originalSize.toFixed(2)} MB`,
      icon: '📦',
      color: 'from-slate-500 to-slate-600',
    },
    {
      label: 'Optimized Size',
      value: `${result.optimizedSize.toFixed(2)} MB`,
      icon: '⚡',
      color: 'from-cyan-500 to-blue-600',
    },
    {
      label: 'Size Reduction',
      value: `${result.sizeReduction}%`,
      icon: '📉',
      color: 'from-green-500 to-emerald-600',
    },
    {
      label: 'Compression Ratio',
      value: `${compressionRatio}x`,
      icon: '🎯',
      color: 'from-purple-500 to-pink-600',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/50 rounded-xl p-6 flex items-start gap-4">
        <span className="text-3xl">✓</span>
        <div>
          <h4 className="font-bold text-green-400 mb-1">Optimization Complete!</h4>
          <p className="text-green-300">Your model has been successfully optimized for edge deployment.</p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {metrics.map((metric, idx) => (
          <div
            key={idx}
            className={`bg-gradient-to-br ${metric.color} rounded-xl p-6 backdrop-blur border border-white/10`}
          >
            <div className="flex items-start justify-between mb-3">
              <span className="text-3xl">{metric.icon}</span>
            </div>
            <p className="text-slate-300 text-sm mb-2">{metric.label}</p>
            <p className="text-white text-2xl font-bold">{metric.value}</p>
          </div>
        ))}
      </div>

      {/* Details */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 space-y-4">
        <h4 className="text-lg font-bold text-white">Optimization Details</h4>

        <div className="space-y-3">
          {/* Original File */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-700">
            <span className="text-slate-400">Original File</span>
            <span className="text-white font-mono">{result.originalFileName}</span>
          </div>

          {/* Optimized File */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-700">
            <span className="text-slate-400">Optimized File</span>
            <span className="text-white font-mono">{result.optimizedFileName}</span>
          </div>

          {/* Status */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-700">
            <span className="text-slate-400">Status</span>
            <span className="text-green-400 font-semibold flex items-center gap-2">
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              {result.status}
            </span>
          </div>

          {/* Space Saved */}
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Space Saved</span>
            <span className="text-white font-bold">
              {(result.originalSize - result.optimizedSize).toFixed(2)} MB
            </span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <div className="mb-4 flex items-end justify-between">
          <span className="text-white font-semibold">Compression Progress</span>
          <span className="text-slate-400 text-sm">
            {result.sizeReduction}% Reduced
          </span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-green-500 to-emerald-500 h-full transition-all duration-500"
            style={{ width: `${Math.min(result.sizeReduction, 100)}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}
