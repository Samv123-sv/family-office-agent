import type { Metadata } from 'next'
import { IBM_Plex_Sans, IBM_Plex_Mono, IBM_Plex_Serif } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import { ErrorToast } from '@/app/components/ErrorToast'
import './globals.css'

const ibmPlexSans = IBM_Plex_Sans({
  weight: ['400', '500', '600'],
  subsets: ['latin'],
  variable: '--font-ibm-plex-sans',
  display: 'swap',
})

const ibmPlexMono = IBM_Plex_Mono({
  weight: ['400', '500', '600'],
  subsets: ['latin'],
  variable: '--font-ibm-plex-mono',
  display: 'swap',
})

const ibmPlexSerif = IBM_Plex_Serif({
  weight: ['400', '500'],
  subsets: ['latin'],
  variable: '--font-ibm-plex-serif',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Deal Flow Intelligence',
  description: 'Family office deal sourcing and analysis platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html
        lang="en"
        className={`${ibmPlexSans.variable} ${ibmPlexMono.variable} ${ibmPlexSerif.variable} h-full`}
      >
        <body className="min-h-full bg-navy text-white font-sans antialiased">
          {children}
          <ErrorToast />
        </body>
      </html>
    </ClerkProvider>
  )
}
