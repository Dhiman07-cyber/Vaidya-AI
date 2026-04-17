import { useState, useEffect, useRef } from 'react'
import { useTheme } from './ThemeProvider'
import { Sun, Moon, Monitor, ChevronDown } from 'lucide-react'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
  const [isAnimating, setIsAnimating] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleToggleClick = () => {
    setIsAnimating(true)
    setTimeout(() => setIsAnimating(false), 150)
    setIsOpen(!isOpen)
  }

  const handleThemeSelect = (newTheme: 'light' | 'dark' | 'system') => {
    setIsAnimating(true)
    setTimeout(() => setIsAnimating(false), 150)
    setTheme(newTheme)
    setIsOpen(false)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={handleToggleClick}
        className={`group relative flex items-center gap-2 px-4 h-10 rounded-xl cursor-pointer transition-all duration-300 ease-out transform hover:scale-105 active:scale-95 ${
          isAnimating ? 'scale-95' : ''
        }`}
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        }}
        title={`Current theme: ${theme}`}
      >
        <div className="relative">
          {theme === 'system' ? (
            <Monitor size={18} className="text-[var(--text-main)] transition-all duration-300 group-hover:text-[var(--accent)]" />
          ) : theme === 'dark' ? (
            <Moon size={18} className="text-[var(--text-main)] transition-all duration-300 group-hover:text-[var(--accent)]" />
          ) : (
            <Sun size={18} className="text-[var(--text-main)] transition-all duration-300 group-hover:text-[var(--accent)]" />
          )}
        </div>
        <ChevronDown 
          size={14} 
          className={`text-[var(--text-muted)] transition-all duration-300 group-hover:text-[var(--text-main)] ${
            isOpen ? 'rotate-180 text-[var(--accent)]' : ''
          }`} 
        />
        
        {/* Subtle glow effect on hover */}
      </button>

      {isOpen && (
        <div 
          className="absolute top-full right-0 mt-3 z-50 min-w-[160px] origin-top-right"
          style={{
            animation: 'slideDown 0.2s ease-out',
          }}
        >
          <div 
            className="rounded-2xl overflow-hidden"
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            }}
          >
            <button
              onClick={() => handleThemeSelect('light')}
              className={`group flex items-center gap-3 w-full px-4 py-3 text-sm font-medium transition-all duration-200 cursor-pointer hover:transform hover:scale-[1.02] active:scale-[0.98] ${
                theme === 'light' 
                  ? 'text-[var(--text-main)]' 
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
              style={{
                background: theme === 'light' 
                  ? 'var(--accent)' 
                  : 'transparent',
                borderBottom: '1px solid var(--border-color)',
              }}
            >
              <Sun size={16} className="transition-transform duration-200 group-hover:scale-110" />
              <span>Light</span>
              {theme === 'light' && (
                <div className="ml-auto w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
              )}
            </button>
            
            <button
              onClick={() => handleThemeSelect('dark')}
              className={`group flex items-center gap-3 w-full px-4 py-3 text-sm font-medium transition-all duration-200 cursor-pointer hover:transform hover:scale-[1.02] active:scale-[0.98] ${
                theme === 'dark' 
                  ? 'text-[var(--text-main)]' 
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
              style={{
                background: theme === 'dark' 
                  ? 'var(--accent)' 
                  : 'transparent',
                borderBottom: '1px solid var(--border-color)',
              }}
            >
              <Moon size={16} className="transition-transform duration-200 group-hover:scale-110" />
              <span>Dark</span>
              {theme === 'dark' && (
                <div className="ml-auto w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
              )}
            </button>
            
            <button
              onClick={() => handleThemeSelect('system')}
              className={`group flex items-center gap-3 w-full px-4 py-3 text-sm font-medium transition-all duration-200 cursor-pointer hover:transform hover:scale-[1.02] active:scale-[0.98] rounded-b-2xl ${
                theme === 'system' 
                  ? 'text-[var(--text-main)]' 
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
              style={{
                background: theme === 'system' 
                  ? 'var(--accent)' 
                  : 'transparent',
              }}
            >
              <Monitor size={16} className="transition-transform duration-200 group-hover:scale-110" />
              <span>System</span>
              {theme === 'system' && (
                <div className="ml-auto w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
              )}
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: scale(0.95) translateY(-10px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
      `}</style>
    </div>
  )
}
