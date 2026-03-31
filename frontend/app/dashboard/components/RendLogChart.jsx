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
    const senalSuprimida = r.senal_suprimida ?? false
    const calibracionActiva = r.calibracion_activa ?? false

    const regimenColor =
      r.regimen === 'RANGO' ? 'text-success' :
      r.regimen === 'TENDENCIA' ? 'text-danger' :
      r.regimen === 'AMBIGUO' ? 'text-warning' :
      'text-dark-textGray'

    const volRatioColor = (r.vol_ratio ?? 0) > 1.3 ? 'text-warning' : 'text-white'

    const percentilColor =
      r.percentil_real == null ? 'text-dark-textGray' :
      r.percentil_real >= 97 ? 'text-success' :
      r.percentil_real >= 95 ? 'text-warning' :
      'text-dark-textGray'

    return (
      <div className="bg-dark-card p-4 rounded-lg shadow-lg border border-dark-borderLight text-sm min-w-[220px]">
        <p className="font-semibold text-white mb-2">{formatTime(item.data_timestamp, timezone, { includeDate: true })}</p>

        {/* RETORNO */}
        <p className="text-[10px] text-dark-textGray/50 uppercase tracking-widest mb-1">Retorno</p>
        <p className="text-dark-textGray">Log Return: <span className="font-mono text-white">{r.log_return?.toFixed(6)}</span></p>
        <p className="text-dark-textGray">Z-Score EWMA: <span className="font-mono text-white">{r.z_score?.toFixed(4)}</span></p>
        <p className="text-dark-textGray">Z-Score Ref: <span className="font-mono text-white">{r.z_score_static?.toFixed(4) ?? '--'}</span></p>

        <div className="border-t border-dark-border/40 my-2" />

        {/* ESTADÍSTICO */}
        <p className="text-[10px] text-dark-textGray/50 uppercase tracking-widest mb-1">Estadístico</p>
        <p className="text-dark-textGray">Percentil Real: <span className={`font-mono ${percentilColor}`}>{r.percentil_real != null ? `${r.percentil_real.toFixed(1)}%` : '--'}</span></p>
        {calibracionActiva && (
          <p className="text-dark-textGray">ν (dist-t): <span className="font-mono text-white">{r.nu_distribucion?.toFixed(1) ?? '--'}</span></p>
        )}
        <p className="text-dark-textGray">Vol Ratio: <span className={`font-mono ${volRatioColor}`}>{r.vol_ratio?.toFixed(2) ?? '--'}</span></p>

        <div className="border-t border-dark-border/40 my-2" />

        {/* RÉGIMEN */}
        <p className="text-[10px] text-dark-textGray/50 uppercase tracking-widest mb-1">Régimen</p>
        <p className="text-dark-textGray">Régimen: <span className={`font-semibold ${regimenColor}`}>{r.regimen ?? 'DESCONOCIDO'}</span></p>
        <p className="text-dark-textGray">ER: <span className="font-mono text-white">{r.er?.toFixed(2) ?? '--'}</span></p>

        <div className="border-t border-dark-border/40 my-2" />

        {/* SEÑAL */}
        <p className="text-[10px] text-dark-textGray/50 uppercase tracking-widest mb-1">Señal</p>
        {r.senal_suprimida_pca ? (
          <p className="text-warning/80 text-xs font-medium">Suprimida — movimiento sistémico USD (PCA)</p>
        ) : senalSuprimida ? (
          <p className="text-dark-textGray/60">Filtrada (régimen ER)</p>
        ) : (
          <p className="text-dark-textGray">
            Señal:{' '}
            <span className={
              r.senal === 'COMPRA' ? 'text-success font-semibold' :
              r.senal === 'VENTA' ? 'text-danger font-semibold' :
              'text-dark-textGray'
            }>
              {(!r.senal || r.senal === 'Sin senal') ? 'Sin señal' : r.senal}
            </span>
          </p>
        )}
        <p className="text-danger/80">+2σ: {r.banda_2sigma_superior?.toFixed(6)}</p>
        <p className="text-danger/80">-2σ: {r.banda_2sigma_inferior?.toFixed(6)}</p>

        {/* GBM MONTE CARLO — solo cuando hay anomalía */}
        {r.gbm_prob_reversion != null && (
          <>
            <div className="border-t border-dark-border/40 my-2" />
            <p className="text-[10px] text-dark-textGray/50 uppercase tracking-widest mb-1">Monte Carlo GBM</p>
            <p className="text-dark-textGray">
              P(reversión):{' '}
              <span className={`font-mono font-semibold ${
                r.gbm_prob_reversion > 0.65 ? 'text-success' :
                r.gbm_prob_reversion > 0.40 ? 'text-warning' :
                'text-danger'
              }`}>
                {(r.gbm_prob_reversion * 100).toFixed(1)}%
              </span>
            </p>
            <p className="text-dark-textGray">
              Horizonte: <span className="font-mono text-white">{r.gbm_horizonte_velas} velas</span>
            </p>
            <p className="text-dark-textGray/60 text-xs">
              p5: {r.gbm_percentil_5?.toFixed(5)} · p50: {r.gbm_percentil_50?.toFixed(5)} · p95: {r.gbm_percentil_95?.toFixed(5)}
            </p>
          </>
        )}

        {/* PCA SISTÉMICO — siempre cuando hay datos multi-par */}
        {r.pca_pc1_loading != null && (
          <>
            <div className="border-t border-dark-border/40 my-2" />
            <p className="text-[10px] text-dark-textGray/50 uppercase tracking-widest mb-1">PCA Sistémico</p>
            <p className="text-dark-textGray">
              PC1 Loading:{' '}
              <span className={`font-mono ${r.pca_es_sistemico ? 'text-warning font-semibold' : 'text-white'}`}>
                {r.pca_pc1_loading?.toFixed(3)}
              </span>
            </p>
            <p className="text-dark-textGray">
              PC1 Varianza:{' '}
              <span className="font-mono text-white">{((r.pca_pc1_varianza ?? 0) * 100).toFixed(1)}%</span>
            </p>
            {r.pca_es_sistemico && (
              <p className="text-warning text-xs font-semibold mt-1">⚡ Movimiento sistémico USD</p>
            )}
            {r.exposure_usd_alto && !r.pca_es_sistemico && (
              <p className="text-warning/70 text-xs mt-1">Alta correlación con EURUSD</p>
            )}
          </>
        )}
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
