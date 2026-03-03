'use client'
import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabaseClient'
import { useRouter } from 'next/navigation'

export default function SettingsPage() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [apiKey, setApiKey] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showInstructions, setShowInstructions] = useState(true)

  useEffect(() => {
    loadUserData()
  }, [])

  const loadUserData = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()

      if (!user) {
        router.push('/login')
        return
      }

      setUser(user)

      const { data: profileData, error } = await supabase
        .from('user_profiles')
        .select('api_key')
        .eq('id', user.id)
        .single()

      if (error) throw error

      setApiKey(profileData?.api_key)
    } catch (err) {
      console.error('Error loading user data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-accent/20 border-t-accent mx-auto mb-4"></div>
          <p className="text-dark-textGray text-sm">Cargando configuracion...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen pt-14">
      <div className="max-w-4xl mx-auto p-8">
        <h1 className="text-2xl font-bold text-white mb-1">Configuracion</h1>
        <p className="text-dark-textGray text-sm mb-8">
          Administra tu API Key y preferencias
        </p>

        {/* API Key Section */}
        <div className="bg-dark-card p-6 rounded-xl border border-dark-border mb-6">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Tu API Key</h3>

          {apiKey ? (
            <>
              <div className="bg-black/40 p-5 rounded-lg mb-4">
                <p className="text-xs text-dark-textGray mb-3">
                  Usa esta API Key para conectar tu backend local:
                </p>
                <div className="flex items-center space-x-2">
                  <code className="flex-1 bg-dark-bg px-4 py-3 rounded border border-accent/20 text-accent font-mono text-sm break-all">
                    {apiKey}
                  </code>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(apiKey)
                      alert('API Key copiada al portapapeles')
                    }}
                    className="px-4 py-3 bg-accent text-black rounded hover:bg-accent-light transition whitespace-nowrap font-medium text-sm"
                  >
                    Copiar
                  </button>
                </div>
              </div>

              {showInstructions && (
                <div className="bg-black/30 p-5 rounded-lg">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-accent">Configurar Backend</h4>
                    <button
                      onClick={() => setShowInstructions(false)}
                      className="text-dark-textGray hover:text-white text-lg leading-none"
                    >
                      &times;
                    </button>
                  </div>

                  <div className="space-y-4 text-sm">
                    <div className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-7 h-7 bg-accent text-black rounded-full flex items-center justify-center text-xs font-bold">1</span>
                      <div className="flex-1">
                        <p className="font-semibold text-white mb-0.5">Descargar Backend</p>
                        <a
                          href="https://github.com/loosttrader-gif/RendLog_Flow"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-accent hover:text-accent-light transition text-xs"
                        >
                          github.com/loosttrader-gif/RendLog_Flow
                        </a>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-7 h-7 bg-accent text-black rounded-full flex items-center justify-center text-xs font-bold">2</span>
                      <div className="flex-1">
                        <p className="font-semibold text-white mb-0.5">Configurar .env</p>
                        <p className="text-dark-textGray text-xs">En <code className="bg-black/40 px-1.5 py-0.5 rounded">backend/.env</code></p>
                        <p className="text-dark-textGray text-xs">Pega tu API_KEY en: <code className="bg-black/40 px-1.5 py-0.5 rounded">API_KEY=</code></p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-7 h-7 bg-success text-white rounded-full flex items-center justify-center text-xs font-bold">3</span>
                      <div className="flex-1">
                        <p className="font-semibold text-white mb-0.5">Ejecutar Backend</p>
                        <code className="block bg-black/40 px-3 py-2 rounded mt-1 text-accent/80 text-xs">python main.py</code>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-dark-textGray text-sm">No se encontro tu API Key. Contacta soporte.</p>
            </div>
          )}
        </div>

        {/* User Info */}
        <div className="bg-dark-card p-6 rounded-xl border border-dark-border">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Informacion de Cuenta</h3>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-dark-textGray uppercase tracking-wider">Email</p>
              <p className="text-white font-medium">{user?.email}</p>
            </div>
            <div>
              <p className="text-xs text-dark-textGray uppercase tracking-wider">ID de Usuario</p>
              <p className="text-dark-textGray font-mono text-xs">{user?.id}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
