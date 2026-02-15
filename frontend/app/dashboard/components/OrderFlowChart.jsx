'use client'
import { useMemo } from 'react'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

function formatTime(timestamp, includeDate = false) {
  const date = new Date(timestamp)
  if (includeDate) {
    const day = date.getDate()
    const month = date.getMonth() + 1
    const time = date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
    return `${day}/${month}, ${time}`
  }
  return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null

  const item = payload[0]?.payload
  if (!item) return null

  const of = item.orderflow
  return (
    <div className="bg-dark-card p-3 rounded-lg shadow-lg border border-dark-borderLight text-sm">
      <p className="font-semibold text-white mb-1">{formatTime(item.data_timestamp, true)}</p>
      <p className="text-dark-textGray">
        Delta: <span className={`font-mono font-semibold ${of.delta > 0 ? 'text-success' : 'text-danger'}`}>
          {of.delta > 0 ? '+' : ''}{of.delta}
        </span>
      </p>
      <p className="text-dark-textGray">Vol Relativo: <span className="font-mono text-white">{of.vol_relativo?.toFixed(2)}</span></p>
      <p className="text-dark-textGray">Z-Score Vol: <span className="font-mono text-white">{of.z_score_vol?.toFixed(4)}</span></p>
      {of.anomalia_vol && (
        <p className="text-warning font-semibold mt-1">Anomalia de volumen</p>
      )}
    </div>
  )
}

const MAX_VALID_DELTA = 1_000_000

export default function OrderFlowChart({ data }) {
  const chartData = useMemo(() => {
    return data
      .filter((item) => {
        if (!item.data_timestamp) return false
        const delta = item.orderflow?.delta
        if (delta != null && Math.abs(delta) > MAX_VALID_DELTA) return false
        return true
      })
      .sort((a, b) => new Date(a.data_timestamp) - new Date(b.data_timestamp))
      .map((item) => ({
        ...item,
        time: formatTime(item.data_timestamp, true),
        tick_volume: item.orderflow?.tick_volume ?? 0,
        vol_relativo: item.orderflow?.vol_relativo ?? 0,
      }))
  }, [data])

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border p-6">
      <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Order Flow - Volumen & Delta</h2>
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart
          data={chartData}
          margin={{ top: 5, right: 20, bottom: 5, left: 10 }}
        >
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12, fill: '#8a8a8a' }}
            tickLine={false}
            axisLine={{ stroke: '#1f1f1f' }}
          />
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 12, fill: '#8a8a8a' }}
            tickLine={false}
            axisLine={{ stroke: '#1f1f1f' }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 12, fill: '#8a8a8a' }}
            tickLine={false}
            axisLine={{ stroke: '#1f1f1f' }}
            tickFormatter={(v) => v.toFixed(1)}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ strokeDasharray: '3 3', stroke: '#2a2a2a' }}
            isAnimationActive={false}
          />
          <Bar
            yAxisId="left"
            dataKey="tick_volume"
            name="Tick Volume"
            isAnimationActive={false}
            radius={[2, 2, 0, 0]}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.orderflow?.delta > 0 ? '#10b981' : '#ef4444'}
                stroke={entry.orderflow?.anomalia_vol ? '#f59e0b' : 'none'}
                strokeWidth={entry.orderflow?.anomalia_vol ? 2 : 0}
              />
            ))}
          </Bar>
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="vol_relativo"
            stroke="#F59E0B"
            strokeWidth={2}
            dot={false}
            name="Vol Relativo"
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
