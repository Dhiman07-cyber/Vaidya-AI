import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { AuthUser } from '@/lib/supabase'
import { ChevronLeft, Menu, Shield } from 'lucide-react'

interface SidebarProps {
  user: AuthUser | null
  currentPath: string
  collapsed?: boolean
  onToggle?: (collapsed: boolean) => void
  plan?: string | null
}

// Store collapsed state globally to persist across pages
let globalCollapsed = false

const getPlanLabel = (plan: string = 'free') => {
  const plans: Record<string, string> = {
    free: 'Standard Plan',
    student: 'Student Plan',
    pro: 'Premium Plan',
    premium: 'Premium Plan',
    admin: 'Admin'
  }
  return plans[plan.toLowerCase()] || 'Standard Plan'
}

const menuItems = [
  { name: 'Dashboard', path: '/dashboard', icon: '🏠' },
  { name: 'Chat', path: '/chat', icon: '💬' },
  { name: 'Flashcards', path: '/flashcards', icon: '🎴' },
  { name: 'MCQs', path: '/mcqs', icon: '✓' },
  { name: 'High Yield', path: '/highyield', icon: '⭐' },
  { name: 'Explain', path: '/explain', icon: '📚' },
  { name: 'Concept Map', path: '/conceptmap', icon: '🗺️' },
  { name: 'Clinical Cases', path: '/clinical-cases', icon: '🏥' },
  { name: 'OSCE Simulator', path: '/osce', icon: '👨‍⚕️' },
  { name: 'Image Analysis', path: '/image-analysis', icon: '🔬' },
  { name: 'Study Planner', path: '/study-planner', icon: '📅' },
  { name: 'Documents', path: '/documents', icon: '📄' },
  { name: 'Profile', path: '/profile', icon: '👤' },
]

export default function Sidebar({ user, currentPath, collapsed: controlledCollapsed, onToggle, plan }: SidebarProps) {
  const router = useRouter()
  const [isCollapsed, setIsCollapsed] = useState(globalCollapsed)

  // Sync with controlled prop if provided
  useEffect(() => {
    if (controlledCollapsed !== undefined) {
      setIsCollapsed(controlledCollapsed)
    }
  }, [controlledCollapsed])

  const handleToggle = () => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    globalCollapsed = newState
    onToggle?.(newState)
  }

  const isActive = (path: string) => currentPath === path
  const sidebarWidth = isCollapsed ? '70px' : '240px'
  const nameMaxWidth = '160px'

  const userInitial = user ? (user.user_metadata?.name || user.email)?.[0].toUpperCase() : 'U'

  return (
    <div className="sidebar-container" data-lenis-prevent>
      {/* Logo & Toggle */}
      <div className="sidebar-header">
        <Link href="/dashboard" className="logo-link">
          <div className="logo-section">
            <div className="logo-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            {!isCollapsed && <span className="logo-text">Vaidya AI</span>}
          </div>
        </Link>

        {!isCollapsed && (
          <button onClick={handleToggle} className="toggle-btn" title="Collapse sidebar">
            <ChevronLeft size={18} />
          </button>
        )}
      </div>

      {isCollapsed && (
        <button onClick={handleToggle} className="toggle-btn-collapsed" title="Expand sidebar">
          <Menu size={18} />
        </button>
      )}

      {/* Menu Items */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            href={item.path}
            passHref
            className="link-wrapper"
          >
            <div className={`nav-item ${isActive(item.path) ? 'active' : ''}`} title={isCollapsed ? item.name : undefined}>
              <span className="nav-icon">{item.icon}</span>
              {!isCollapsed && <span className="nav-label">{item.name}</span>}
            </div>
          </Link>
        ))}
      </nav>

      {/* User Area */}
      <div className="sidebar-footer">
        {isCollapsed ? (
          <div className="user-avatar-small">
            {userInitial}
          </div>
        ) : (
          <div className="user-full-card">
            <div className="user-info-row">
              <div className="user-avatar">
                {userInitial}
              </div>
              <div className="user-text">
                <p
                  className="user-name"
                  style={{ maxWidth: nameMaxWidth }}
                  title={user ? (user.user_metadata?.name || user.email) : ''}
                >
                  {user ? (user.user_metadata?.name || user.email?.split('@')[0]) : 'Loading...'}
                </p>
                <p className="user-subtext">{getPlanLabel(plan || 'free')}</p>
              </div>


            </div>

            {/* Token Meter Removed */}

            {/* Only show upgrade button for free users, and only when plan is confirmed */}
            {plan?.toLowerCase() === 'free' && (
              <button onClick={() => router.push('/upgrade')} className="upgrade-button">
                Upgrade Plan
              </button>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        .sidebar-container {
          width: ${sidebarWidth};
          height: 100vh;
          background-color: #fdfbf7;
          border-right: 1px solid rgba(0, 0, 0, 0.06);
          display: flex;
          flex-direction: column;
          position: fixed;
          left: 0;
          top: 0;
          transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          z-index: 100;
          color: #1e293b;
          box-shadow: 4px 0 24px rgba(0,0,0,0.02);
        }

        .sidebar-header {
          padding: ${isCollapsed ? '20px 0' : '16px 20px'};
          display: flex;
          align-items: center;
          justify-content: ${isCollapsed ? 'center' : 'space-between'};
          min-height: 70px;
          border-bottom: 1px solid rgba(0,0,0,0.04);
        }

        .logo-link {
          text-decoration: none;
          display: block;
          cursor: pointer;
        }

        .logo-section {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .logo-icon {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }

        .logo-text {
          font-size: 18px;
          font-weight: 800;
          color: #1e293b;
          letter-spacing: -0.03em;
        }

        .toggle-btn {
          background: white;
          border: 1px solid rgba(0, 0, 0, 0.1);
          border-radius: 8px;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: #64748b;
          transition: all 0.2s;
        }

        .toggle-btn:hover {
          background-color: #f8fafc;
          color: #1e293b;
        }

        .toggle-btn-collapsed {
          margin: 10px auto;
          background: white;
          border: 1px solid rgba(0, 0, 0, 0.1);
          border-radius: 8px;
          color: #64748b;
          cursor: pointer;
          padding: 8px;
          transition: all 0.2s;
        }

        .toggle-btn-collapsed:hover {
          background-color: #f8fafc;
          color: #1e293b;
        }

        .sidebar-nav {
          flex: 1;
          padding: 16px 12px;
          overflow-y: auto;
          scrollbar-width: none;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .sidebar-nav::-webkit-scrollbar {
          display: none;
        }

        /* Ensure link wrapper doesn't break flex layout */
        :global(.link-wrapper) {
          text-decoration: none;
          display: block;
          width: 100%;
        }

        .nav-item {
          display: flex !important;
          flex-direction: row !important;
          align-items: center !important; 
          gap: 12px;
          padding: ${isCollapsed ? '12px 0' : '12px 14px'};
          justify-content: ${isCollapsed ? 'center' : 'flex-start'};
          background: white;
          color: #1e293b;
          border-radius: 12px;
          border: 1px solid rgba(0,0,0,0.04);
          transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
          font-weight: 700;
          font-size: 14px;
          width: 100%;
          white-space: nowrap;
          box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }

        .nav-item:hover {
          transform: scale(0.98);
          background-color: #f8fafc;
        }

        .nav-item.active {
          background-color: #f8fafc;
          border-color: rgba(99, 102, 241, 0.3);
          color: #6366F1;
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
        }

        .nav-icon {
          font-size: 18px;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .nav-label {
           white-space: nowrap;
        }

        .sidebar-footer {
          padding: 16px;
          border-top: 1px solid rgba(0, 0, 0, 0.06);
          background: white;
        }

        .user-avatar-small {
          width: 32px;
          height: 32px;
          border-radius: 10px;
          background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          margin: 0 auto;
          box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
        }

        .user-full-card {
           display: flex;
           flex-direction: column;
           gap: 12px;
        }

        .user-info-row {
          display: flex !important;
          flex-direction: row !important;
          align-items: center !important;
          gap: 12px;
        }

        .user-avatar {
          width: 40px;
          height: 40px;
          border-radius: 12px;
          background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          flex-shrink: 0;
          font-size: 14px;
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }

        .user-text {
          display: flex;
          flex-direction: column;
          min-width: 0;
        }

        .user-name {
          font-size: 14px;
          font-weight: 800;
          color: #1e293b;
          margin: 0;
          line-height: 1.2;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .user-subtext {
          font-size: 11px;
          color: #64748b;
          margin: 4px 0 0 0;
          font-weight: 600;
        }

        .upgrade-button {
          width: 100%;
          padding: 12px;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 13px;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .upgrade-button:hover {
          filter: brightness(1.1);
          transform: translateY(-1px);
          box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
        }
      `}</style>
    </div>
  )
}

export { globalCollapsed }
