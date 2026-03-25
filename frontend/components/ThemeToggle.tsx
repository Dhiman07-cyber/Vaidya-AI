import { useTheme } from './ThemeProvider'
import { Sun, Moon, Monitor } from 'lucide-react'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const cycleTheme = () => {
    if (theme === 'light') setTheme('dark')
    else if (theme === 'dark') setTheme('system')
    else setTheme('light')
  }

  return (
    <button
      onClick={cycleTheme}
      className="theme-toggle-btn"
      title={`Current theme: ${theme}`}
    >
      {theme === 'system' ? <Monitor size={18} /> : theme === 'dark' ? <Moon size={18} /> : <Sun size={18} />}
      <style jsx>{`
        .theme-toggle-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          border-radius: 10px;
          background: transparent;
          border: 1px solid var(--border-strong);
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .theme-toggle-btn:hover {
          background: var(--accent-hover);
          color: var(--text-main);
          transform: scale(0.95);
        }
      `}</style>
    </button>
  )
}
