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

      // Verificar si el usuario ya tiene profile
      const { data: profile } = await supabase
        .from('user_profiles')
        .select('id')
        .eq('id', data.user.id)
        .maybeSingle()

      if (!profile) {
        // No tiene profile, llamar Edge Function para crearlo
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
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="bg-dark-card p-8 rounded-lg shadow-lg max-w-md w-full border border-dark-border">
        <h1 className="text-3xl font-bold text-center mb-2">Iniciar Sesion</h1>
        <p className="text-dark-textGray text-center mb-8">
          Accede a tu dashboard de RendLog Flow
        </p>

        {error && (
          <div className="bg-red-900/20 border border-danger rounded-lg p-4 mb-6">
            <p className="text-danger text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
              placeholder="tu@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Contrasena</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
              placeholder="Tu contrasena"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Iniciando sesion...' : 'Iniciar Sesion'}
          </button>
        </form>

        <p className="text-center text-sm text-dark-textGray mt-6">
          No tienes cuenta?{' '}
          <a href="/register" className="text-primary hover:underline">
            Registrate aqui
          </a>
        </p>
      </div>
    </div>
  )
}
