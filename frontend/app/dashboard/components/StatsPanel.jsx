'use client'
import { formatTime } from '@/lib/timezone'

export default function StatsPanel({ latestData, isConnected, selectedTF, timezone }) {
  const rendlog = latestData?.rendlog
  const senal = rendlog?.senal
  const zScore = rendlog?.z_score

  return (
    <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
      <div className="bg-dark-card rounded-xl border border-dark-border p-5">
        <p className="text-xs text-dark-textGray uppercase tracking-wider mb-1">Timeframe</p>
        <p className="text-2xl font-bold text-accent">{selectedTF || '--'}</p>
        <p className="text-xs text-dark-textGray mt-1">
          {formatTime(latestData?.data_timestamp, timezone, { includeDate: true, includeSeconds: true })}
        </p>
      </div>

      <div className="bg-dark-card rounded-xl border border-dark-border p-5">
        <p className="text-xs text-dark-textGray uppercase tracking-wider mb-1">Z-Score</p>
        <p className="text-2xl font-bold text-white font-mono">
          {zScore != null ? zScore.toFixed(4) : '--'}
        </p>
      </div>

      <div className="bg-dark-card rounded-xl border border-dark-border p-5">
        <p className="text-xs text-dark-textGray uppercase tracking-wider mb-1">Senal</p>
        <p className={`text-2xl font-bold ${
          senal === 'COMPRA' ? 'text-success' :
          senal === 'VENTA' ? 'text-danger' :
          'text-dark-textGray'
        }`}>
          {senal || 'Sin senal'}
        </p>
      </div>

      <div className="bg-dark-card rounded-xl border border-dark-border p-5">
        <p className="text-xs text-dark-textGray uppercase tracking-wider mb-1">Realtime</p>
        <div className="flex items-center space-x-2">
          <span className={`inline-block w-2.5 h-2.5 rounded-full ${
            isConnected ? 'bg-success animate-pulse' : 'bg-danger'
          }`} />
          <p className={`text-lg font-semibold ${
            isConnected ? 'text-success' : 'text-danger'
          }`}>
            {isConnected ? 'Conectado' : 'Desconectado'}
          </p>
        </div>
      </div>
    </div>
  )
}
