import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import { supabase, AuthUser } from '@/lib/supabase'
import DashboardLayout from '@/components/DashboardLayout'
import { parseMarkdown } from '@/lib/markdown'
import { Check, X, ChevronRight, Send, Search, MoreHorizontal, BookOpen, Clock, Activity, ArrowRight, Sparkles, Plus, Trash2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import SessionSidebar, { ChatSession } from '@/components/SessionSidebar'

// Tailwind class mappings
// Premium styles (for consistency)
const styles = {
  container: "max-w-[1200px] mx-auto",
  mainArea: "flex-1 flex flex-col overflow-y-auto p-4 pt-20 sm:p-10 custom-scrollbar bg-[var(--bg-main)]", // Matches chat theme color
  searchOnlyState: "bg-[var(--bg-card)] rounded-[24px] sm:rounded-[32px] p-6 sm:p-10 text-center border border-[var(--border-subtle)] mt-4 sm:mt-0 w-full max-w-[750px] mx-auto",
  sparkleIcon: "w-10 h-10 sm:w-14 sm:h-14 bg-[#F0FDF4] dark:bg-green-900/30 rounded-xl sm:rounded-2xl mx-auto mb-3 sm:mb-4 flex items-center justify-center",
  h1: "text-2xl sm:text-2xl font-[800] mb-1 sm:mb-2 text-[#064E3B] dark:text-green-300",
  p: "text-sm sm:text-base text-[#64748B] dark:text-slate-300 mb-5 sm:mb-6",
  largeSearch: "bg-[var(--bg-card)] border-[1.5px] border-[var(--border-subtle)] p-1.5 pl-4 sm:p-1.5 sm:pl-5 rounded-xl sm:rounded-2xl flex items-center gap-2 sm:gap-3 focus-within:border-[#10B981] focus-within:ring-4 focus-within:ring-[#10B981]/5 transition-all outline-none",
  topicInput: "border-none bg-transparent flex-1 text-sm sm:text-base font-medium outline-none text-[#1E293B] dark:text-slate-100 min-w-0",
  generateBtn: "bg-gradient-to-br from-[#6366F1] to-[#4F46E5] text-white border-none px-4 py-2.5 sm:px-6 sm:py-3 rounded-lg sm:rounded-xl font-bold cursor-pointer hover:translate-y-[-2px] transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap text-sm sm:text-base",
  activeHeader: "flex flex-col gap-3 mb-6 sm:mb-10 w-full",
  breadcrumb: "flex items-center gap-1.5 text-[10px] sm:text-xs font-bold text-[#94A3B8] dark:text-slate-400 pl-1 tracking-wider uppercase",
  miniSearch: "flex items-center justify-between bg-[var(--bg-card)] px-4 py-2.5 sm:px-6 sm:py-3 rounded-xl sm:rounded-2xl border-2 border-[#10B981]/20 w-full",
  aiMessage: "flex flex-col gap-3 mb-6 sm:mb-10 items-start",
  aiAvatar: "hidden",
  aiBubble: "bg-[var(--bg-card)] p-6 sm:p-10 rounded-2xl sm:rounded-3xl border border-[var(--border-subtle)] w-full text-[var(--text-main)] leading-relaxed text-sm sm:text-[17px]",
  resultCard: "bg-[var(--bg-card)] rounded-2xl sm:rounded-3xl p-6 sm:p-12 border border-[var(--border-subtle)] border-2",
  citations: "mt-8 sm:mt-12 pt-6 sm:pt-8 border-t border-[var(--border-subtle)]",
  citation: "bg-[var(--accent-soft)] px-3 py-2 sm:px-4 sm:py-3 rounded-lg sm:rounded-xl mb-2 text-[var(--text-muted)] font-medium border border-[var(--border-subtle)] flex items-center gap-2 text-xs sm:text-sm"
}

export default function Explain() {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [topic, setTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [sessionsError, setSessionsError] = useState<string | null>(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [activeDocument, setActiveDocument] = useState<any>(null)
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    checkAuth()
  }, [])

  // Check for document context
  useEffect(() => {
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
  }, [router.query.document])

  const checkAuth = async () => {
    try {
      const { data, error } = await supabase.auth.getSession()
      if (error || !data.session) {
        console.warn('Auth session missing or Supabase unreachable (explain)')
        router.push('/')
        return
      }
      setUser(data.session.user as AuthUser)
      loadSessions(data.session.access_token)
    } catch (err) {
      console.error('Supabase auth failure (explain):', err)
      setError('Connection failed: Identity service unreachable.')
    } finally {
      setLoading(false)
    }
  }

  const getAuthToken = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
  }

  const loadSessions = async (token?: string) => {
    try {
      setSessionsLoading(true)
      setSessionsError(null)
      const authToken = token || await getAuthToken()
      if (!authToken) return

      const response = await fetch(`${API_URL}/api/study-tools/sessions?feature=explain`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      }).catch(err => {
        throw new Error('Connection failed: Backend server unreachable.')
      })

      if (response && response.ok) {
        const data = await response.json()
        setSessions(data)
      } else {
        setSessionsError('Failed to load sessions')
      }
    } catch (err: any) {
      console.error('Failed to load sessions:', err)
      setSessionsError(err.message || 'Connection failed: Backend server unreachable.')
    } finally {
      setSessionsLoading(false)
    }
  }

  const loadSessionMaterials = async (sessionId: string) => {
    try {
      setGenerating(true)
      const authToken = await getAuthToken()
      if (!authToken) return

      const response = await fetch(`${API_URL}/api/study-tools/sessions/${sessionId}/materials`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      })

      if (response.ok) {
        const materials = await response.json()
        if (materials && materials.length > 0) {
          const material = materials[0]
          setTopic(material.topic)
          setResult(material)
        }
      }
    } catch (err) {
      console.error('Failed to load material:', err)
    } finally {
      setGenerating(false)
    }
  }

  const handleSelectSession = async (sessionId: string) => {
    setCurrentSessionId(sessionId)
    await loadSessionMaterials(sessionId)
  }

  const handleNewSession = () => {
    setCurrentSessionId(null)
    setResult(null)
    setTopic('')
  }

  const handleDeleteSession = async (sessionId: string) => {
    try {
      const authToken = await getAuthToken()
      if (!authToken) return

      const response = await fetch(`${API_URL}/api/study-tools/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${authToken}` }
      })

      if (response.ok) {
        setSessions(prev => prev.filter(s => s.id !== sessionId))
        if (currentSessionId === sessionId) {
          handleNewSession()
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  const handleDeleteAllSessions = async () => {
    try {
      const authToken = await getAuthToken()
      if (!authToken) return

      const response = await fetch(`${API_URL}/api/study-tools/sessions/all?feature=explain`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${authToken}` }
      })

      if (response.ok) {
        setSessions([])
        handleNewSession()
      }
    } catch (err) {
      console.error('Failed to delete all sessions:', err)
    }
  }

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic')
      return
    }

    setGenerating(true)
    setError(null)
    setResult(null)

    try {
      const authToken = await getAuthToken()
      if (!authToken) return

      // If document is active, search for relevant context
      let documentContext = ''
      if (activeDocument) {
        try {
          const searchResponse = await fetch(
            `${API_URL}/api/documents/search?query=${encodeURIComponent(topic)}&feature=explain&top_k=5`,
            {
              headers: { 'Authorization': `Bearer ${authToken}` }
            }
          )
          if (searchResponse.ok) {
            const searchData = await searchResponse.json()
            if (searchData.results && searchData.results.length > 0) {
              documentContext = searchData.results.map((r: any) => r.content).join('\n\n')
            }
          }
        } catch (err) {
          console.error('Failed to fetch document context:', err)
        }
      }

      const response = await fetch(
        `${API_URL}/api/study-tools/explain`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            topic: topic,
            session_id: currentSessionId,
            format: 'interactive',
            document_context: documentContext || undefined
          })
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.error?.message || 'Failed to generate explanation')
      }

      const data = await response.json()
      setResult(data)

      if (!currentSessionId) {
        setCurrentSessionId(data.session_id)
        loadSessions(authToken)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate explanation')
    } finally {
      setGenerating(false)
    }
  }

  if (loading || !user) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100dvh' }}>
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <>
      <Head>
        <title>Explain - Vaidya AI</title>
      </Head>
      <DashboardLayout user={user}>
        <div className="flex min-h-[calc(100dvh-64px)] relative bg-[var(--bg-main)]">
          {/* Floating Document Badge */}
          {activeDocument && (
            <div
              style={{
                position: 'fixed',
                top: '80px',
                right: '24px',
                zIndex: 1000,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'white',
                padding: '8px 16px',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                border: '2px solid #EF4444',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(239,68,68,0.2)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'
              }}
              title={`Using context from: ${activeDocument.filename}`}
            >
              <BookOpen size={16} color="#EF4444" />
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#EF4444' }}>
                {activeDocument.filename.length > 20
                  ? activeDocument.filename.substring(0, 20) + '...'
                  : activeDocument.filename}
              </span>
              <button
                onClick={() => {
                  setActiveDocument(null)
                  sessionStorage.removeItem('activeDocument')
                  router.push('/explain')
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94A3B8',
                  cursor: 'pointer',
                  padding: '2px',
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '18px',
                  lineHeight: 1
                }}
                title="Clear document context"
              >
                ×
              </button>
            </div>
          )}

          {/* Main Content Area */}
          <div 
            className="flex-1 p-[20px] lg:p-[40px] transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] max-lg:!mr-0 max-lg:!p-[20px]"
            style={{ marginRight: isSidebarCollapsed ? '80px' : '320px' }}
          >
            {!result && !generating ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={styles.searchOnlyState}
              >
                <div className={styles.sparkleIcon}>
                  <Sparkles size={32} color="#6366F1" />
                </div>
                <h1 className={styles.h1}>Detailed Explanations</h1>
                <p className={styles.p}>Enter any medical topic for a comprehensive breakdown</p>
                <div className={styles.largeSearch}>
                  <input
                    type="text"
                    placeholder="e.g. Heart Failure, Renal Physiology, Pharmacology..."
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
                    className={styles.topicInput}
                  />
                  <button
                    className={styles.generateBtn}
                    onClick={handleGenerate}
                    disabled={generating || !topic.trim()}
                  >
                    Explain
                  </button>
                </div>
              </motion.div>
            ) : generating ? (
              <div className="flex flex-col items-center justify-center flex-1 h-full">
                <Clock size={48} className="animate-spin mb-4 text-[#6366F1]" />
                <h3 className="text-xl font-bold text-[var(--text-main)]">Analyzing topic...</h3>
                <p className="text-[var(--text-muted)]">Synthesizing evidence-based explanation for {topic}</p>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="max-w-[1240px] mx-auto w-full"
              >
                <div className={styles.activeHeader}>
                  <div className={styles.breadcrumb}>
                    <span>{topic}</span>
                    <ChevronRight size={14} />
                  </div>
                </div>

                <div className={styles.aiMessage}>
                  <div className={styles.aiBubble}>
                    <p>I've prepared a detailed clinical breakdown of <strong>{topic}</strong>. Review the sections below for high-yield insights.</p>
                  </div>
                </div>

                <div className={styles.resultCard}>
                  <div className="flex justify-between items-center mb-8 pb-6 border-b-2 border-[#F0FDF4] dark:border-slate-600">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-[#10B981] to-[#059669] rounded-xl flex items-center justify-center">
                        <BookOpen size={20} className="text-white" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-[#064E3B] dark:text-green-400">Comprehensive Explanation</h3>
                        <p className="text-xs text-[#64748B] dark:text-slate-400 mt-0.5">Evidence-based clinical breakdown</p>
                      </div>
                    </div>
                    <button
                      onClick={handleNewSession}
                      className="text-xs font-bold text-white bg-gradient-to-r from-[#6366F1] to-[#4F46E5] hover:from-[#4F46E5] hover:to-[#4338CA] px-5 py-2.5 rounded-xl transition-all cursor-pointer uppercase tracking-wide shadow-md hover:shadow-lg transform hover:scale-105"
                    >
                      New Topic
                    </button>
                  </div>

                  <div className="explanation-content">
                    <div dangerouslySetInnerHTML={{ __html: parseMarkdown(result.content) }} />
                  </div>

                  {result.citations && (
                    <div className={styles.citations}>
                      <div className="flex items-center gap-2 mb-5">
                        <div className="w-8 h-8 bg-[#EEF2FF] dark:bg-slate-700 rounded-lg flex items-center justify-center">
                          <BookOpen size={16} className="text-[#6366F1] dark:text-indigo-400" />
                        </div>
                        <h4 className="text-base font-bold text-[#1E293B] dark:text-slate-100">Referenced Sources</h4>
                      </div>
                      <div className="grid gap-3">
                        {result.citations.sources?.map((source: any, idx: number) => (
                          <div key={idx} className="bg-gradient-to-r from-[#F8FAFC] to-[#F1F5F9] dark:from-slate-700 dark:to-slate-600 px-4 py-3 rounded-xl border border-[#E2E8F0] dark:border-slate-500 flex items-center gap-3 hover:shadow-md transition-shadow">
                            <div className="w-8 h-8 bg-white dark:bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                              <span className="text-xs font-bold text-[#6366F1] dark:text-indigo-400">{idx + 1}</span>
                            </div>
                            <span className="text-sm font-medium text-[#475569] dark:text-slate-200">{source.document_filename}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </div>

          <div className="static lg:fixed lg:top-[64px] lg:right-0 lg:bottom-0 z-10 bg-[var(--bg-sidebar)]">
            <SessionSidebar
              sessions={sessions}
              currentSessionId={currentSessionId}
              onSelectSession={handleSelectSession}
              onNewSession={handleNewSession}
              onDeleteSession={handleDeleteSession}
              onDeleteAllSessions={handleDeleteAllSessions}
              loading={sessionsLoading}
              error={sessionsError}
              position="right"
              newSessionLabel="New Topic"
              untitledLabel="Untitled Explanation"
              isCollapsed={isSidebarCollapsed}
              onToggleCollapsed={setIsSidebarCollapsed}
              disableMobileHamburger
            />
          </div>
        </div>

        <style jsx global>{`
          .custom-scrollbar::-webkit-scrollbar { width: 4px; }
          .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
          .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 10px; }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.2); }
          .animate-spin { animation: spin 1.5s linear infinite; }
          @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } 
          
                    
          /* Enhanced Explanation Content Styling */
          .explanation-content {
            font-size: 17px;
            line-height: 1.9;
            color: var(--text-main);
            max-width: 100%;
          }
          
          .explanation-content h1 {
            font-size: 36px;
            font-weight: 900;
            margin-top: 48px;
            margin-bottom: 32px;
            padding: 20px 24px;
            background: linear-gradient(135deg, #065F46 0%, #10B981 100%);
            color: white;
            border-radius: 16px;
            border-left: 6px solid #10B981;
            box-shadow: 0 8px 24px rgba(16, 185, 129, 0.35);
            letter-spacing: -0.03em;
            line-height: 1.2;
            position: relative;
            overflow: hidden;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
          }
          
          .explanation-content h1::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #10B981, #059669, #047857);
          }
          
          .explanation-content h1:first-child {
            margin-top: 0;
          }
          
          .explanation-content h2 {
            font-size: 28px;
            font-weight: 800;
            color: white;
            margin-top: 48px;
            margin-bottom: 24px;
            padding: 16px 20px;
            background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
            border-radius: 12px;
            border-left: 5px solid #6366F1;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
            letter-spacing: -0.02em;
            line-height: 1.3;
            position: relative;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
          }
          
          .explanation-content h2::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #818CF8, #6366F1);
            border-radius: 2px;
          }
          
          .explanation-content h3 {
            font-size: 24px;
            font-weight: 700;
            color: white;
            margin-top: 40px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            line-height: 1.3;
            padding: 14px 18px;
            background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%);
            border-radius: 10px;
            border-left: 4px solid #F59E0B;
            box-shadow: 0 4px 16px rgba(245, 158, 11, 0.35);
            position: relative;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
          }
          
          .explanation-content h3::after {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 60px;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1));
            border-radius: 0 10px 10px 0;
          }
          
          .explanation-content h3::before {
            content: "◆";
            color: white;
            font-size: 18px;
            flex-shrink: 0;
            font-weight: 900;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
          }
          
          .explanation-content p {
            margin-bottom: 20px;
            color: #1E293B;
            text-align: left;
            line-height: 1.8;
            letter-spacing: 0.005em;
            font-size: 17px;
            padding: 16px 20px;
            background: linear-gradient(135deg, #FAFAFA 0%, #F5F5F5 100%);
            border-radius: 8px;
            border-left: 3px solid #E5E7EB;
            transition: all 0.2s ease;
          }
          
          .dark .explanation-content p {
            color: var(--text-main);
            background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
            border-left-color: #475569;
          }
          
          .explanation-content p:hover {
            background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
            border-left-color: #9CA3AF;
          }
          
          .dark .explanation-content p:hover {
            background: linear-gradient(135deg, #334155 0%, #475569 100%);
            border-left-color: #64748B;
          }
          
          .explanation-content strong {
            font-weight: 800;
            color: #1E293B;
            background: linear-gradient(120deg, #FEF3C7 0%, #FDE68A 100%);
            padding: 4px 8px;
            border-radius: 6px;
            border: 1px solid #F59E0B;
            box-shadow: 0 2px 4px rgba(245, 158, 11, 0.1);
            display: inline-block;
          }
          
          .explanation-content em {
            font-style: italic;
            color: var(--text-muted);
          }
          
          .explanation-content code {
            background: var(--accent-soft);
            color: var(--accent-primary, #6366F1);
            padding: 4px 8px;
            border-radius: 6px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 15px;
            font-weight: 600;
            border: 1px solid var(--border-subtle);
          }
          
          .explanation-content pre {
            background: var(--accent-soft);
            padding: 20px;
            border-radius: 12px;
            overflow-x: auto;
            margin: 20px 0;
            border: 2px solid var(--border-subtle);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
          }
          
          .explanation-content pre code {
            background: transparent;
            padding: 0;
            border: none;
            color: var(--text-main);
            font-size: 14px;
            line-height: 1.7;
          }
          
          .explanation-content ul,
          .explanation-content > div > ul {
            margin: 24px 0 !important;
            padding-left: 0 !important;
            list-style: none !important;
            background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
          }
          
          .explanation-content ul li,
          .explanation-content > div > ul li {
            position: relative !important;
            padding: 12px 16px 12px 40px !important;
            margin-bottom: 16px !important;
            color: #1E293B !important;
            line-height: 1.7 !important;
            letter-spacing: 0.005em !important;
            font-size: 16px !important;
            font-weight: 500 !important;
            background: white !important;
            border-radius: 10px !important;
            border-left: 3px solid transparent !important;
            transition: all 0.2s ease !important;
          }
          
          .explanation-content ul li:hover,
          .explanation-content > div > ul li:hover {
            background: #F8FAFC !important;
            border-left-color: var(--accent-primary, #10B981) !important;
            transform: translateX(2px) !important;
          }
          
          .explanation-content ul li::before,
          .explanation-content > div > ul li::before {
            content: "▶" !important;
            position: absolute !important;
            left: 12px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: 8px !important;
            height: 8px !important;
            background: linear-gradient(135deg, var(--accent-primary, #10B981) 0%, var(--accent-primary-dark, #059669) 100%) !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 10px !important;
            font-weight: bold !important;
            color: white !important;
            box-shadow: 0 2px 6px rgba(16, 185, 129, 0.25) !important;
            flex-shrink: 0 !important;
          }
          
          .explanation-content ol,
          .explanation-content > div > ol {
            margin: 24px 0 !important;
            padding-left: 0 !important;
            list-style: none !important;
            counter-reset: item !important;
            background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            border: 1px solid #C7D2FE !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1) !important;
          }
          
          .explanation-content ol li,
          .explanation-content > div > ol li {
            position: relative !important;
            padding: 12px 16px 12px 48px !important;
            margin-bottom: 16px !important;
            color: #1E293B !important;
            line-height: 1.7 !important;
            counter-increment: item !important;
            letter-spacing: 0.005em !important;
            font-size: 16px !important;
            font-weight: 500 !important;
            background: white !important;
            border-radius: 10px !important;
            border-left: 3px solid transparent !important;
            transition: all 0.2s ease !important;
          }
          
          .explanation-content ol li:hover,
          .explanation-content > div > ol li:hover {
            background: #F8FAFC !important;
            border-left-color: var(--accent-secondary, #6366F1) !important;
            transform: translateX(2px) !important;
          }
          
          .explanation-content ol li::before,
          .explanation-content > div > ol li::before {
            content: counter(item) !important;
            position: absolute !important;
            left: 12px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: 24px !important;
            height: 24px !important;
            background: linear-gradient(135deg, var(--accent-secondary, #6366F1) 0%, var(--accent-secondary-dark, #4F46E5) 100%) !important;
            color: white !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 12px !important;
            font-weight: bold !important;
            box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25) !important;
            flex-shrink: 0 !important;
          }
          
          /* Nested Lists */
          .explanation-content ul ul, .explanation-content ol ol {
            margin: 12px 0 12px 20px;
            background: transparent;
            border: none;
            padding: 0;
            box-shadow: none;
          }
          
          .explanation-content ul ul li, .explanation-content ol ol li {
            background: rgba(248, 250, 252, 0.8);
            border-left: 2px solid #CBD5E1;
            padding: 8px 12px 8px 32px;
            margin-bottom: 8px;
            font-size: 15px;
            border-radius: 6px;
          }
          
          .explanation-content ul ul li::before {
            width: 6px;
            height: 6px;
            background: #64748B;
            left: 16px;
            content: "•";
            color: #64748B;
            font-size: 8px;
          }
          
          .explanation-content ol ol li::before {
            width: 18px;
            height: 18px;
            background: #94A3B8;
            left: 12px;
            font-size: 10px;
          }
          
          /* Strong text within lists */
          .explanation-content ul li strong, .explanation-content ol li strong {
            color: #1E293B;
            font-weight: 800;
            background: linear-gradient(120deg, #FEF3C7 0%, #FDE68A 100%) !important;
            padding: 3px 6px;
            border-radius: 4px;
            border: 1px solid #F59E0B;
            box-shadow: 0 1px 3px rgba(245, 158, 11, 0.2);
          }
          
          /* Topic section separators */
          .explanation-content > div {
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 2px solid #E5E7EB;
            position: relative;
          }
          
          .explanation-content > div:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
          }
          
          /* Enhanced Key Points section - using class-based approach */
          .explanation-content .key-points-section {
            margin-top: 40px !important;
            padding: 24px !important;
            background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%) !important;
            border-radius: 20px !important;
            border: 2px solid #FCA5A5 !important;
            box-shadow: 0 8px 32px rgba(220, 38, 38, 0.15) !important;
          }
          
          .explanation-content .key-points-section h3 {
            background: linear-gradient(135deg, #DC2626 0%, #EF4444 50%, #F87171 100%) !important;
            border-left-color: #DC2626 !important;
            box-shadow: 0 8px 24px rgba(220, 38, 38, 0.4) !important;
            margin-bottom: 24px !important;
            padding: 18px 22px !important;
            font-size: 26px !important;
          }
          
          .explanation-content .key-points-section h3::before {
            content: "★" !important;
            font-size: 24px !important;
          }
          
          .explanation-content .key-points-section ul {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
          }
          
          .explanation-content .key-points-section ul li {
            background: white !important;
            border-left: 4px solid #EF4444 !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            margin-bottom: 12px !important;
            font-size: 17px !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.1) !important;
            transition: all 0.3s ease !important;
          }
          
          .explanation-content .key-points-section ul li:hover {
            background: #FEF2F2 !important;
            border-left-color: #DC2626 !important;
            transform: translateX(4px) !important;
            box-shadow: 0 4px 16px rgba(220, 38, 38, 0.2) !important;
          }
          
          .explanation-content .key-points-section ul li::before {
            background: linear-gradient(135deg, #DC2626, #EF4444) !important;
            content: "✓" !important;
            font-size: 14px !important;
            width: 24px !important;
            height: 24px !important;
          }
          
          .explanation-content br {
            display: block;
            content: "";
            margin-top: 10px;
          }
          
          .explanation-content blockquote {
            background: var(--accent-soft);
            border-left: 4px solid var(--accent-warning, #F59E0B);
            padding: 18px 20px;
            margin: 20px 0;
            border-radius: 10px;
            font-style: italic;
            color: var(--text-main);
            box-shadow: 0 2px 6px rgba(245, 158, 11, 0.08);
            line-height: 1.8;
          }
          
          .explanation-content table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
          }
          
          .explanation-content th {
            background: linear-gradient(135deg, var(--accent-primary, #10B981) 0%, var(--accent-primary-dark, #059669) 100%);
            color: white;
            padding: 14px 16px;
            text-align: left;
            font-weight: 700;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
          }
          
          .explanation-content td {
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-subtle);
            background: var(--bg-card);
            color: var(--text-main);
            line-height: 1.7;
          }
          
          .explanation-content tr:last-child td {
            border-bottom: none;
          }
          
          .explanation-content tr:nth-child(even) td {
            background: var(--accent-soft);
          }
          
          .explanation-content a {
            color: var(--accent-secondary, #6366F1);
            text-decoration: none;
            font-weight: 600;
            border-bottom: 2px solid transparent;
            transition: border-color 0.2s;
          }
          
          .explanation-content a:hover {
            border-bottom-color: var(--accent-secondary, #6366F1);
          }
          
          /* Responsive adjustments */
          @media (max-width: 768px) {
            .explanation-content {
              font-size: 16px;
              line-height: 1.8;
            }
            
            .explanation-content h1 {
              font-size: 24px;
            }
            
            .explanation-content h2 {
              font-size: 20px;
            }
            
            .explanation-content h3 {
              font-size: 18px;
            }
            
            .explanation-content ul li,
            .explanation-content ol li {
              padding-left: 32px;
            }
          }
        `}</style>
      </DashboardLayout>
    </>
  )
}
