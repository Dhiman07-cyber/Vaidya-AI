import { useRouter } from 'next/router'
import { supabase, AuthUser } from '@/lib/supabase'
import AdminSidebar from './AdminSidebar'

interface AdminLayoutProps {
  user: AuthUser
  children: React.ReactNode
}

/**
 * Admin Layout Component
 * Provides consistent layout for admin pages with sidebar navigation
 * Requirements: 2.7, 13.7
 */
export default function AdminLayout({ user, children }: AdminLayoutProps) {
  const router = useRouter()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/')
  }

  const handleBackToChat = () => {
    router.push('/chat')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        padding: '15px 20px',
        borderBottom: '1px solid #ddd',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#343a40',
        color: 'white'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <h1 style={{ margin: 0, fontSize: '20px' }}>Medical AI Platform - Admin</h1>
          <button
            onClick={handleBackToChat}
            style={{
              padding: '6px 12px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            ← Back to Chat
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span>{user.user_metadata?.name || user.email}</span>
          <span style={{
            padding: '4px 8px',
            backgroundColor: '#dc3545',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            ADMIN
          </span>
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content Area with Sidebar */}
      <div style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden'
      }}>
        <AdminSidebar />
        <main style={{
          flex: 1,
          overflow: 'auto',
          backgroundColor: '#f8f9fa'
        }}>
          {children}
        </main>
      </div>
    </div>
  )
}
