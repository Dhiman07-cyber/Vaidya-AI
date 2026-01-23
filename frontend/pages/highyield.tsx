import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import { supabase, AuthUser } from '@/lib/supabase'
import DashboardLayout from '@/components/DashboardLayout'
import { parseMarkdown } from '@/lib/markdown'
import styles from '@/styles/HighYield.module.css'
import SessionSidebar, { ChatSession } from '@/components/SessionSidebar'
import { Sparkles, FileText, Trash2, Search, ArrowRight, BookOpen, Star } from 'lucide-react'

// Quick topic suggestions
const SUGGESTIONS = [
  'Cardiac Cycle',
  'Diabetes Mellitus',
  'Rheumatoid Arthritis',
  'Acute Pancreatitis',
  'Glomerulonephritis',
  'Multiple Sclerosis'
]

export default function HighYield() {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [topic, setTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeDocument, setActiveDocument] = useState<any>(null)

  // Session state
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [sessionsError, setSessionsError] = useState<string | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    checkAuth()
    checkDocumentContext()
  }, [])

  const checkDocumentContext = () => {
    const documentId = router.query.document as string
    if (documentId) {
      const stored = sessionStorage.getItem('activeDocument')
      if (stored) {
        try {
          const docData = JSON.parse(stored)
          if (docData.id === documentId) {
            setActiveDocument(docData)
          }
        } catch (e) {
          console.error('Failed to parse document data:', e)
        }
      }
    }
  }

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      router.push('/')
      return
    }
    setUser(session.user as AuthUser)

    // Load sessions
    loadSessions(session.access_token)

    setLoading(false)
  }

  const loadSessions = async (token: string) => {
    try {
      setSessionsLoading(true)
      const response = await fetch(`${API_URL}/api/study-tools/sessions?feature=highyield`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      }
    } catch (err) {
      console.error('Failed to load sessions:', err)
    } finally {
      setSessionsLoading(false)
    }
  }

  const handleSelectSession = async (sessionId: string) => {
    try {
      setCurrentSessionId(sessionId)
      setResult(null) // Clear current result while loading
      setGenerating(true) // Show loading state

      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      // Load session materials
      const response = await fetch(`${API_URL}/api/study-tools/sessions/${sessionId}/materials`, {
        headers: { Authorization: `Bearer ${session.access_token}` }
      })

      if (response.ok) {
        const materials = await response.json()
        if (materials && materials.length > 0) {
          // Use the most recent material
          const latest = materials[0]
          setResult({
            content: latest.content,
            topic: latest.topic,
            // Citations might be missing in history per backend impl, but we use what we have
          })
          setTopic(latest.topic || '')
        }
      }
    } catch (err) {
      console.error('Failed to select session:', err)
      setError('Failed to load session content')
    } finally {
      setGenerating(false)
    }
  }

  const handleNewSession = () => {
    setCurrentSessionId(null)
    setResult(null)
    setTopic('')
    setError(null)
  }

  const handleDeleteSession = async (sessionId: string) => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      await fetch(`${API_URL}/api/study-tools/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${session.access_token}` }
      })

      setSessions(prev => prev.filter(s => s.id !== sessionId))
      if (currentSessionId === sessionId) {
        handleNewSession()
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  const handleDeleteAllSessions = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      await fetch(`${API_URL}/api/study-tools/sessions/all?feature=highyield`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${session.access_token}` }
      })

      setSessions([])
      handleNewSession()
    } catch (err) {
      console.error('Failed to delete all sessions:', err)
    }
  }

  const handleGenerate = async (selectedTopic?: string) => {
    const targetTopic = selectedTopic || topic
    if (!targetTopic.trim()) {
      setError('Please enter a topic')
      return
    }

    if (selectedTopic) setTopic(selectedTopic)

    setGenerating(true)
    setError(null)
    setResult(null)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token

      // If document is active, search for relevant context
      let documentContext = ''
      if (activeDocument) {
        try {
          const searchResponse = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/api/documents/search?query=${encodeURIComponent(targetTopic)}&feature=highyield&top_k=5`,
            {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            }
          )

          if (searchResponse.ok) {
            const searchResults = await searchResponse.json()
            if (searchResults.length > 0) {
              documentContext = '\n\n[Document Context]\n' + searchResults.map((r: any) => r.content).join('\n\n')
            }
          }
        } catch (searchErr) {
          console.error('Document search failed:', searchErr)
        }
      }

      const topicWithContext = documentContext ? targetTopic + documentContext : targetTopic

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/study-tools/highyield`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            topic: topicWithContext,
            format: 'interactive',
            session_id: currentSessionId // Pass current session ID if exists
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.error?.message || 'Failed to generate high-yield notes')
      }

      const data = await response.json()
      setResult(data)

      // Update session if it was new or changed
      if (data.session_id) {
        setCurrentSessionId(data.session_id)
        // Reload sessions to update the list (title might have changed or new session created)
        loadSessions(token!)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate high-yield notes')
    } finally {
      setGenerating(false)
    }
  }

  if (loading || !user) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#fdfbf7' }}>
        <div className={styles.loadingSpinner} style={{ borderTopColor: '#8B5CF6' }}></div>
      </div>
    )
  }

  return (
    <>
      <Head>
        <title>High Yield - Vaidya AI</title>
      </Head>
      <DashboardLayout user={user}>
        <div style={{
          height: 'calc(100vh - 64px)',
          display: 'flex',
          backgroundColor: '#fdfbf7',
          overflow: 'hidden',
          position: 'relative'
        }}>
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div className={styles.hyWrapper} data-station-active="true">
              <div className={styles.mainContent}>

                {/* RAG Banner */}
                {activeDocument && (
                  <div style={{
                    background: 'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)',
                    color: 'white',
                    padding: '12px 20px',
                    borderRadius: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '24px',
                    boxShadow: '0 10px 20px rgba(139, 92, 246, 0.2)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ background: 'rgba(255,255,255,0.2)', padding: '8px', borderRadius: '10px' }}>
                        <BookOpen size={18} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '14px' }}>RAG Enabled: Contextual Analysis</div>
                        <div style={{ fontSize: '12px', opacity: 0.9 }}>{activeDocument.filename}</div>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setActiveDocument(null)
                        sessionStorage.removeItem('activeDocument')
                        router.push('/highyield')
                      }}
                      style={{
                        background: 'rgba(255, 255, 255, 0.2)',
                        border: 'none',
                        color: 'white',
                        padding: '6px 14px',
                        borderRadius: '10px',
                        cursor: 'pointer',
                        fontSize: '12px',
                        fontWeight: 700,
                        transition: 'all 0.2s'
                      }}
                    >
                      Disable Context
                    </button>
                  </div>
                )}

                {!result && !generating ? (
                  <div className={styles.landingView}>
                    <div className={styles.heroIcon}>
                      <Star fill="white" size={48} color="white" />
                    </div>
                    <div className={styles.heroText}>
                      <h1>High-Yield Notes</h1>
                      <p>Transform deep medical topics into structured, clinical summary points</p>
                    </div>

                    <div className={styles.inputSection}>
                      <input
                        type="text"
                        placeholder="Enter a medical topic (e.g. 'Atrial Fibrillation')"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
                        className={styles.topicInput}
                      />
                      <button
                        onClick={() => handleGenerate()}
                        disabled={generating || !topic.trim()}
                        className={styles.generateBtn}
                      >
                        Generate Notes
                        <ArrowRight size={18} />
                      </button>
                    </div>

                    <div className={styles.quickSuggestions}>
                      {SUGGESTIONS.map((s) => (
                        <button
                          key={s}
                          className={styles.suggestionChip}
                          onClick={() => handleGenerate(s)}
                        >
                          {s}
                        </button>
                      ))}
                    </div>

                    {error && (
                      <div className={styles.errorBanner}>
                        <Sparkles size={18} />
                        {error}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className={styles.resultsView}>
                    <div className={styles.resultHeader}>
                      <div className={styles.resultTitle}>
                        <div className={styles.titleIcon}>
                          <FileText size={20} />
                        </div>
                        <div>
                          <h2>High-Yield Summary</h2>
                          <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748B' }}>Topic: {topic}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setResult(null)
                          setTopic('')
                          // Don't clear session here, just the view. Or maybe we want New Session?
                          // For now, let's just clear the view, matching previous behavior.
                          // But if we are in a session, clearing view might be confusing.
                          // Let's call handleNewSession() which does both.
                          handleNewSession()
                        }}
                        className={styles.clearBtn}
                      >
                        <Trash2 size={16} style={{ marginRight: 8, display: 'inline' }} />
                        Clear Results
                      </button>
                    </div>

                    {error && (
                      <div className={styles.errorBanner}>
                        <Sparkles size={18} />
                        {error}
                      </div>
                    )}

                    <div className={styles.resultCard}>
                      {generating ? (
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px' }}>
                          <div className={styles.loadingSpinner} style={{ width: '40px', height: '40px', borderTopColor: '#8B5CF6', marginBottom: '20px' }}></div>
                          <p style={{ fontWeight: 600, color: '#475569' }}>Synthesizing high-yield content...</p>
                        </div>
                      ) : (
                        <div className={styles.scrollArea} data-lenis-prevent>
                          <div className={styles.noteContent}>
                            <div dangerouslySetInnerHTML={{ __html: parseMarkdown(result?.content || '') }} />
                          </div>

                          {result?.citations && (
                            <div className={styles.citationsSection}>
                              <h4>Evidence-Based Citations</h4>
                              {result.citations.sources?.map((source: any, idx: number) => (
                                <div key={idx} className={styles.citationItem}>
                                  <FileText size={14} />
                                  {source.document_filename}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <SessionSidebar
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelectSession={handleSelectSession}
            onNewSession={handleNewSession}
            onDeleteSession={handleDeleteSession}
            onDeleteAllSessions={handleDeleteAllSessions}
            isNewChatDisabled={false}
            loading={sessionsLoading}
            error={sessionsError}
            position="right"
            newSessionLabel="New Topic"
            untitledLabel="Untitled Topic"
          />
        </div>
      </DashboardLayout>
    </>
  )
}
