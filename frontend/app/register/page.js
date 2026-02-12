'use client'
import { useState } from 'react'
import { supabase } from '@/lib/supabaseClient'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [registrationSuccess, setRegistrationSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      })

      if (signUpError) throw signUpError

      setRegistrationSuccess(true)

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (registrationSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-8">
        <div className="bg-dark-card p-8 rounded-lg shadow-lg max-w-2xl w-full border border-dark-border">
          <div className="text-center mb-6">
            <div className="text-6xl mb-4">📧</div>
            <h1 className="text-3xl font-bold text-primary mb-2">Confirma tu Email!</h1>
            <p className="text-dark-textGray">Hemos enviado un email de confirmacion a:</p>
            <p className="text-dark-text font-semibold mt-2">{email}</p>
          </div>

          <div className="bg-dark-bg p-6 rounded-lg mb-6">
            <h3 className="font-semibold text-lg mb-4 text-primary">Proximos Pasos:</h3>

            <div className="space-y-4 text-sm">
              <div className="flex items-start space-x-3">
                <span className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white font-bold">1</span>
                <div className="flex-1">
                  <p className="font-semibold mb-1">Revisa tu bandeja de entrada</p>
                  <p className="text-dark-textGray">Busca un email de <code className="bg-dark-card px-2 py-1 rounded">noreply@mail.app.supabase.io</code></p>
                  <p className="text-dark-textGray text-xs mt-1">Revisa tambien spam/promociones</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <span className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white font-bold">2</span>
                <div className="flex-1">
                  <p className="font-semibold mb-1">Confirma tu email</p>
                  <p className="text-dark-textGray">Click en el boton &quot;Confirmar Email&quot; del correo</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <span className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white font-bold">3</span>
                <div className="flex-1">
                  <p className="font-semibold mb-1">Inicia sesion</p>
                  <p className="text-dark-textGray">Una vez confirmado, inicia sesion en la plataforma</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <span className="flex-shrink-0 w-8 h-8 bg-success rounded-full flex items-center justify-center text-white font-bold text-xs">OK</span>
                <div className="flex-1">
                  <p className="font-semibold mb-1">Obten tu API Key</p>
                  <p className="text-dark-textGray">Ve a <strong>Settings</strong> en el dashboard para ver tu API_KEY</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4 mb-6">
            <p className="text-yellow-400 text-sm">
              <strong>Importante:</strong> El email puede tardar hasta 2 minutos en llegar.
              Si no lo recibes, revisa tu carpeta de spam.
            </p>
          </div>

          <a
            href="/login"
            className="block w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-semibold text-center"
          >
            Ir a Login
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="bg-dark-card p-8 rounded-lg shadow-lg max-w-md w-full border border-dark-border">
        <h1 className="text-3xl font-bold text-center mb-2">Crear Cuenta</h1>
        <p className="text-dark-textGray text-center mb-8">
          Registrate para obtener tu API Key
        </p>

        {error && (
          <div className="bg-red-900/20 border border-danger rounded-lg p-4 mb-6">
            <p className="text-danger text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-6">
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
              minLength={6}
              className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
              placeholder="Minimo 6 caracteres"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creando cuenta...' : 'Crear Cuenta'}
          </button>
        </form>

        <p className="text-center text-sm text-dark-textGray mt-6">
          Ya tienes cuenta?{' '}
          <a href="/login" className="text-primary hover:underline">
            Inicia sesion
          </a>
        </p>
      </div>
    </div>
  )
}
