'use client'
import { useState } from 'react'
import { supabase } from '@/lib/supabaseClient'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const router = useRouter()

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) throw error

      const { data: profile } = await supabase
        .from('user_profiles')
        .select('id')
        .eq('id', data.user.id)
        .maybeSingle()

      if (!profile) {
        console.log('Profile no encontrado, creando profile...')
        console.log('JWT Token:', data.session.access_token)

        try {
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/create-profile`,
            {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${data.session.access_token}`,
                'Content-Type': 'application/json'
              }
            }
          )

          const result = await response.json()

          if (!response.ok) {
            console.error('Error creating profile:', result)
          } else {
            console.log('Profile created successfully:', result)
          }
        } catch (fnError) {
          console.error('Error calling create-profile function:', fnError)
        }
      } else {
        console.log('Profile ya existe, continuando...')
      }

      router.push('/settings')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* GIF Background */}
      <img
        src="/login-registervideo.gif"
        alt=""
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Dark overlay on video */}
      <div className="absolute inset-0 bg-black/60" />

      {/* Form Panel - right side */}
      <div className="relative z-10 ml-auto w-full max-w-md lg:max-w-lg min-h-screen flex items-center justify-center px-6 lg:px-12">
        <div className="glass-panel rounded-2xl p-8 lg:p-10 w-full shadow-2xl">
          {/* Logo */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold">
              <span className="text-accent">Rend</span>
              <span className="text-white">Log</span>
              <span className="text-dark-textGray text-lg ml-2 font-normal">Flow</span>
            </h2>
            <div className="w-12 h-0.5 bg-accent/40 mt-3" />
          </div>

          <h1 className="text-2xl font-semibold text-white mb-1">Iniciar Sesion</h1>
          <p className="text-dark-textGray text-sm mb-8">
            Accede a tu dashboard de trading algoritmico
          </p>

          {error && (
            <div className="bg-danger/10 border border-danger/30 rounded-lg p-3 mb-6">
              <p className="text-danger text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-medium text-dark-textGray uppercase tracking-wider mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input-field"
                placeholder="tu@email.com"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-dark-textGray uppercase tracking-wider mb-2">
                Contrasena
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="input-field"
                placeholder="Tu contrasena"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  Iniciando sesion...
                </span>
              ) : (
                'Iniciar Sesion'
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-white/5">
            <p className="text-center text-sm text-dark-textGray">
              No tienes cuenta?{' '}
              <a href="/register" className="text-accent hover:text-accent-light transition">
                Registrate aqui
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
