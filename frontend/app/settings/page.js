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
      <div className="min-h-screen flex items-center justify-center bg-dark-bg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-dark-textGray">Cargando configuracion...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark-bg">
      <div className="max-w-4xl mx-auto p-8">
        <h1 className="text-3xl font-bold text-dark-text mb-2">Configuracion</h1>
        <p className="text-dark-textGray mb-8">
          Administra tu API Key y preferencias
        </p>

        {/* API Key Section */}
        <div className="bg-dark-card p-6 rounded-lg border border-dark-border mb-8">
          <h3 className="text-xl font-semibold text-dark-text mb-4">Tu API Key</h3>

          {apiKey ? (
            <>
              <div className="bg-dark-bg p-6 rounded-lg mb-4">
                <p className="text-sm text-dark-textGray mb-3">
                  Usa esta API Key para conectar tu backend local:
                </p>
                <div className="flex items-center space-x-2">
                  <code className="flex-1 bg-dark-card px-4 py-3 rounded border border-primary text-primary font-mono text-sm break-all">
                    {apiKey}
                  </code>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(apiKey)
                      alert('API Key copiada al portapapeles')
                    }}
                    className="px-4 py-3 bg-primary text-white rounded hover:bg-primary-dark transition whitespace-nowrap"
                  >
                    Copiar
                  </button>
                </div>
              </div>

              {showInstructions && (
                <div className="bg-dark-bg p-6 rounded-lg">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-semibold text-lg text-primary">Configurar Backend</h4>
                    <button
                      onClick={() => setShowInstructions(false)}
                      className="text-dark-textGray hover:text-dark-text text-xl leading-none"
                    >
                      &times;
                    </button>
                  </div>

                  <div className="space-y-4 text-sm">
                    <div className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white font-bold">1</span>
                      <div className="flex-1">
                        <p className="font-semibold mb-1">Descargar Backend</p>
                        <a
                          href="https://github.com/loostrader-gif/RendLog_Flow"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          https://github.com/loostrader-gif/RendLog_Flow
                        </a>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white font-bold">2</span>
                      <div className="flex-1">
                        <p className="font-semibold mb-1">Configurar .env</p>
                        <p className="text-dark-textGray">En <code className="bg-dark-card px-2 py-1 rounded">backend/.env</code></p>
                        <p className="text-dark-textGray">Pega tu API_KEY en: <code className="bg-dark-card px-2 py-1 rounded">API_KEY=</code></p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-8 h-8 bg-success rounded-full flex items-center justify-center text-white font-bold text-xs">OK</span>
                      <div className="flex-1">
                        <p className="font-semibold mb-1">Ejecutar Backend</p>
                        <code className="block bg-dark-card px-3 py-2 rounded mt-1">python main.py</code>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-dark-textGray">No se encontro tu API Key. Contacta soporte.</p>
            </div>
          )}
        </div>

        {/* User Info */}
        <div className="bg-dark-card p-6 rounded-lg border border-dark-border">
          <h3 className="text-xl font-semibold text-dark-text mb-4">Informacion de Cuenta</h3>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-dark-textGray">Email</p>
              <p className="text-dark-text font-medium">{user?.email}</p>
            </div>
            <div>
              <p className="text-sm text-dark-textGray">ID de Usuario</p>
              <p className="text-dark-text font-mono text-xs">{user?.id}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
