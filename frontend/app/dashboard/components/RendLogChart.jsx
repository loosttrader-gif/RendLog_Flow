'use client'
import {
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Brush,
} from 'recharts'

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
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
  if (!item || !item.rendlog) return null

  const r = item.rendlog
  return (
    <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200 text-sm">
      <p className="font-semibold text-gray-800 mb-2">{formatTime(item.data_timestamp)}</p>
      <p className="text-gray-600">Log Return: <span className="font-mono">{r.log_return?.toFixed(6)}</span></p>
      <p className="text-gray-600">Z-Score: <span className="font-mono">{r.z_score?.toFixed(4)}</span></p>
      <p className="text-gray-600 mb-2">
        Señal:{' '}
        <span className={
          r.senal === 'COMPRA' ? 'text-green-600 font-semibold' :
          r.senal === 'VENTA' ? 'text-red-600 font-semibold' :
          'text-gray-400'
        }>
          {r.senal || 'Sin señal'}
        </span>
      </p>
      <p className="text-red-500">+2σ: {r.banda_2sigma_superior?.toFixed(6)}</p>
      <p className="text-red-500">-2σ: {r.banda_2sigma_inferior?.toFixed(6)}</p>
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
    banda_3sigma_sup: item.rendlog?.banda_3sigma_superior,
    banda_3sigma_inf: item.rendlog?.banda_3sigma_inferior,
  }))

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">RendLog - Log Returns</h2>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis
            dataKey="time"
            tick={{ fontSize: 11, fill: '#6b7280' }}
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
          {/* Banda superior 3σ */}
          <Line
            type="monotone"
            dataKey="banda_3sigma_sup"
            stroke="#F97316"
            strokeWidth={2}
            strokeDasharray="3 3"
            dot={false}
            name="Banda +3σ"
          />
          {/* Banda inferior 3σ */}
          <Line
            type="monotone"
            dataKey="banda_3sigma_inf"
            stroke="#F97316"
            strokeWidth={2}
            strokeDasharray="3 3"
            dot={false}
            name="Banda -3σ"
          />
          {/* Banda superior 2σ */}
          <Line
            type="monotone"
            dataKey="banda_2sigma_sup"
            stroke="#EF4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Banda +2σ"
          />
          {/* Banda inferior 2σ */}
          <Line
            type="monotone"
            dataKey="banda_2sigma_inf"
            stroke="#EF4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Banda -2σ"
          />
          {/* Log Return principal */}
          <Line
            type="monotone"
            dataKey="log_return"
            stroke="#111827"
            strokeWidth={2}
            dot={<CustomDot />}
            name="Log Return"
          />
          <Brush
            dataKey="time"
            height={30}
            stroke="#3B82F6"
            startIndex={Math.max(0, chartData.length - 50)}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
