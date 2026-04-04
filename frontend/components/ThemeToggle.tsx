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
      className="flex items-center justify-center w-9 h-9 rounded-[10px] bg-transparent border border-[var(--border-strong)] text-[var(--text-muted)] cursor-pointer transition-all duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] hover:bg-[var(--accent-hover)] hover:text-[var(--text-main)] hover:scale-95"
      title={`Current theme: ${theme}`}
    >
      {theme === 'system' ? <Monitor size={18} /> : theme === 'dark' ? <Moon size={18} /> : <Sun size={18} />}
    </button>
  )
}
