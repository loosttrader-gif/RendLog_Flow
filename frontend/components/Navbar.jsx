'use client'
import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabaseClient'
import { useRouter } from 'next/navigation'

export default function Navbar() {
  const [user, setUser] = useState(null)
  const router = useRouter()

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <nav className="fixed top-0 w-full bg-dark-card border-b border-dark-border z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <span className="text-2xl font-bold text-primary">RendLog</span>
            <span className="ml-2 text-sm text-dark-textGray">Flow</span>
          </div>

          {user ? (
            <div className="flex items-center space-x-4">
              <a href="/dashboard" className="text-dark-text hover:text-primary transition">
                Dashboard
              </a>
              <a href="/settings" className="text-dark-text hover:text-primary transition">
                Settings
              </a>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-danger text-white rounded hover:bg-red-600 transition"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-4">
              <a href="/login" className="text-dark-text hover:text-primary transition">
                Login
              </a>
              <a
                href="/register"
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark transition"
              >
                Registro
              </a>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
