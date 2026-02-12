'use client'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Scatter,
  ComposedChart,
} from 'recharts'

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}

function CustomDot({ cx, cy, payload }) {
  if (!payload || !payload.rendlog) return null
  const { log_return, banda_2sigma_superior, banda_2sigma_inferior } = payload.rendlog

  if (log_return > banda_2sigma_superior) {
    return <circle cx={cx} cy={cy} r={5} fill="#ef4444" stroke="#fff" strokeWidth={1} />
  }
  if (log_return < banda_2sigma_inferior) {
    return <circle cx={cx} cy={cy} r={5} fill="#22c55e" stroke="#fff" strokeWidth={1} />
  }
  return null
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null

  const item = payload[0]?.payload
  if (!item) return null

  const rendlog = item.rendlog
  return (
    <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200 text-sm">
      <p className="font-semibold text-gray-800 mb-1">{formatTime(item.data_timestamp)}</p>
      <p className="text-gray-600">Log Return: <span className="font-mono">{rendlog.log_return?.toFixed(6)}</span></p>
      <p className="text-gray-600">Z-Score: <span className="font-mono">{rendlog.z_score?.toFixed(4)}</span></p>
      <p className="text-gray-600">
        Señal:{' '}
        <span className={
          rendlog.senal === 'COMPRA' ? 'text-green-600 font-semibold' :
          rendlog.senal === 'VENTA' ? 'text-red-600 font-semibold' :
          'text-gray-400'
        }>
          {rendlog.senal || 'Sin señal'}
        </span>
      </p>
    </div>
  )
}

export default function RendLogChart({ data }) {
  const chartData = data.map((item) => ({
    ...item,
    time: formatTime(item.data_timestamp),
    log_return: item.rendlog?.log_return,
    banda_2sigma_sup: item.rendlog?.banda_2sigma_superior,
    banda_2sigma_inf: item.rendlog?.banda_2sigma_inferior,
  }))

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">RendLog - Log Returns</h2>
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            tickFormatter={(v) => v.toFixed(4)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="banda_2sigma_sup"
            stroke="#1f2937"
            strokeWidth={1}
            strokeDasharray="5 5"
            dot={false}
            name="Banda +2σ"
          />
          <Line
            type="monotone"
            dataKey="banda_2sigma_inf"
            stroke="#1f2937"
            strokeWidth={1}
            strokeDasharray="5 5"
            dot={false}
            name="Banda -2σ"
          />
          <Line
            type="monotone"
            dataKey="log_return"
            stroke="#111827"
            strokeWidth={2}
            dot={<CustomDot />}
            name="Log Return"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
