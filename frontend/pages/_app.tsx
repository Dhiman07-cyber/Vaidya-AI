import type { AppProps } from 'next/app'
import { useEffect } from 'react'
import { useRouter } from 'next/router'
import Lenis from 'lenis'
import '@/styles/globals.css'

if (typeof window !== 'undefined') {
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    let [resource, config] = args;
    // Map absolute API calls to relative paths so our robust custom local proxy catches them!
    if (typeof resource === 'string' && resource.includes('localhost:8000')) {
        resource = resource.replace('http://localhost:8000', '');
    }
    return originalFetch(resource, config);
  };
}

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter()
  
  useEffect(() => {
    // Disable Lenis on pages with custom scrolling
    const disableLenisPages = ['/highyield', '/image-analysis', '/osce']
    const shouldDisableLenis = disableLenisPages.includes(router.pathname)
    
    if (shouldDisableLenis) {
      // Don't initialize Lenis on these pages
      return
    }
    
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      wrapper: window,
      content: document.documentElement,
      lerp: 0.1,
      smoothWheel: true,
    })

    function raf(time: number) {
      lenis.raf(time)
      requestAnimationFrame(raf)
    }

    requestAnimationFrame(raf)

    return () => {
      lenis.destroy()
    }
  }, [router.pathname])

  return <Component {...pageProps} />
}
