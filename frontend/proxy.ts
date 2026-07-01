import { clerkMiddleware } from '@clerk/nextjs/server'

export const proxy = clerkMiddleware()

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jte?|tsx?|cjs|mjs|ttf|woff2?|png|jpg|jpeg|gif|webp|svg|ico)).*)',
    '/(api|trpc)(.*)',
  ],
}
