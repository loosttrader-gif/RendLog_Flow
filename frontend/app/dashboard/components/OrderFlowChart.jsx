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
    <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200 text-sm">
      <p className="font-semibold text-gray-800 mb-1">{formatTime(item.data_timestamp, true)}</p>
      <p className="text-gray-600">
        Delta: <span className={`font-mono font-semibold ${of.delta > 0 ? 'text-green-600' : 'text-red-600'}`}>
          {of.delta > 0 ? '+' : ''}{of.delta}
        </span>
      </p>
      <p className="text-gray-600">Vol Relativo: <span className="font-mono">{of.vol_relativo?.toFixed(2)}</span></p>
      <p className="text-gray-600">Z-Score Vol: <span className="font-mono">{of.z_score_vol?.toFixed(4)}</span></p>
      {of.anomalia_vol && (
        <p className="text-orange-500 font-semibold mt-1">Anomalia de volumen</p>
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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Order Flow - Volumen & Delta</h2>
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart
          data={chartData}
          margin={{ top: 5, right: 20, bottom: 5, left: 10 }}
        >
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            tickFormatter={(v) => v.toFixed(1)}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ strokeDasharray: '3 3' }}
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
                fill={entry.orderflow?.delta > 0 ? '#22c55e' : '#ef4444'}
                stroke={entry.orderflow?.anomalia_vol ? '#f97316' : 'none'}
                strokeWidth={entry.orderflow?.anomalia_vol ? 2 : 0}
              />
            ))}
          </Bar>
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="vol_relativo"
            stroke="#8b5cf6"
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
