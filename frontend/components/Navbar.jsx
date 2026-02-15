'use client'
import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabaseClient'
import { useRouter, usePathname } from 'next/navigation'

export default function Navbar() {
  const [user, setUser] = useState(null)
  const router = useRouter()
  const pathname = usePathname()

  const isAuthPage = pathname === '/login' || pathname === '/register'

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

  // Hide navbar on auth pages (video background handles branding)
  if (isAuthPage) return null

  return (
    <nav className="fixed top-0 w-full bg-black/90 backdrop-blur-md border-b border-white/5 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-14">
          <div className="flex items-center">
            <span className="text-xl font-bold text-accent">Rend</span>
            <span className="text-xl font-bold text-white">Log</span>
            <span className="ml-2 text-xs text-dark-textGray uppercase tracking-widest">Flow</span>
          </div>

          {user ? (
            <div className="flex items-center space-x-1">
              <a
                href="/dashboard"
                className={`px-3 py-1.5 rounded text-sm transition ${
                  pathname === '/dashboard'
                    ? 'text-accent bg-accent/10'
                    : 'text-dark-textGray hover:text-white'
                }`}
              >
                Dashboard
              </a>
              <a
                href="/settings"
                className={`px-3 py-1.5 rounded text-sm transition ${
                  pathname === '/settings'
                    ? 'text-accent bg-accent/10'
                    : 'text-dark-textGray hover:text-white'
                }`}
              >
                Settings
              </a>
              <div className="w-px h-5 bg-white/10 mx-2" />
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 text-sm text-dark-textGray hover:text-danger transition"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <a href="/login" className="px-3 py-1.5 text-sm text-dark-textGray hover:text-white transition">
                Login
              </a>
              <a
                href="/register"
                className="px-4 py-1.5 text-sm bg-accent text-black rounded hover:bg-accent-light transition font-medium"
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
