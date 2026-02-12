'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import { supabase } from '@/lib/supabaseClient'
import { useRouter } from 'next/navigation'
import RendLogChart from './components/RendLogChart'
import OrderFlowChart from './components/OrderFlowChart'
import StatsPanel from './components/StatsPanel'

const TIMEFRAMES = ['1M', '5M', '15M', '30M', '1H', '4H']

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [isConnected, setIsConnected] = useState(false)
  const [selectedTF, setSelectedTF] = useState('30M')
  const userRef = useRef(null)

  const fetchData = useCallback(async (userId, tf) => {
    const { data: rows, error } = await supabase
      .from('user_data')
      .select('*')
      .eq('user_id', userId)
      .eq('timeframe', tf)
      .order('data_timestamp', { ascending: false })
      .limit(100)

    if (error) {
      console.error('Error fetching data:', error)
      return
    }

    // Reverse para que queden en orden cronológico (oldest → newest)
    setData((rows || []).reverse())
  }, [])

  useEffect(() => {
    let channel = null
    let pollInterval = null

    const init = async () => {
      const { data: { user } } = await supabase.auth.getUser()

      if (!user) {
        router.push('/login')
        return
      }

      setUser(user)
      userRef.current = user
      await fetchData(user.id, selectedTF)
      setLoading(false)

      // Realtime: escuchar INSERT y UPDATE
      channel = supabase
        .channel(`user_data_changes_${selectedTF}`)
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'user_data',
            filter: `user_id=eq.${user.id}`,
          },
          () => {
            // Re-fetch completo en cualquier cambio
            fetchData(user.id, selectedTF)
          }
        )
        .subscribe((status) => {
          setIsConnected(status === 'SUBSCRIBED')
        })

      // Polling cada 30s como respaldo
      pollInterval = setInterval(() => {
        fetchData(user.id, selectedTF)
      }, 30000)
    }

    init()

    return () => {
      if (channel) {
        supabase.removeChannel(channel)
      }
      if (pollInterval) {
        clearInterval(pollInterval)
      }
    }
  }, [router, fetchData, selectedTF])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Cargando dashboard...</p>
        </div>
      </div>
    )
  }

  const latestData = data.length > 0 ? data[data.length - 1] : null

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Datos de trading en tiempo real</p>
        </div>

        {/* Selector de Timeframe */}
        <div className="flex gap-2 mb-6">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => setSelectedTF(tf)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedTF === tf
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-6">
          <StatsPanel latestData={latestData} isConnected={isConnected} selectedTF={selectedTF} />

          {data.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <p className="text-gray-500 text-lg">No hay datos disponibles.</p>
              <p className="text-gray-400 mt-2">
                Ejecuta tu backend Python para empezar a recibir datos.
              </p>
            </div>
          ) : (
            <>
              <RendLogChart data={data} />
              <OrderFlowChart data={data} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
