import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import { supabase, AuthUser } from '@/lib/supabase'
import DashboardLayout from '@/components/DashboardLayout'
import ClinicalMapViewer, { parseClinicalMapData, MapNode, MapConnection } from '@/components/ClinicalMapViewer'
import styles from '@/styles/ConceptMap.module.css'

interface ConceptMapSession {
  id: string
  title: string
  created_at: string
  updated_at: string
}

interface ConceptMapMaterial {
  id: string
  topic: string
  content: string
  created_at: string
}

export default function ConceptMap() {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [topic, setTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // History management
  const [sessions, setSessions] = useState<ConceptMapSession[]>([])
  const [currentSession, setCurrentSession] = useState<ConceptMapSession | null>(null)
  const [materials, setMaterials] = useState<ConceptMapMaterial[]>([])
  const [currentMaterial, setCurrentMaterial] = useState<ConceptMapMaterial | null>(null)

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
      loadMaterials(currentSession.id)
    }
  }, [currentSession])

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      router.push('/')
      return
    }
    setUser(session.user as AuthUser)
    setLoading(false)
  }

  const loadSessions = async () => {
    try {
      const { data, error } = await supabase
        .from('study_tool_sessions')
        .select('*')
        .eq('feature', 'map')
        .order('updated_at', { ascending: false })

      if (error) throw error
      setSessions(data || [])
      
      // Auto-select most recent session
      if (data && data.length > 0 && !currentSession) {
        setCurrentSession(data[0])
      }
    } catch (err: any) {
      console.error('Failed to load sessions:', err)
    }
  }

  const loadMaterials = async (sessionId: string) => {
    try {
      const { data, error } = await supabase
        .from('study_materials')
        .select('*')
        .eq('session_id', sessionId)
        .order('created_at', { ascending: false })
      
      if (error) throw error
      setMaterials(data || [])
      
      if (data && data.length > 0) {
        setCurrentMaterial(data[0])
      } else {
        setCurrentMaterial(null)
      }
    } catch (err: any) {
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
        `${process.env.NEXT_PUBLIC_API_URL}/api/study-tools/conceptmap`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            topic: topic,
            format: 'interactive'
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.error?.message || 'Failed to generate concept map')
      }

      const data = await response.json()
      
      // Reload sessions to show the new one
      await loadSessions()
      
      // If we have a session_id in the response, load that session's materials
      if (data.session_id) {
        // Find the session
        const { data: sessionData } = await supabase
          .from('study_tool_sessions')
          .select('*')
          .eq('id', data.session_id)
          .single()
        
        if (sessionData) {
          setCurrentSession(sessionData)
          await loadMaterials(data.session_id)
        }
      }
      
      setTopic('')
      
    } catch (err: any) {
      setError(err.message || 'Failed to generate concept map')
    } finally {
      setGenerating(false)
    }
  }

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm('Delete this session and all its concept maps?')) return

    try {
      const { error } = await supabase
        .from('study_tool_sessions')
        .delete()
        .eq('id', sessionId)

      if (error) throw error

      // Reload sessions
      await loadSessions()
      
      // Clear current session if it was deleted
      if (currentSession?.id === sessionId) {
        setCurrentSession(null)
        setMaterials([])
        setCurrentMaterial(null)
      }
    } catch (err: any) {
      console.error('Failed to delete session:', err)
      setError('Failed to delete session')
    }
  }

  if (loading || !user) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <p>Loading...</p>
      </div>
    )
  }

  // Parse map data with proper typing
  let mapNodes: MapNode[] = []
  let mapConnections: MapConnection[] = []
  
  if (currentMaterial?.content) {
    const parsed = parseClinicalMapData(currentMaterial.content)
    mapNodes = parsed.nodes
    mapConnections = parsed.connections
  }

  // Calculate stats
  const stats = {
    symptoms: mapNodes.filter(n => n.type === 'symptom').length,
    diagnosis: mapNodes.filter(n => n.type === 'diagnosis').length,
    riskFactors: mapNodes.filter(n => n.type === 'complication').length,
    treatments: mapNodes.filter(n => n.type === 'treatment').length
  }

  return (
    <>
      <Head>
        <title>Clinical Map - VaidyaAI</title>
      </Head>
      <DashboardLayout user={user}>
        <div className={styles.container}>
          <div className={styles.header}>
            <h1>Clinical Map</h1>
            <p>Here is a clinical map summarizing key information about medical topics.</p>
          </div>

          <div className={styles.mainLayout}>
            {/* Left Sidebar - History */}
            <div className={styles.sidebar}>
              <h3>History</h3>
              <div className={styles.sessionList}>
                {sessions.length === 0 ? (
                  <div className={styles.emptyState}>No previous maps</div>
                ) : (
                  sessions.map((session) => (
                    <div
                      key={session.id}
                      className={`${styles.sessionItem} ${currentSession?.id === session.id ? styles.active : ''}`}
                      onClick={() => setCurrentSession(session)}
                    >
                      <div className={styles.sessionTitle}>{session.title}</div>
                      <div className={styles.sessionDate}>
                        {new Date(session.created_at).toLocaleDateString()}
                      </div>
                      <button
                        className={styles.deleteBtn}
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        title="Delete session"
                      >
                        🗑️
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Main Content */}
            <div className={styles.mainContent}>
              {/* Input Section */}
              <div className={styles.inputSection}>
                <div className={styles.searchBox}>
                  <span className={styles.searchIcon}>🔍</span>
                  <input
                    type="text"
                    placeholder="Pulmonary Embolism"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
                    className={styles.topicInput}
                  />
                </div>
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

              {/* Concept Map Display */}
              {currentMaterial ? (
                <div className={styles.mapContainer}>
                  <div className={styles.mapHeader}>
                    <h2>Clinical Map</h2>
                  </div>
                  
                  <div className={styles.mapContent}>
                    <ClinicalMapViewer
                      title={currentMaterial.topic}
                      nodes={mapNodes}
                      connections={mapConnections}
                    />
                  </div>
                </div>
              ) : (
                <div className={styles.placeholder}>
                  <div className={styles.placeholderIcon}>🗺️</div>
                  <h3>Ready to generate clinical maps</h3>
                  <p>Enter a topic above and click Generate</p>
                </div>
              )}
            </div>

            {/* Right Sidebar - Card Summary */}
            <div className={styles.rightSidebar}>
              <h3>Card Summary</h3>
              
              {currentMaterial ? (
                <div className={styles.summaryCard}>
                  <div className={styles.topicIcon}>
                    <div className={styles.iconCircle}>🫁</div>
                  </div>
                  <h4 className={styles.topicTitle}>{currentMaterial.topic}</h4>
                  
                  <div className={styles.statsSection}>
                    <div className={styles.statItem}>
                      <span className={styles.statIcon}>🔵</span>
                      <span className={styles.statLabel}>System:</span>
                      <span className={styles.statValue}>Card</span>
                    </div>
                    
                    <div className={styles.statItem}>
                      <span className={styles.statIcon}>🔺</span>
                      <span className={styles.statLabel}>Diagnostics:</span>
                      <div className={styles.statBadges}>
                        {stats.diagnosis > 0 && (
                          <span className={styles.badge}>D-Dimer</span>
                        )}
                        {stats.diagnosis > 1 && (
                          <span className={styles.badge}>CTPA</span>
                        )}
                        {stats.diagnosis > 2 && (
                          <span className={styles.badge}>V/Q Scan</span>
                        )}
                      </div>
                    </div>
                    
                    <div className={styles.statItem}>
                      <span className={styles.statIcon}>🟩</span>
                      <span className={styles.statLabel}>Treatments:</span>
                      <div className={styles.treatmentList}>
                        {stats.treatments > 0 && <div className={styles.treatmentItem}>✓ Heparin</div>}
                        {stats.treatments > 1 && <div className={styles.treatmentItem}>✓ Alteplase</div>}
                        {stats.treatments > 2 && <div className={styles.treatmentItem}>✓ Warfarin</div>}
                      </div>
                    </div>
                  </div>
                  
                  <div className={styles.legend}>
                    <h4>Legend</h4>
                    <div className={styles.legendItems}>
                      <div className={styles.legendItem}>
                        <span className={styles.legendColor} style={{ background: '#f093fb' }}></span>
                        <span>Symptoms</span>
                        <span className={styles.legendCount}>{stats.symptoms}</span>
                      </div>
                      <div className={styles.legendItem}>
                        <span className={styles.legendColor} style={{ background: '#4facfe' }}></span>
                        <span>Diagnosis</span>
                        <span className={styles.legendCount}>{stats.diagnosis}</span>
                      </div>
                      <div className={styles.legendItem}>
                        <span className={styles.legendColor} style={{ background: '#fa709a' }}></span>
                        <span>Risk Factors</span>
                        <span className={styles.legendCount}>{stats.riskFactors}</span>
                      </div>
                      <div className={styles.legendItem}>
                        <span className={styles.legendColor} style={{ background: '#43e97b' }}></span>
                        <span>Treatment</span>
                        <span className={styles.legendCount}>{stats.treatments}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className={styles.emptyState}>
                  Generate a map to see summary
                </div>
              )}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </>
  )
}
