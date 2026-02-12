'use client'
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

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null

  const item = payload[0]?.payload
  if (!item) return null

  const of = item.orderflow
  return (
    <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200 text-sm">
      <p className="font-semibold text-gray-800 mb-1">{formatTime(item.data_timestamp)}</p>
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

function CustomBar(props) {
  const { x, y, width, height, payload } = props
  if (!payload) return null

  const isAnomaly = payload.orderflow?.anomalia_vol
  const fill = payload.orderflow?.delta > 0 ? '#22c55e' : '#ef4444'

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={fill}
        rx={2}
      />
      {isAnomaly && (
        <rect
          x={x - 1}
          y={y - 1}
          width={width + 2}
          height={height + 2}
          fill="none"
          stroke="#f97316"
          strokeWidth={2.5}
          rx={3}
        />
      )}
    </g>
  )
}

export default function OrderFlowChart({ data }) {
  const chartData = data.map((item) => ({
    ...item,
    time: formatTime(item.data_timestamp),
    tick_volume: item.orderflow?.tick_volume,
    vol_relativo: item.orderflow?.vol_relativo,
  }))

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Order Flow - Volumen & Delta</h2>
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
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
          <Tooltip content={<CustomTooltip />} />
          <Bar
            yAxisId="left"
            dataKey="tick_volume"
            shape={<CustomBar />}
            name="Tick Volume"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="vol_relativo"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={false}
            name="Vol Relativo"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
