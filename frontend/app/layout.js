import './globals.css'
import Navbar from '@/components/Navbar'

export const metadata = {
  title: 'RendLog Flow',
  description: 'Sistema de Trading Algoritmico basado en Rendimientos Logaritmicos',
}

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className="bg-dark-bg text-dark-text min-h-screen">
        <Navbar />
        <main className="pt-16">
          {children}
        </main>
      </body>
    </html>
  )
}
