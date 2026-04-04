import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { AuthUser } from '@/lib/supabase'
import {
  ChevronLeft, Menu, ChevronDown,
  LayoutDashboard, BookOpen, Stethoscope,
  Library, MessageSquare, Layers,
  ClipboardCheck, Star, Microscope,
  Map, Activity, FileText,
  PenTool, Image as ImageIcon, CalendarDays,
  User
} from 'lucide-react'

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

// Hub-based navigation structure
const navHubs = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    icon: LayoutDashboard,
    path: '/dashboard',
    children: null, // Direct link, no children
  },
  {
    id: 'study',
    name: 'Study Hub',
    icon: BookOpen,
    path: null, // Parent group
    children: [
      { name: 'AI Chat', path: '/chat', icon: MessageSquare },
      { name: 'Flashcards', path: '/flashcards', icon: Layers },
      { name: 'MCQs', path: '/mcqs', icon: ClipboardCheck },
      { name: 'High Yield', path: '/highyield', icon: Star },
      { name: 'Explain', path: '/explain', icon: PenTool },
      { name: 'Image Analysis', path: '/image-analysis', icon: ImageIcon },
    ],
  },
  {
    id: 'clinical',
    name: 'Clinical',
    icon: Stethoscope,
    path: null,
    children: [
      { name: 'Clinical Cases', path: '/clinical-cases', icon: Activity },
      { name: 'OSCE Simulator', path: '/osce', icon: ClipboardCheck },
      { name: 'Concept Map', path: '/conceptmap', icon: Map },
    ],
  },
  {
    id: 'knowledge',
    name: 'Knowledge',
    icon: Library,
    path: null,
    children: [
      { name: 'Documents', path: '/documents', icon: FileText },
      { name: 'Study Planner', path: '/study-planner', icon: CalendarDays },
    ],
  },
]

export default function Sidebar({ user, currentPath, collapsed: controlledCollapsed, onToggle, plan }: SidebarProps) {
  const router = useRouter()
  const [isCollapsed, setIsCollapsed] = useState(globalCollapsed)
  const [expandedHubs, setExpandedHubs] = useState<Record<string, boolean>>({})

  // Sync with controlled prop if provided
  useEffect(() => {
    if (controlledCollapsed !== undefined) {
      setIsCollapsed(controlledCollapsed)
    }
  }, [controlledCollapsed])

  // Auto-expand the hub that contains the current path
  useEffect(() => {
    navHubs.forEach(hub => {
      if (hub.children) {
        const isActive = hub.children.some(child => currentPath === child.path)
        if (isActive) {
          setExpandedHubs(prev => ({ ...prev, [hub.id]: true }))
        }
      }
    })
  }, [currentPath])

  const handleToggle = () => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    globalCollapsed = newState
    onToggle?.(newState)
  }

  const toggleHub = (hubId: string) => {
    if (isCollapsed) return // Don't toggle in collapsed mode
    setExpandedHubs(prev => ({ ...prev, [hubId]: !prev[hubId] }))
  }

  const isActive = (path: string) => currentPath === path
  const isHubActive = (hub: typeof navHubs[0]) => {
    if (hub.path) return currentPath === hub.path
    return hub.children?.some(child => currentPath === child.path) || false
  }

  const sidebarWidth = isCollapsed ? '70px' : '260px'
  const userInitial = user ? (user.user_metadata?.name || user.email)?.[0].toUpperCase() : 'U'

  return (
    <div
      className="fixed left-0 top-0 h-dvh flex flex-col z-[100] border-r transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]"
      style={{
        width: sidebarWidth,
        backgroundColor: 'var(--bg-sidebar)',
        borderColor: 'var(--border-subtle)',
        color: 'var(--text-main)',
        boxShadow: '4px 0 24px rgba(0,0,0,0.02)',
      }}
      data-lenis-prevent
    >
      {/* Logo & Toggle */}
      <div
        className={`flex items-center min-h-[70px] border-b ${isCollapsed ? 'justify-center py-5' : 'justify-between px-5 py-4'}`}
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <Link href="/dashboard" className="no-underline block cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 text-white flex items-center justify-center flex-shrink-0 shadow-[0_4px_12px_rgba(99,102,241,0.3)]">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            {!isCollapsed && <span className="text-lg font-extrabold tracking-tight" style={{ color: 'var(--text-main)' }}>Vaidya AI</span>}
          </div>
        </Link>

        {!isCollapsed && (
          <button
            onClick={handleToggle}
            className="w-6 h-6 rounded-lg flex items-center justify-center cursor-pointer border transition-all hover:scale-105"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-strong)',
              color: 'var(--text-muted)',
            }}
            title="Collapse sidebar"
          >
            <ChevronLeft size={18} />
          </button>
        )}
      </div>

      {isCollapsed && (
        <button
          onClick={handleToggle}
          className="mx-auto my-2.5 p-2 rounded-lg cursor-pointer border transition-all hover:scale-105"
          style={{
            backgroundColor: 'var(--bg-card)',
            borderColor: 'var(--border-strong)',
            color: 'var(--text-muted)',
          }}
          title="Expand sidebar"
        >
          <Menu size={18} />
        </button>
      )}

      {/* Navigation Hubs */}
      <nav className="flex-1 py-4 px-3 overflow-y-auto flex flex-col gap-1" style={{ scrollbarWidth: 'none' }}>
        {navHubs.map(hub => {
          const HubIcon = hub.icon
          const hubIsActive = isHubActive(hub)
          const isExpanded = expandedHubs[hub.id] || false

          // Direct link (Dashboard)
          if (hub.path) {
            return (
              <Link key={hub.id} href={hub.path} className="no-underline block w-full">
                <div
                  className={`flex items-center gap-3 rounded-xl border transition-all duration-200 cursor-pointer font-bold text-sm w-full ${
                    isCollapsed ? 'justify-center py-3' : 'px-3.5 py-2.5'
                  } ${hubIsActive
                    ? 'shadow-[0_4px_12px_var(--medical-blue-soft)]'
                    : 'shadow-[0_2px_4px_rgba(0,0,0,0.02)] hover:scale-[0.98]'
                  }`}
                  style={{
                    backgroundColor: hubIsActive ? 'var(--accent-hover)' : 'var(--bg-card)',
                    borderColor: hubIsActive ? 'var(--medical-blue-soft)' : 'var(--border-subtle)',
                    color: hubIsActive ? 'var(--medical-blue)' : 'var(--text-main)',
                  }}
                  title={isCollapsed ? hub.name : undefined}
                >
                  <HubIcon size={18} className="flex-shrink-0" />
                  {!isCollapsed && <span className="whitespace-nowrap">{hub.name}</span>}
                </div>
              </Link>
            )
          }

          // Hub with children (expandable group)
          return (
            <div key={hub.id} className="w-full">
              <button
                onClick={() => {
                  if (isCollapsed) {
                    // In collapsed mode, navigate to the first child
                    if (hub.children?.[0]) {
                      router.push(hub.children[0].path)
                    }
                  } else {
                    toggleHub(hub.id)
                  }
                }}
                className={`flex items-center gap-3 w-full rounded-xl border transition-all duration-200 cursor-pointer font-bold text-sm ${
                  isCollapsed ? 'justify-center py-3' : 'px-3.5 py-2.5'
                } ${hubIsActive && !isExpanded
                  ? 'shadow-[0_4px_12px_var(--medical-blue-soft)]'
                  : 'shadow-[0_2px_4px_rgba(0,0,0,0.02)] hover:scale-[0.98]'
                }`}
                style={{
                  backgroundColor: hubIsActive ? 'var(--accent-hover)' : 'var(--bg-card)',
                  borderColor: hubIsActive ? 'var(--medical-blue-soft)' : 'var(--border-subtle)',
                  color: hubIsActive ? 'var(--medical-blue)' : 'var(--text-main)',
                }}
                title={isCollapsed ? hub.name : undefined}
              >
                <HubIcon size={18} className="flex-shrink-0" />
                {!isCollapsed && (
                  <>
                    <span className="whitespace-nowrap flex-1 text-left">{hub.name}</span>
                    <ChevronDown
                      size={14}
                      className={`transition-transform duration-200 flex-shrink-0 ${isExpanded ? 'rotate-180' : ''}`}
                      style={{ color: 'var(--text-muted)' }}
                    />
                  </>
                )}
              </button>

              {/* Children (sub-nav items) */}
              {!isCollapsed && isExpanded && hub.children && (
                <div className="ml-3 mt-1 pl-3 flex flex-col gap-0.5 border-l-2" style={{ borderColor: 'var(--border-subtle)' }}>
                  {hub.children.map(child => {
                    const ChildIcon = child.icon
                    const childActive = isActive(child.path)
                    return (
                      <Link key={child.path} href={child.path} className="no-underline block w-full">
                        <div
                          className={`flex items-center gap-2.5 py-2 px-3 rounded-lg transition-all duration-200 cursor-pointer text-[13px] font-semibold ${
                            childActive ? '' : 'hover:translate-x-0.5'
                          }`}
                          style={{
                            backgroundColor: childActive ? 'var(--medical-blue-soft)' : 'transparent',
                            color: childActive ? 'var(--medical-blue)' : 'var(--text-muted)',
                          }}
                        >
                          <ChildIcon size={15} className="flex-shrink-0" />
                          <span className="whitespace-nowrap">{child.name}</span>
                        </div>
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </nav>

      {/* User Area */}
      <div className="p-4 border-t" style={{ borderColor: 'var(--border-subtle)', backgroundColor: 'var(--bg-sidebar)' }}>
        {isCollapsed ? (
          <div
            className="w-8 h-8 rounded-[10px] bg-gradient-to-br from-indigo-500 to-violet-500 text-white flex items-center justify-center font-extrabold mx-auto shadow-[0_4px_10px_rgba(99,102,241,0.3)]"
          >
            {userInitial}
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <Link href="/profile" className="no-underline block">
              <div className="flex items-center gap-3 group cursor-pointer">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white flex items-center justify-center font-extrabold flex-shrink-0 text-sm shadow-[0_4px_12px_rgba(99,102,241,0.3)]">
                  {userInitial}
                </div>
                <div className="flex flex-col min-w-0">
                  <p
                    className="text-sm font-extrabold m-0 leading-tight whitespace-nowrap overflow-hidden text-ellipsis max-w-[160px] group-hover:underline"
                    style={{ color: 'var(--text-main)' }}
                    title={user ? (user.user_metadata?.name || user.email) : ''}
                  >
                    {user ? (user.user_metadata?.name || user.email?.split('@')[0]) : 'Loading...'}
                  </p>
                  <p className="text-[11px] font-semibold mt-1 m-0" style={{ color: 'var(--text-muted)' }}>
                    {getPlanLabel(plan || 'free')}
                  </p>
                </div>
              </div>
            </Link>

            {plan?.toLowerCase() === 'free' && (
              <button
                onClick={() => router.push('/upgrade')}
                className="w-full py-3 bg-gradient-to-r from-indigo-500 to-violet-500 text-white border-none rounded-xl text-[13px] font-bold cursor-pointer transition-all hover:brightness-110 hover:-translate-y-0.5 shadow-[0_4px_12px_rgba(99,102,241,0.3)] hover:shadow-[0_6px_16px_rgba(99,102,241,0.4)] flex justify-center items-center"
              >
                Upgrade Plan
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export { globalCollapsed }
