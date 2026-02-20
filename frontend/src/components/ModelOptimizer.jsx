import { useState } from 'react'
import FileUpload from './FileUpload'
import OptimizationMetrics from './OptimizationMetrics'

export default function ModelOptimizer() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile)
    setError(null)
  }

  const handleOptimize = async () => {
    if (!file) {
      setError('Please select a model file first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:5000/api/optimize', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Optimization failed')
      }

      const data = await response.json()
      setResult(data)
      setFile(null)
    } catch (err) {
      setError(err.message || 'Failed to optimize model')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="mb-12">
        <h2 className="text-4xl font-bold text-white mb-3">Model Optimizer</h2>
        <p className="text-slate-400 text-lg">Upload your PyTorch model and optimize it for edge deployment</p>
      </div>

      {/* Upload Section */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur">
        <h3 className="text-xl font-bold text-white mb-6">Step 1: Upload Model</h3>
        <FileUpload file={file} onFileSelect={handleFileSelect} />
      </div>

      {/* Action Button */}
      <div className="flex gap-4">
        <button
          onClick={handleOptimize}
          disabled={!file || loading}
          className={`flex-1 py-4 px-8 rounded-xl font-bold text-lg transition-all duration-300 flex items-center justify-center gap-3 ${
            loading || !file
              ? 'bg-slate-600 text-slate-400 cursor-not-allowed opacity-50'
              : 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:shadow-lg hover:shadow-cyan-500/50 active:scale-95'
          }`}
        >
          {loading ? (
            <>
              <span className="animate-spin">⚙️</span>
              Optimizing Model...
            </>
          ) : (
            <>
              <span>⚡</span>
              Start Optimization
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-6 flex items-start gap-4">
          <span className="text-2xl">⚠️</span>
          <div>
            <h4 className="font-bold text-red-400 mb-1">Optimization Failed</h4>
            <p className="text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div className="space-y-6">
          <OptimizationMetrics result={result} />
        </div>
      )}
    </div>
  )
}
