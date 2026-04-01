'use client'

/**
 * CorrelacionPanel — Vista compacta del estado multi-par.
 *
 * Muestra una fila por símbolo con:
 *   - Z-Score (EWMA)
 *   - Señal (COMPRA / VENTA / —)
 *   - PC1 Loading (indicador de factor USD)
 *   - Barra de exposición USD
 *   - Estado sistémico
 *
 * Props:
 *   data:           array de { symbol, rendlog, data_timestamp }
 *   selectedSymbol: string — símbolo activo en el dashboard (para highlight)
 */
export default function CorrelacionPanel({ data, selectedSymbol }) {
  if (!data || data.length === 0) return null

  const pc1Varianza = data[0]?.rendlog?.pca_pc1_varianza ?? null
  const esSistemico = data.some((d) => d?.rendlog?.pca_es_sistemico)

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-white uppercase tracking-wider">
            Análisis Multi-Par
          </h2>
          {pc1Varianza != null && (
            <p className="text-dark-textGray text-xs mt-0.5">
              PC1 explica{' '}
              <span className={`font-mono font-semibold ${
                pc1Varianza > 0.60 ? 'text-warning' : 'text-white'
              }`}>
                {(pc1Varianza * 100).toFixed(1)}%
              </span>
              {' '}de la varianza
              {esSistemico && (
                <span className="ml-2 text-warning font-semibold">— movimiento sistémico USD</span>
              )}
            </p>
          )}
        </div>
        {esSistemico && (
          <div className="flex items-center gap-1.5 bg-warning/10 border border-warning/30 rounded-lg px-3 py-1.5">
            <span className="w-2 h-2 rounded-full bg-warning animate-pulse" />
            <span className="text-warning text-xs font-semibold">USD Sistémico</span>
          </div>
        )}
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-border">
              <th className="text-left text-[10px] text-dark-textGray/50 uppercase tracking-wider pb-2 pr-4">Par</th>
              <th className="text-right text-[10px] text-dark-textGray/50 uppercase tracking-wider pb-2 px-4">Z-Score</th>
              <th className="text-center text-[10px] text-dark-textGray/50 uppercase tracking-wider pb-2 px-4">Señal</th>
              <th className="text-right text-[10px] text-dark-textGray/50 uppercase tracking-wider pb-2 px-4">PC1 Loading</th>
              <th className="text-center text-[10px] text-dark-textGray/50 uppercase tracking-wider pb-2 px-4">Régimen</th>
              <th className="text-center text-[10px] text-dark-textGray/50 uppercase tracking-wider pb-2 pl-4">Exp. USD</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-border/30">
            {data.map((item) => {
              const r = item?.rendlog ?? {}
              const sym = item?.symbol
              const isActive = sym === selectedSymbol
              const zScore = r.z_score ?? 0
              const pc1 = r.pca_pc1_loading
              const sistémico = r.pca_es_sistemico
              const exposicion = r.exposure_usd_alto

              const zColor =
                Math.abs(zScore) > 2 ? (zScore < 0 ? 'text-success' : 'text-danger') :
                Math.abs(zScore) > 1.5 ? 'text-warning' :
                'text-dark-textGray'

              return (
                <tr
                  key={sym}
                  className={`transition ${isActive ? 'bg-accent/5' : 'hover:bg-dark-cardHover/50'}`}
                >
                  {/* Par */}
                  <td className="py-2.5 pr-4">
                    <span className={`font-mono font-semibold ${isActive ? 'text-accent' : 'text-white'}`}>
                      {sym}
                    </span>
                    {isActive && (
                      <span className="ml-2 text-[10px] text-accent/70 uppercase">activo</span>
                    )}
                  </td>

                  {/* Z-Score */}
                  <td className="py-2.5 px-4 text-right">
                    <span className={`font-mono ${zColor}`}>
                      {zScore >= 0 ? '+' : ''}{zScore.toFixed(3)}
                    </span>
                  </td>

                  {/* Señal */}
                  <td className="py-2.5 px-4 text-center">
                    {r.senal === 'COMPRA' ? (
                      <span className="text-success font-semibold text-xs">COMPRA</span>
                    ) : r.senal === 'VENTA' ? (
                      <span className="text-danger font-semibold text-xs">VENTA</span>
                    ) : r.senal_suprimida_pca ? (
                      <span className="text-warning/70 text-xs">Sup. PCA</span>
                    ) : r.senal_suprimida ? (
                      <span className="text-dark-textGray/50 text-xs">Sup. ER</span>
                    ) : (
                      <span className="text-dark-textGray/40 text-xs">—</span>
                    )}
                  </td>

                  {/* PC1 Loading */}
                  <td className="py-2.5 px-4 text-right">
                    {pc1 != null ? (
                      <div className="flex items-center justify-end gap-2">
                        {/* Barra visual del loading */}
                        <div className="w-16 h-1.5 bg-dark-border rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${sistémico ? 'bg-warning' : 'bg-accent/60'}`}
                            style={{ width: `${Math.min(Math.abs(pc1) * 100, 100)}%` }}
                          />
                        </div>
                        <span className={`font-mono text-xs ${sistémico ? 'text-warning' : 'text-dark-textGray'}`}>
                          {pc1.toFixed(3)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-dark-textGray/30 text-xs">—</span>
                    )}
                  </td>

                  {/* Régimen */}
                  <td className="py-2.5 px-4 text-center">
                    <span className={`text-xs font-medium ${
                      r.regimen === 'RANGO' ? 'text-success' :
                      r.regimen === 'TENDENCIA' ? 'text-danger' :
                      r.regimen === 'AMBIGUO' ? 'text-warning' :
                      'text-dark-textGray/40'
                    }`}>
                      {r.regimen ?? '—'}
                    </span>
                  </td>

                  {/* Exposición USD */}
                  <td className="py-2.5 pl-4 text-center">
                    {exposicion ? (
                      <span className="inline-flex items-center gap-1 text-warning/80 text-xs">
                        <span className="w-1.5 h-1.5 rounded-full bg-warning/80" />
                        Alta
                      </span>
                    ) : (
                      <span className="text-dark-textGray/30 text-xs">—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
