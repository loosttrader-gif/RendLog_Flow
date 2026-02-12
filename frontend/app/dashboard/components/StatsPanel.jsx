'use client'

function formatTimestamp(timestamp) {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  return date.toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export default function StatsPanel({ latestData, isConnected, selectedTF }) {
  const rendlog = latestData?.rendlog
  const senal = rendlog?.senal
  const zScore = rendlog?.z_score

  return (
    <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
      {/* Timeframe activo + última actualización */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <p className="text-sm text-gray-500 mb-1">Timeframe</p>
        <p className="text-2xl font-bold text-blue-600">{selectedTF || '--'}</p>
        <p className="text-xs text-gray-400 mt-1">
          {formatTimestamp(latestData?.data_timestamp)}
        </p>
      </div>

      {/* Z-Score */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <p className="text-sm text-gray-500 mb-1">Z-Score</p>
        <p className="text-2xl font-bold text-gray-800 font-mono">
          {zScore != null ? zScore.toFixed(4) : '--'}
        </p>
      </div>

      {/* Señal */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <p className="text-sm text-gray-500 mb-1">Señal</p>
        <p className={`text-2xl font-bold ${
          senal === 'COMPRA' ? 'text-green-500' :
          senal === 'VENTA' ? 'text-red-500' :
          'text-gray-400'
        }`}>
          {senal || 'Sin señal'}
        </p>
      </div>

      {/* Estado conexión */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <p className="text-sm text-gray-500 mb-1">Realtime</p>
        <div className="flex items-center space-x-2">
          <span className={`inline-block w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`} />
          <p className={`text-lg font-semibold ${
            isConnected ? 'text-green-600' : 'text-red-600'
          }`}>
            {isConnected ? 'Conectado' : 'Desconectado'}
          </p>
        </div>
      </div>
    </div>
  )
}
