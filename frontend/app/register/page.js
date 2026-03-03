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
      <div className="min-h-screen flex relative overflow-hidden">
        {/* GIF Background */}
        <img
          src="/login-registervideo.gif"
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-black/60" />

        <div className="relative z-10 ml-auto w-full max-w-xl lg:max-w-2xl min-h-screen flex items-center justify-center px-6 lg:px-12 py-8">
          <div className="glass-panel rounded-2xl p-8 lg:p-10 w-full shadow-2xl">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full bg-accent/15 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-accent mb-2">Confirma tu Email</h1>
              <p className="text-dark-textGray text-sm">Hemos enviado un email de confirmacion a:</p>
              <p className="text-white font-semibold mt-1">{email}</p>
            </div>

            <div className="bg-black/30 p-6 rounded-xl mb-6">
              <h3 className="font-semibold text-sm uppercase tracking-wider text-accent mb-4">Proximos Pasos</h3>

              <div className="space-y-4 text-sm">
                <div className="flex items-start space-x-3">
                  <span className="flex-shrink-0 w-7 h-7 bg-accent text-black rounded-full flex items-center justify-center text-xs font-bold">1</span>
                  <div className="flex-1">
                    <p className="font-semibold text-white mb-0.5">Revisa tu bandeja de entrada</p>
                    <p className="text-dark-textGray text-xs">Busca un email de <code className="bg-black/40 px-1.5 py-0.5 rounded text-accent/80">noreply@mail.app.supabase.io</code></p>
                    <p className="text-dark-textGray text-xs mt-0.5">Revisa tambien spam/promociones</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <span className="flex-shrink-0 w-7 h-7 bg-accent text-black rounded-full flex items-center justify-center text-xs font-bold">2</span>
                  <div className="flex-1">
                    <p className="font-semibold text-white mb-0.5">Confirma tu email</p>
                    <p className="text-dark-textGray text-xs">Click en el boton &quot;Confirmar Email&quot; del correo</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <span className="flex-shrink-0 w-7 h-7 bg-accent text-black rounded-full flex items-center justify-center text-xs font-bold">3</span>
                  <div className="flex-1">
                    <p className="font-semibold text-white mb-0.5">Inicia sesion</p>
                    <p className="text-dark-textGray text-xs">Una vez confirmado, inicia sesion en la plataforma</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <span className="flex-shrink-0 w-7 h-7 bg-success text-white rounded-full flex items-center justify-center text-xs font-bold">4</span>
                  <div className="flex-1">
                    <p className="font-semibold text-white mb-0.5">Obten tu API Key</p>
                    <p className="text-dark-textGray text-xs">Ve a <strong className="text-white">Settings</strong> en el dashboard para ver tu API_KEY</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-warning/10 border border-warning/20 rounded-lg p-3 mb-6">
              <p className="text-warning text-xs">
                <strong>Importante:</strong> El email puede tardar hasta 2 minutos en llegar.
                Si no lo recibes, revisa tu carpeta de spam.
              </p>
            </div>

            <a
              href="/login"
              className="btn-primary block text-center"
            >
              Ir a Login
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* Video Background */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
      >
        <source src="/login-registervideo.mp4" type="video/mp4" />
      </video>
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

          <h1 className="text-2xl font-semibold text-white mb-1">Crear Cuenta</h1>
          <p className="text-dark-textGray text-sm mb-8">
            Registrate para obtener tu API Key
          </p>

          {error && (
            <div className="bg-danger/10 border border-danger/30 rounded-lg p-3 mb-6">
              <p className="text-danger text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-5">
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
                minLength={6}
                className="input-field"
                placeholder="Minimo 6 caracteres"
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
                  Creando cuenta...
                </span>
              ) : (
                'Crear Cuenta'
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-white/5">
            <p className="text-center text-sm text-dark-textGray">
              Ya tienes cuenta?{' '}
              <a href="/login" className="text-accent hover:text-accent-light transition">
                Inicia sesion
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
