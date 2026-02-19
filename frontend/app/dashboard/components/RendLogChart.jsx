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
import { formatTime } from '@/lib/timezone'

function CustomDot({ cx, cy, payload }) {
  if (!payload || !payload.rendlog) return null
  const { log_return, banda_2sigma_superior, banda_2sigma_inferior } = payload.rendlog

  if (log_return > banda_2sigma_superior) {
    return <circle cx={cx} cy={cy} r={5} fill="#ef4444" stroke="#1f1f1f" strokeWidth={1} />
  }
  if (log_return < banda_2sigma_inferior) {
    return <circle cx={cx} cy={cy} r={5} fill="#10b981" stroke="#1f1f1f" strokeWidth={1} />
  }
  return null
}

export default function RendLogChart({ data, timezone }) {
  function CustomTooltip({ active, payload }) {
    if (!active || !payload || !payload.length) return null

    const item = payload[0]?.payload
    if (!item || !item.rendlog) return null

    const r = item.rendlog
    return (
      <div className="bg-dark-card p-4 rounded-lg shadow-lg border border-dark-borderLight text-sm">
        <p className="font-semibold text-white mb-2">{formatTime(item.data_timestamp, timezone, { includeDate: true })}</p>
        <p className="text-dark-textGray">Log Return: <span className="font-mono text-white">{r.log_return?.toFixed(6)}</span></p>
        <p className="text-dark-textGray">Z-Score: <span className="font-mono text-white">{r.z_score?.toFixed(4)}</span></p>
        <p className="text-dark-textGray mb-2">
          Senal:{' '}
          <span className={
            r.senal === 'COMPRA' ? 'text-success font-semibold' :
            r.senal === 'VENTA' ? 'text-danger font-semibold' :
            'text-dark-textGray'
          }>
            {r.senal || 'Sin senal'}
          </span>
        </p>
        <p className="text-danger/80">+2s: {r.banda_2sigma_superior?.toFixed(6)}</p>
        <p className="text-danger/80">-2s: {r.banda_2sigma_inferior?.toFixed(6)}</p>
      </div>
    )
  }

  const chartData = data.map((item) => ({
    ...item,
    time: formatTime(item.data_timestamp, timezone, { includeDate: true }),
    log_return: item.rendlog?.log_return,
    banda_2sigma_sup: item.rendlog?.banda_2sigma_superior,
    banda_2sigma_inf: item.rendlog?.banda_2sigma_inferior,
    banda_3sigma_sup: item.rendlog?.banda_3sigma_superior,
    banda_3sigma_inf: item.rendlog?.banda_3sigma_inferior,
  }))

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border p-6">
      <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">RendLog - Log Returns</h2>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis
            dataKey="time"
            tick={{ fontSize: 11, fill: '#8a8a8a' }}
            tickLine={false}
            axisLine={{ stroke: '#1f1f1f' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#8a8a8a' }}
            tickLine={false}
            axisLine={{ stroke: '#1f1f1f' }}
            tickFormatter={(v) => v.toFixed(4)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="banda_3sigma_sup"
            stroke="#F97316"
            strokeWidth={2}
            strokeDasharray="3 3"
            dot={false}
            name="Banda +3s"
          />
          <Line
            type="monotone"
            dataKey="banda_3sigma_inf"
            stroke="#F97316"
            strokeWidth={2}
            strokeDasharray="3 3"
            dot={false}
            name="Banda -3s"
          />
          <Line
            type="monotone"
            dataKey="banda_2sigma_sup"
            stroke="#EF4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Banda +2s"
          />
          <Line
            type="monotone"
            dataKey="banda_2sigma_inf"
            stroke="#EF4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Banda -2s"
          />
          <Line
            type="monotone"
            dataKey="log_return"
            stroke="#F59E0B"
            strokeWidth={2}
            dot={<CustomDot />}
            name="Log Return"
          />
          <Brush
            dataKey="time"
            height={30}
            stroke="#F59E0B"
            fill="#111111"
            startIndex={Math.max(0, chartData.length - 50)}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
