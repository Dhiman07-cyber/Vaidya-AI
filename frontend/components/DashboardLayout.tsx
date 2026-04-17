import { ReactNode, useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { AuthUser, supabase } from '@/lib/supabase'
import Sidebar from './Sidebar'
import ThemeToggle from './ThemeToggle'
import {
  Menu, X, LogOut, ChevronRight, Crown,
  LayoutDashboard, BookOpen, Stethoscope, Library,
  MessageSquare, Layers, ClipboardCheck, Star,
  PenTool, Image as ImageIcon, Activity, Map,
  FileText, CalendarDays, Microscope, ChevronDown
} from 'lucide-react'

interface DashboardLayoutProps {
  user: AuthUser | null
  children: ReactNode
}

// Get page title from path
const getPageTitle = (pathname: string): string => {
  const titles: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/chat': 'Chat',
    '/flashcards': 'Flashcards',
    '/mcqs': 'MCQs',
    '/highyield': 'High Yield',
    '/explain': 'Explain',
    '/conceptmap': 'Concept Map',
    '/clinical-cases': 'Clinical Reasoning Engine',
    '/osce-simulator': 'OSCE Simulator',
    '/clinical-reasoning': 'Clinical Reasoning',
    '/osce': 'OSCE Station',
    '/study-planner': 'Study Planner',
    '/documents': 'Documents',
    '/profile': 'Profile',
    '/image-analysis': 'Image Analysis',
  }
  return titles[pathname] || pathname.slice(1).charAt(0).toUpperCase() + pathname.slice(2)
}

// Store sidebar and plan state globally to prevent flicker on navigation
let globalSidebarCollapsed = false
let sessionPlanCache: string | null = null

// Mobile Menu Hub Structure (matching Sidebar)
const mobileHubs = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    icon: LayoutDashboard,
    path: '/dashboard',
    children: null,
  },
  {
    id: 'study',
    name: 'Study Hub',
    icon: BookOpen,
    path: null,
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

export default function DashboardLayout({ user, children }: DashboardLayoutProps) {
  const router = useRouter()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(globalSidebarCollapsed)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false)
  const [plan, setPlan] = useState<string | null>(sessionPlanCache)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false)
  const [expandedMobileHubs, setExpandedMobileHubs] = useState<Record<string, boolean>>({})

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    const fetchUserPlan = async () => {
      if (!user) return
      try {
        const { data, error } = await supabase
          .from('users')
          .select('plan')
          .eq('id', user.id)
          .single()

        if (error) {
          console.warn('Could not fetch user plan from Supabase:', error.message)
          return
        }

        if (data?.plan) {
          setPlan(data.plan)
          sessionPlanCache = data.plan
          localStorage.setItem('valdia_user_plan', data.plan)
        }
      } catch (error) {
        console.error('Network or technical error fetching user plan:', error)
      }
    }

    // Try to load from localStorage first if not in global cache
    if (!sessionPlanCache) {
      const savedPlan = localStorage.getItem('valdia_user_plan')
      if (savedPlan) {
        sessionPlanCache = savedPlan
        setPlan(savedPlan)
      }
    }

    if (user?.id && !sessionPlanCache) {
      fetchUserPlan()
    }
  }, [user?.id])

  const handleSidebarToggle = (collapsed: boolean) => {
    setSidebarCollapsed(collapsed)
    globalSidebarCollapsed = collapsed
  }

  const handleSignOut = async () => {
    sessionPlanCache = null
    localStorage.removeItem('valdia_user_plan')
    await supabase.auth.signOut()
    router.push('/')
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('#user-profile-menu')) {
        setIsDropdownOpen(false)
      }
      if (!target.closest('#notifications-menu')) {
        setIsNotificationsOpen(false)
      }
    }

    if (isDropdownOpen || isNotificationsOpen) {
      document.addEventListener('click', handleClickOutside)
    }

    return () => {
      document.removeEventListener('click', handleClickOutside)
    }
  }, [isDropdownOpen, isNotificationsOpen])

  const sidebarWidth = isMobile ? '0px' : (sidebarCollapsed ? '70px' : '260px')

  const toggleMobileHub = (hubId: string) => {
    setExpandedMobileHubs(prev => ({ ...prev, [hubId]: !prev[hubId] }))
  }

  return (
    <div className="flex min-h-dvh" style={{ backgroundColor: 'var(--bg-main)', fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
      {!isMobile && (
        <Sidebar
          user={user}
          currentPath={router.pathname}
          collapsed={sidebarCollapsed}
          onToggle={handleSidebarToggle}
          plan={plan}
        />
      )}

      {/* Mobile Navigation Drawer */}
      {isMobile && isMobileMenuOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[1000] flex justify-end animate-[fadeIn_0.3s_ease]">
          <div
            className="w-full max-w-[320px] h-full flex flex-col animate-[slideLeft_0.3s_cubic-bezier(0.16,1,0.3,1)] shadow-[-10px_0_30px_rgba(0,0,0,0.1)] overflow-y-auto overscroll-contain"
            style={{ backgroundColor: 'var(--bg-sidebar)' }}
            data-lenis-prevent
          >
            {/* Drawer Header */}
            <div className="p-6 flex justify-between items-start border-b" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
              <div className="flex flex-col gap-4">
                <div className="flex justify-between items-center w-full">
                  <div className="w-[60px] h-[60px] bg-gradient-to-br from-indigo-500 to-violet-500 rounded-[20px] flex items-center justify-center text-2xl text-white font-extrabold shadow-[0_10px_20px_-5px_rgba(99,102,241,0.4)]">
                    {user ? user.email?.[0].toUpperCase() : '?'}
                  </div>
                  <ThemeToggle />
                </div>
                <div>
                  <h3 className="m-0 text-lg font-extrabold tracking-tight" style={{ color: 'var(--text-main)' }}>
                    {user ? (user.user_metadata?.name || user.email?.split('@')[0]) : 'Loading...'}
                  </h3>
                  <div className="text-[13px] font-medium mt-0.5" style={{ color: 'var(--text-muted)' }}>{user?.email || '...'}</div>
                  <div className="inline-block mt-2 px-2.5 py-1 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-md text-[11px] font-extrabold uppercase tracking-wide">
                    {(plan || 'free') === 'free' ? 'User' : 'Premium'}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer border"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-strong)', color: 'var(--text-muted)' }}
              >
                <X size={24} />
              </button>
            </div>

            {/* Navigation Links - Hub Structure */}
            <div className="flex-1 p-6 flex flex-col gap-2">
              {mobileHubs.map(hub => {
                const HubIcon = hub.icon
                const isExpanded = expandedMobileHubs[hub.id] || false
                const hubActive = hub.path ? router.pathname === hub.path : hub.children?.some(c => router.pathname === c.path)

                if (hub.path) {
                  return (
                    <Link
                      key={hub.id}
                      href={hub.path}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="flex items-center justify-between p-4 rounded-2xl no-underline border transition-all shadow-[0_2px_4px_rgba(0,0,0,0.02)] active:scale-[0.98]"
                      style={{
                        backgroundColor: hubActive ? 'var(--accent-hover)' : 'var(--bg-card)',
                        borderColor: hubActive ? 'var(--medical-blue-soft)' : 'var(--border-subtle)',
                        color: hubActive ? 'var(--medical-blue)' : 'var(--text-main)',
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <HubIcon size={18} />
                        <span className="font-bold text-[15px]">{hub.name}</span>
                      </div>
                      <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
                    </Link>
                  )
                }

                return (
                  <div key={hub.id}>
                    <button
                      onClick={() => toggleMobileHub(hub.id)}
                      className="flex items-center justify-between p-4 rounded-2xl w-full border transition-all shadow-[0_2px_4px_rgba(0,0,0,0.02)]"
                      style={{
                        backgroundColor: hubActive ? 'var(--accent-hover)' : 'var(--bg-card)',
                        borderColor: hubActive ? 'var(--medical-blue-soft)' : 'var(--border-subtle)',
                        color: hubActive ? 'var(--medical-blue)' : 'var(--text-main)',
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <HubIcon size={18} />
                        <span className="font-bold text-[15px]">{hub.name}</span>
                      </div>
                      <ChevronDown size={16} className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} style={{ color: 'var(--text-muted)' }} />
                    </button>

                    {isExpanded && hub.children && (
                      <div className="ml-4 mt-1 pl-3 flex flex-col gap-1 border-l-2" style={{ borderColor: 'var(--border-subtle)' }}>
                        {hub.children.map(child => {
                          const ChildIcon = child.icon
                          const childActive = router.pathname === child.path
                          return (
                            <Link
                              key={child.path}
                              href={child.path}
                              onClick={() => setIsMobileMenuOpen(false)}
                              className="flex items-center gap-2.5 py-2.5 px-3 rounded-lg no-underline transition-all"
                              style={{
                                backgroundColor: childActive ? 'var(--medical-blue-soft)' : 'transparent',
                                color: childActive ? 'var(--medical-blue)' : 'var(--text-muted)',
                              }}
                            >
                              <ChildIcon size={16} />
                              <span className="font-semibold text-[14px]">{child.name}</span>
                            </Link>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Drawer Footer Actions */}
            <div className="p-6 border-t flex flex-col gap-3" style={{ borderColor: 'var(--border-subtle)', backgroundColor: 'var(--bg-sidebar)' }}>
              <button
                className="w-full p-4 bg-gradient-to-r from-indigo-500 to-violet-500 text-white border-none rounded-2xl font-bold text-[15px] flex items-center justify-center gap-2 shadow-[0_8px_16px_-4px_rgba(99,102,241,0.4)] cursor-pointer"
                onClick={() => router.push('/upgrade')}
              >
                <Crown size={18} />
                Upgrade to Pro
              </button>

              <button
                className="w-full p-4 bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-400 border-none rounded-2xl font-bold text-[15px] flex items-center justify-center gap-2 cursor-pointer"
                onClick={() => { setIsMobileMenuOpen(false); setIsLogoutModalOpen(true); }}
              >
                <LogOut size={18} />
                Sign Out
              </button>

              <div className="mt-3 flex items-center gap-3 pt-3">
                <div className="w-8 h-8 bg-slate-800 rounded-full text-white flex items-center justify-center font-extrabold text-sm">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div className="flex flex-col text-[10px] leading-tight" style={{ color: 'var(--text-muted)' }}>
                  <strong>VAIDYA AI SERVICES</strong>
                  <span>VERSION 1.0.0 • PRE-ALFA</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div
        className="flex-1 min-w-0 flex flex-col transition-[margin-left] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]"
        style={{ marginLeft: sidebarWidth }}
      >
        {/* Top Bar */}
        <div
          className="h-16 flex items-center justify-between px-8 max-md:px-5 sticky top-0 z-50 border-b backdrop-blur-xl"
          style={{
            backgroundColor: 'var(--bg-card)',
            borderColor: 'var(--border-subtle)',
            boxShadow: '0 4px 12px rgba(0,0,0,0.02)',
          }}
        >
          <div>
            <h1
              className="text-lg font-extrabold tracking-tight m-0"
              style={{ color: 'var(--text-main)' }}
            >
              {getPageTitle(router.pathname)}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {!isMobile && <ThemeToggle />}
            {/* Desktop Profile Menu */}
            {!isMobile && (
              <>
                <div id="notifications-menu" className="relative">
                  <button
                    onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
                    className={`w-11 h-11 rounded-[14px] flex items-center justify-center cursor-pointer border transition-all shadow-[0_4px_12px_rgba(0,0,0,0.04)] ${isNotificationsOpen ? 'translate-y-[-1px] shadow-[0_6px_16px_rgba(0,0,0,0.06)]' : 'hover:translate-y-[-1px] hover:shadow-[0_6px_16px_rgba(0,0,0,0.06)]'}`}
                    style={{
                      backgroundColor: isNotificationsOpen ? 'var(--accent-hover)' : 'var(--bg-card)',
                      borderColor: isNotificationsOpen ? 'var(--border-subtle)' : 'var(--border-strong)',
                      color: isNotificationsOpen ? 'var(--text-main)' : 'var(--cream-text-muted)',
                    }}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                    </svg>
                  </button>

                  {isNotificationsOpen && (
                    <div
                      className="absolute top-[calc(100%+12px)] right-0 w-[340px] rounded-3xl shadow-[0_20px_40px_-8px_rgba(0,0,0,0.12),0_0_0_1px_rgba(0,0,0,0.04),0_10px_20px_-5px_rgba(0,0,0,0.05)] border overflow-hidden animate-[slideDown_0.3s_cubic-bezier(0.16,1,0.3,1)] z-[100]"
                      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
                    >
                      <div className="px-6 py-[18px] flex items-center justify-between border-b" style={{ backgroundColor: 'var(--cream-bg)', borderColor: 'rgba(0,0,0,0.06)' }}>
                        <h3 className="text-[15px] font-extrabold m-0 tracking-tight" style={{ color: 'var(--cream-text-main)' }}>Notifications</h3>
                        <button className="text-[11px] font-extrabold text-indigo-500 bg-indigo-500/[0.08] border-none cursor-pointer px-3 py-1.5 rounded-[10px] transition-all uppercase tracking-wide hover:bg-indigo-500 hover:text-white hover:-translate-y-px">
                          Clear all
                        </button>
                      </div>
                      <div className="max-h-[420px] overflow-y-auto">
                        <div className="py-14 px-8 flex flex-col items-center text-center gap-4" style={{ background: 'linear-gradient(180deg, var(--bg-card) 0%, var(--cream-bg) 100%)' }}>
                          <div className="w-[72px] h-[72px] bg-[var(--bg-card)] rounded-[22px] flex items-center justify-center shadow-[0_10px_25px_-5px_rgba(0,0,0,0.05),inset_0_0_0_1px_rgba(0,0,0,0.02)] mb-1" style={{ color: 'var(--text-muted)' }}>
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                            </svg>
                          </div>
                          <p className="text-base font-extrabold m-0 tracking-tight" style={{ color: 'var(--cream-text-main)' }}>Your medical feed is pristine.</p>
                          <span className="text-[13.5px] font-medium leading-relaxed max-w-[220px]" style={{ color: 'var(--cream-text-muted)' }}>No new alerts. Your dashboard is in peak health.</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div id="user-profile-menu" className="relative">
                  <div
                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    className={`flex items-center gap-3 py-1.5 pl-1.5 pr-3.5 rounded-2xl cursor-pointer border transition-all shadow-[0_4px_12px_rgba(0,0,0,0.04)] ${isDropdownOpen ? '-translate-y-px' : 'hover:-translate-y-px'}`}
                    style={{
                      backgroundColor: isDropdownOpen ? 'var(--accent-hover)' : 'var(--bg-card)',
                      borderColor: isDropdownOpen ? 'var(--medical-blue-soft)' : 'var(--border-strong)',
                    }}
                  >
                    <div className="w-9 h-9 bg-gradient-to-br from-amber-200 to-amber-300 rounded-xl flex items-center justify-center font-extrabold text-sm shadow-[0_2px_8px_rgba(232,217,192,0.4)]" style={{ color: 'var(--cream-text-main)' }}>
                      {user ? user.email?.[0].toUpperCase() : '?'}
                    </div>
                    <div className="hidden sm:flex flex-col items-center gap-0.5">
                      <p className="text-[13px] font-bold m-0 max-w-[130px] whitespace-nowrap overflow-hidden text-ellipsis leading-tight" style={{ color: 'var(--cream-text-main)' }}>
                        {user ? (user.user_metadata?.name || user.email?.split('@')[0]) : 'Loading...'}
                      </p>
                      <p className="text-[10px] font-extrabold text-violet-500 uppercase tracking-wide m-0 bg-violet-500/10 px-2 py-0.5 rounded-md leading-none inline-flex items-center justify-center">
                        {(plan || user?.user_metadata?.plan || 'free') === 'free' ? 'Standard' : (plan || user?.user_metadata?.plan || 'pro') === 'pro' ? 'Premium' : (plan || 'free').charAt(0).toUpperCase() + (plan || 'free').slice(1)}
                      </p>
                    </div>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`} style={{ color: 'var(--cream-text-muted)' }}>
                      <path d="m6 9 6 6 6-6" />
                    </svg>
                  </div>

                  {isDropdownOpen && (
                    <div
                      className="absolute top-[calc(100%+12px)] right-0 w-[280px] rounded-3xl shadow-[0_20px_40px_-8px_rgba(0,0,0,0.12),0_0_0_1px_rgba(0,0,0,0.04)] border overflow-hidden animate-[slideDown_0.3s_cubic-bezier(0.4,0,0.2,1)]"
                      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
                    >
                      <div className="p-6 flex items-center gap-3 border-b" style={{ backgroundColor: 'var(--cream-bg)', borderColor: 'rgba(0,0,0,0.06)' }}>
                        <div className="w-12 h-12 min-w-[48px] flex-shrink-0 bg-gradient-to-br from-amber-200 to-amber-300 rounded-[14px] flex items-center justify-center font-extrabold text-lg">
                          {user ? user.email?.[0].toUpperCase() : '?'}
                        </div>
                        <div>
                          <p className="text-[15px] font-extrabold m-0 max-w-[160px] whitespace-nowrap overflow-hidden text-ellipsis" style={{ color: 'var(--cream-text-main)' }}>
                            {user ? (user.user_metadata?.name || user.email?.split('@')[0]) : 'Loading...'}
                          </p>
                          <p className="text-xs font-semibold mt-0.5 m-0 max-w-[160px] whitespace-nowrap overflow-hidden text-ellipsis" style={{ color: 'var(--cream-text-muted)' }}>
                            {user?.email || '...'}
                          </p>
                        </div>
                      </div>

                      <div className="p-3">
                        <button
                          onClick={() => { setIsDropdownOpen(false); router.push('/profile'); }}
                          className="w-full flex items-center gap-3 py-3 px-4 border-none bg-transparent rounded-[14px] cursor-pointer transition-all text-sm font-bold hover:bg-[var(--cream-bg)]"
                          style={{ color: 'var(--cream-text-muted)' }}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                          Profile Settings
                        </button>
                        <button
                          onClick={() => { setIsDropdownOpen(false); setIsLogoutModalOpen(true); }}
                          className="w-full flex items-center gap-3 py-3 px-4 border-none bg-transparent rounded-[14px] cursor-pointer transition-all text-sm font-bold hover:bg-rose-50 hover:text-rose-600"
                          style={{ color: 'var(--cream-text-muted)' }}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                          Log out
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Mobile Menu Trigger */}
            {isMobile && (
              <button
                className="w-11 h-11 flex items-center justify-center bg-[var(--bg-card)] border rounded-xl cursor-pointer shadow-[0_4px_12px_rgba(0,0,0,0.05)]"
                style={{ borderColor: 'var(--border-subtle)' }}
                onClick={() => setIsMobileMenuOpen(true)}
              >
                <Menu size={24} style={{ color: 'var(--text-main)' }} />
              </button>
            )}
          </div>
        </div>

        {/* Main Content Area */}
        <main 
          className={`flex-1 overflow-y-auto ${['/chat', '/mcqs', '/flashcards', '/explain', '/osce', '/clinical-cases', '/highyield', '/image-analysis'].includes(router.pathname) ? 'p-0' : 'p-10 max-md:p-4'}`}
          style={{ backgroundColor: 'var(--bg-main)' }}
        >
          {children}
        </main>
      </div>

      <div id="vaidya-portal-root" />

      {/* Logout Modal */}
      {isLogoutModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xl flex items-center justify-center z-[5000] p-5 transition-all duration-400">
          <div
            className="w-full max-w-[420px] rounded-[32px] p-12 text-center border shadow-[0_48px_96px_-24px_rgba(0,0,0,0.25)]"
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'rgba(0,0,0,0.05)' }}
          >
            <div className="w-[72px] h-[72px] bg-rose-50 text-rose-500 rounded-3xl flex items-center justify-center mx-auto mb-7">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </div>
            <h2 className="text-[26px] font-extrabold mb-3.5 tracking-tight" style={{ color: 'var(--cream-text-main)' }}>Sign out?</h2>
            <p className="text-base leading-relaxed mb-9 font-medium" style={{ color: 'var(--cream-text-muted)' }}>
              Ready to wrap up your clinical session? We&apos;ll save your progress.
            </p>
            <div className="flex flex-col gap-3">
              <button
                onClick={handleSignOut}
                className="bg-gray-800 text-white border-none p-4 rounded-[18px] font-extrabold cursor-pointer transition-all hover:bg-gray-900 hover:-translate-y-px"
              >
                Log out
              </button>
              <button
                onClick={() => setIsLogoutModalOpen(false)}
                className="p-3.5 rounded-[18px] font-bold cursor-pointer transition-all border hover:bg-white"
                style={{ backgroundColor: 'var(--cream-bg)', borderColor: 'rgba(0,0,0,0.05)', color: 'var(--cream-text-main)' }}
              >
                Stay Logged In
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx global>{`
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideLeft { from { transform: translateX(100%); } to { transform: translateX(0); } }
      `}</style>
    </div>
  )
}
