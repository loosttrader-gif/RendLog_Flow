import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export async function GET(request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    const cookieStore = cookies()
    const supabase = createRouteHandlerClient({ cookies: () => cookieStore })

    // Intercambiar codigo por sesion
    await supabase.auth.exchangeCodeForSession(code)

    // Obtener sesion actual
    const { data: { session } } = await supabase.auth.getSession()

    if (session) {
      try {
        // Llamar Edge Function para crear profile
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/create-profile`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json'
            }
          }
        )

        const result = await response.json()

        if (!response.ok) {
          console.error('Error creating profile:', result)
        } else {
          console.log('Profile created successfully')
        }
      } catch (error) {
        console.error('Error calling create-profile function:', error)
      }
    }
  }

  // Redirigir a settings
  return NextResponse.redirect(new URL('/settings', request.url))
}
