import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import { supabase } from '@/lib/supabase'
import Layout from '@/components/Layout'
import styles from '@/styles/Planner.module.css'

interface StudySession {
  id: string
  topic: string
  duration: number
  scheduled_date: string
  notes: string
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled'
  created_at: string
}

export default function Planner() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [sessions, setSessions] = useState<StudySession[]>([])
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    topic: '',
    duration: 60,
    scheduled_date: '',
    notes: ''
  })

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      router.push('/')
      return
    }
    setUser(session.user)
    await fetchSessions(session.access_token)
    setLoading(false)
  }

  const fetchSessions = async (token: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/study/sessions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { data: { session } } = await supabase.auth.getSession()
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/study/sessions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        await fetchSessions(session?.access_token!)
        setShowForm(false)
        setFormData({ topic: '', duration: 60, scheduled_date: '', notes: '' })
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const updateStatus = async (sessionId: string, status: string) => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/study/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status })
      })

      if (response.ok) {
        await fetchSessions(session?.access_token!)
      }
    } catch (error) {
      console.error('Failed to update session:', error)
    }
  }

  const deleteSession = async (sessionId: string) => {
    if (!confirm('Delete this study session?')) return

    try {
      const { data: { session } } = await supabase.auth.getSession()
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/study/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${session?.access_token}` }
      })

      if (response.ok) {
        await fetchSessions(session?.access_token!)
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className={styles.loading}>Loading...</div>
      </Layout>
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#48bb78'
      case 'in_progress': return '#4299e1'
      case 'planned': return '#ed8936'
      case 'cancelled': return '#f56565'
      default: return '#718096'
    }
  }

  return (
    <Layout>
      <Head>
        <title>Study Planner - VaidyaAI</title>
      </Head>

      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h1>Study Planner 📅</h1>
            <p>Organize and track your study sessions</p>
          </div>
          <button onClick={() => setShowForm(!showForm)} className={styles.addBtn}>
            {showForm ? 'Cancel' : '+ New Session'}
          </button>
        </div>

        {showForm && (
          <div className={styles.formCard}>
            <h3>Create Study Session</h3>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Topic</label>
                <input
                  type="text"
                  value={formData.topic}
                  onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                  placeholder="e.g., Cardiovascular System"
                  required
                />
              </div>
              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Duration (minutes)</label>
                  <input
                    type="number"
                    value={formData.duration}
                    onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) })}
                    min="15"
                    step="15"
                    required
                  />
                </div>
                <div className={styles.formGroup}>
                  <label>Scheduled Date</label>
                  <input
                    type="datetime-local"
                    value={formData.scheduled_date}
                    onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                  />
                </div>
              </div>
              <div className={styles.formGroup}>
                <label>Notes (optional)</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Study goals, resources, etc."
                  rows={3}
                />
              </div>
              <button type="submit" className={styles.submitBtn}>
                Create Session
              </button>
            </form>
          </div>
        )}

        <div className={styles.sessionsGrid}>
          {sessions.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📚</div>
              <h3>No study sessions yet</h3>
              <p>Create your first study session to get started</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div key={session.id} className={styles.sessionCard}>
                <div className={styles.sessionHeader}>
                  <h3>{session.topic}</h3>
                  <span
                    className={styles.statusBadge}
                    style={{ background: getStatusColor(session.status) }}
                  >
                    {session.status.replace('_', ' ')}
                  </span>
                </div>
                <div className={styles.sessionDetails}>
                  <div className={styles.detail}>
                    <span className={styles.detailIcon}>⏱️</span>
                    <span>{session.duration} minutes</span>
                  </div>
                  {session.scheduled_date && (
                    <div className={styles.detail}>
                      <span className={styles.detailIcon}>📅</span>
                      <span>{new Date(session.scheduled_date).toLocaleString()}</span>
                    </div>
                  )}
                </div>
                {session.notes && (
                  <div className={styles.sessionNotes}>
                    {session.notes}
                  </div>
                )}
                <div className={styles.sessionActions}>
                  {session.status === 'planned' && (
                    <button
                      onClick={() => updateStatus(session.id, 'in_progress')}
                      className={styles.actionBtn}
                    >
                      Start
                    </button>
                  )}
                  {session.status === 'in_progress' && (
                    <button
                      onClick={() => updateStatus(session.id, 'completed')}
                      className={styles.actionBtn}
                    >
                      Complete
                    </button>
                  )}
                  <button
                    onClick={() => deleteSession(session.id)}
                    className={styles.deleteBtn}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Layout>
  )
}
