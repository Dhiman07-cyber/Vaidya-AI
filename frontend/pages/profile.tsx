import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { createClient } from '@supabase/supabase-js'
import UserApiKeyForm from '../components/UserApiKeyForm'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
const supabase = createClient(supabaseUrl, supabaseAnonKey)

/**
 * Profile Page
 * User profile management including personal API key
 * Requirements: 27.1, 27.5
 */
export default function ProfilePage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [currentKey, setCurrentKey] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkUser()
  }, [])

  const checkUser = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) {
        router.push('/')
        return
      }

      setUser(user)
      
      // Check if user has a personal API key
      await fetchUserKey(user.id)
    } catch (err) {
      console.error('Error checking user:', err)
      setError('Failed to load user data')
    } finally {
      setLoading(false)
    }
  }

  const fetchUserKey = async (userId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/user/api-key`, {
        headers: {
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setCurrentKey(data.has_key ? 'exists' : null)
      }
    } catch (err) {
      console.error('Error fetching user key:', err)
    }
  }

  const handleSubmitKey = async (key: string) => {
    try {
      const session = await supabase.auth.getSession()
      const token = session.data.session?.access_token

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/user/api-key`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ key })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save API key')
      }

      setCurrentKey('exists')
    } catch (err) {
      throw err
    }
  }

  const handleRemoveKey = async () => {
    try {
      const session = await supabase.auth.getSession()
      const token = session.data.session?.access_token

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/user/api-key`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to remove API key')
      }

      setCurrentKey(null)
    } catch (err) {
      throw err
    }
  }

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push('/')
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        backgroundColor: '#f8f9fa'
      }}>
        <div>Loading...</div>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f8f9fa'
    }}>
      {/* Header */}
      <header style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #dee2e6',
        padding: '16px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ margin: 0, fontSize: '24px' }}>Profile</h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => router.push('/chat')}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Back to Chat
          </button>
          <button
            onClick={handleSignOut}
            style={{
              padding: '8px 16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main style={{
        maxWidth: '800px',
        margin: '0 auto',
        padding: '32px 24px'
      }}>
        {error && (
          <div style={{
            padding: '12px',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            borderRadius: '4px',
            marginBottom: '24px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        {/* User Info */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          marginBottom: '24px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ marginTop: 0, marginBottom: '16px' }}>Account Information</h2>
          <div style={{ fontSize: '14px', color: '#495057' }}>
            <p><strong>Email:</strong> {user?.email}</p>
            <p style={{ marginBottom: 0 }}><strong>User ID:</strong> {user?.id}</p>
          </div>
        </div>

        {/* API Key Management */}
        <UserApiKeyForm
          currentKey={currentKey}
          onSubmit={handleSubmitKey}
          onRemove={handleRemoveKey}
        />
      </main>
    </div>
  )
}
