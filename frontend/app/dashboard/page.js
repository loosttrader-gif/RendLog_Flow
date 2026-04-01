'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import { supabase } from '@/lib/supabaseClient'
import { useRouter } from 'next/navigation'
import { TIMEZONE_OPTIONS, DEFAULT_TIMEZONE, LOCALSTORAGE_KEY } from '@/lib/timezone'
import RendLogChart from './components/RendLogChart'
import OrderFlowChart from './components/OrderFlowChart'
import StatsPanel from './components/StatsPanel'
import CorrelacionPanel from './components/CorrelacionPanel'

const TIMEFRAMES = ['1M', '5M', '15M', '30M', '1H', '4H']
const SYMBOLS    = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD']

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [data, setData] = useState([])
  const [multiPairLatest, setMultiPairLatest] = useState([])
  const [loading, setLoading] = useState(true)
  const [isConnected, setIsConnected] = useState(false)
  const [selectedTF, setSelectedTF] = useState('30M')
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD')
  const [selectedTZ, setSelectedTZ] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(LOCALSTORAGE_KEY)
      if (stored && stored.startsWith('Etc/')) {
        localStorage.removeItem(LOCALSTORAGE_KEY)
        return DEFAULT_TIMEZONE
      }
      return stored || DEFAULT_TIMEZONE
    }
    return DEFAULT_TIMEZONE
  })
  const userRef = useRef(null)

  const handleTimezoneChange = (e) => {
    const tz = e.target.value
    setSelectedTZ(tz)
    localStorage.setItem(LOCALSTORAGE_KEY, tz)
  }

  const fetchData = useCallback(async (userId, tf, symbol) => {
    const { data: rows, error } = await supabase
      .from('user_data')
      .select('*')
      .eq('user_id', userId)
      .eq('timeframe', tf)
      .eq('symbol', symbol)
      .order('data_timestamp', { ascending: false })
      .limit(100)

    if (error) {
      console.error('Error fetching data:', error?.message, '| code:', error?.code, '| details:', error?.details, '| hint:', error?.hint)
      return
    }

    setData((rows || []).reverse())
  }, [])

  // Fetch la última vela de todos los símbolos para el CorrelacionPanel
  const fetchMultiPair = useCallback(async (userId, tf) => {
    const results = await Promise.all(
      SYMBOLS.map((sym) =>
        supabase
          .from('user_data')
          .select('symbol, rendlog, data_timestamp')
          .eq('user_id', userId)
          .eq('timeframe', tf)
          .eq('symbol', sym)
          .order('data_timestamp', { ascending: false })
          .limit(1)
          .then(({ data }) => (data && data.length > 0 ? data[0] : null))
      )
    )
    setMultiPairLatest(results.filter(Boolean))
  }, [])

  useEffect(() => {
    let channel = null
    let pollInterval = null
    let debounceTimer = null
    let cancelled = false

    const refresh = () => {
      if (cancelled || !userRef.current) return
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        if (cancelled) return
        fetchData(userRef.current.id, selectedTF, selectedSymbol)
        fetchMultiPair(userRef.current.id, selectedTF)
      }, 400)
    }

    const init = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (cancelled) return

      if (!user) {
        router.push('/login')
        return
      }

      setUser(user)
      userRef.current = user
      await Promise.all([
        fetchData(user.id, selectedTF, selectedSymbol),
        fetchMultiPair(user.id, selectedTF),
      ])
      if (cancelled) return

      setLoading(false)

      channel = supabase
        .channel(`user_data_${selectedSymbol}_${selectedTF}`)
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'user_data',
            filter: `user_id=eq.${user.id}`,
          },
          refresh
        )
        .subscribe((status) => {
          if (!cancelled) setIsConnected(status === 'SUBSCRIBED')
        })

      pollInterval = setInterval(refresh, 30000)
    }

    init()

    return () => {
      cancelled = true
      clearTimeout(debounceTimer)
      if (channel) supabase.removeChannel(channel)
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [router, fetchData, fetchMultiPair, selectedTF, selectedSymbol])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-accent/20 border-t-accent mx-auto mb-4"></div>
          <p className="text-dark-textGray text-sm">Cargando dashboard...</p>
        </div>
      </div>
    )
  }

  const latestData = data.length > 0 ? data[data.length - 1] : null

  return (
    <div className="min-h-screen pt-14">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-dark-textGray text-sm mt-1">Datos de trading en tiempo real</p>
        </div>

        {/* Selectores: Símbolo + Timeframe + Timezone */}
        <div className="flex flex-col gap-3 mb-6">
          {/* Fila 1: Símbolos */}
          <div className="flex justify-between items-center">
            <div className="flex gap-1.5">
              {SYMBOLS.map((sym) => (
                <button
                  key={sym}
                  onClick={() => setSelectedSymbol(sym)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    selectedSymbol === sym
                      ? 'bg-accent text-black'
                      : 'bg-dark-card text-dark-textGray border border-dark-border hover:border-dark-borderLight hover:text-white'
                  }`}
                >
                  {sym}
                </button>
              ))}
            </div>
          </div>

          {/* Fila 2: Timeframes + Timezone */}
          <div className="flex justify-between items-center">
            <div className="flex gap-1.5">
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf}
                  onClick={() => setSelectedTF(tf)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    selectedTF === tf
                      ? 'bg-accent text-black'
                      : 'bg-dark-card text-dark-textGray border border-dark-border hover:border-dark-borderLight hover:text-white'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
            <select
              value={selectedTZ}
              onChange={handleTimezoneChange}
              className="bg-dark-card text-dark-textGray border border-dark-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
            >
              {TIMEZONE_OPTIONS.map((tz) => (
                <option key={tz.value} value={tz.value}>
                  {tz.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-5">
          <StatsPanel
            latestData={latestData}
            isConnected={isConnected}
            selectedTF={selectedTF}
            selectedSymbol={selectedSymbol}
            timezone={selectedTZ}
          />

          {/* Panel de correlación multi-par (siempre visible si hay datos) */}
          {multiPairLatest.length > 0 && (
            <CorrelacionPanel data={multiPairLatest} selectedSymbol={selectedSymbol} />
          )}

          {data.length === 0 ? (
            <div className="bg-dark-card rounded-xl border border-dark-border p-12 text-center">
              <p className="text-dark-textGray">No hay datos disponibles.</p>
              <p className="text-dark-textGray/60 mt-2 text-sm">
                Ejecuta tu backend Python para empezar a recibir datos.
              </p>
            </div>
          ) : (
            <>
              <RendLogChart data={data} timezone={selectedTZ} />
              <OrderFlowChart data={data} timezone={selectedTZ} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
