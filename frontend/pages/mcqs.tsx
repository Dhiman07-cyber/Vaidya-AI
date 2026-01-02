import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import { supabase } from '@/lib/supabase'
import Layout from '@/components/Layout'
import styles from '@/styles/StudyTools.module.css'

interface Session {
  id: string
  title: string
  created_at: string
}

interface Material {
  id: string
  topic: string
  content: string
  created_at: string
}

export default function MCQs() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSession, setCurrentSession] = useState<string | null>(null)
  const [materials, setMaterials] = useState<Material[]>([])
  const [topic, setTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkAuth()
  }, [])

  useEffect(() => {
    if (user) {
      loadSessions()
    }
  }, [user])

  useEffect(() => {
    if (currentSession) {
      loadMaterials(currentSession)
    }
  }, [currentSession])

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      router.push('/')
      return
    }
    setUser(session.user)
    setLoading(false)
  }

  const loadSessions = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/study-tools/sessions/mcq`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setSessions(data)
        if (data.length > 0 && !currentSession) {
          setCurrentSession(data[0].id)
        }
      }
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }

  const loadMaterials = async (sessionId: string) => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/study-tools/sessions/${sessionId}/materials`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setMaterials(data)
      }
    } catch (err) {
      console.error('Failed to load materials:', err)
    }
  }

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic')
      return
    }

    setGenerating(true)
    setError(null)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/study-tools/mcqs`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            topic: topic,
            session_id: currentSession
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.error?.message || 'Failed to generate MCQs')
      }

      const data = await response.json()
      
      await loadSessions()
      if (data.session_id) {
        setCurrentSession(data.session_id)
        await loadMaterials(data.session_id)
      }
      
      setTopic('')
    } catch (err: any) {
      setError(err.message || 'Failed to generate MCQs')
    } finally {
      setGenerating(false)
    }
  }

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Delete this session and all its MCQs?')) return

    try {
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/study-tools/sessions/${sessionId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        await loadSessions()
        if (currentSession === sessionId) {
          setCurrentSession(null)
          setMaterials([])
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className={styles.loading}>Loading...</div>
      </Layout>
    )
  }

  return (
    <Layout>
      <Head>
        <title>MCQ Practice - VaidyaAI</title>
      </Head>

      <div className={styles.container}>
        <div className={styles.header}>
          <h1>📝 MCQ Practice</h1>
          <p>Generate multiple choice questions for any medical topic</p>
        </div>

        <div className={styles.twoColumn}>
          <div className={styles.sidebar}>
            <h3>Sessions</h3>
            <div className={styles.sessionList}>
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`${styles.sessionItem} ${currentSession === session.id ? styles.active : ''}`}
                  onClick={() => setCurrentSession(session.id)}
                >
                  <div className={styles.sessionTitle}>{session.title}</div>
                  <div className={styles.sessionDate}>
                    {new Date(session.created_at).toLocaleDateString()}
                  </div>
                  <button
                    className={styles.deleteBtn}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteSession(session.id)
                    }}
                  >
                    🗑️
                  </button>
                </div>
              ))}
              {sessions.length === 0 && (
                <div className={styles.emptyState}>No sessions yet</div>
              )}
            </div>
          </div>

          <div className={styles.mainContent}>
            <div className={styles.inputSection}>
              <input
                type="text"
                placeholder="Enter a medical topic (e.g., 'diabetes mellitus')"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
                className={styles.topicInput}
              />
              <button
                onClick={handleGenerate}
                disabled={generating}
                className={styles.generateBtn}
              >
                {generating ? 'Generating...' : 'Generate'}
              </button>
            </div>

            {error && (
              <div className={styles.error}>
                ⚠️ {error}
              </div>
            )}

            <div className={styles.materialsContainer}>
              {materials.map((material) => (
                <div key={material.id} className={styles.materialCard}>
                  <div className={styles.materialHeader}>
                    <h3>{material.topic}</h3>
                    <span className={styles.materialDate}>
                      {new Date(material.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className={styles.materialContent}>
                    {material.content}
                  </div>
                </div>
              ))}
              {materials.length === 0 && !generating && (
                <div className={styles.placeholder}>
                  <div className={styles.placeholderIcon}>📝</div>
                  <h3>Ready to generate MCQs</h3>
                  <p>Enter a topic above and click Generate</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
