import { useRef } from 'react'

export default function FileUpload({ file, onFileSelect }) {
  const fileInputRef = useRef(null)

  const handleDrop = (e) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile && droppedFile.name.endsWith('.pt')) {
      onFileSelect(droppedFile)
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      onFileSelect(selectedFile)
    }
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      onClick={handleClick}
      className="border-2 border-dashed border-slate-600 rounded-2xl p-12 text-center cursor-pointer hover:border-cyan-400/50 hover:bg-slate-700/30 transition-all duration-300 group"
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pt,.pth"
        onChange={handleFileChange}
        className="hidden"
      />

      {file ? (
        <div className="space-y-3">
          <div className="text-5xl">✓</div>
          <div>
            <p className="text-lg font-bold text-white">{file.name}</p>
            <p className="text-slate-400 text-sm mt-1">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
          <p className="text-xs text-slate-500 mt-4">Click to change file</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-6xl group-hover:scale-110 transition-transform">📦</div>
          <div>
            <p className="text-xl font-bold text-white mb-2">Drop your model here</p>
            <p className="text-slate-400">or click to browse</p>
          </div>
          <p className="text-xs text-slate-500 mt-4">Supported formats: .pt, .pth</p>
        </div>
      )}
    </div>
  )
}
