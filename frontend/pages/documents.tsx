import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import { supabase, AuthUser } from '@/lib/supabase'
import DashboardLayout from '@/components/DashboardLayout'
import DocumentUpload from '../components/DocumentUpload'
import DocumentList, { Document } from '../components/DocumentList'
import {
  Search, Plus, ListFilter, Zap, Database, ShieldCheck, Activity, Trash2, AlertTriangle
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import styles from '@/styles/Documents.module.css'

export default function DocumentsPage() {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'all' | 'synced'>('all')
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [docToDelete, setDocToDelete] = useState<string | null>(null)

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
      setUser(user as AuthUser)
      await fetchDocuments()
    } catch (err) {
      setError('Failed to load user data')
    } finally {
      setLoading(false)
    }
  }

  const fetchDocuments = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documents`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      }).catch(err => {
        console.warn('Network error fetching documents:', err)
        return null
      })

      if (!response) {
        setDocuments([])
        return
      }

      if (!response.ok) throw new Error('Failed to fetch documents')

      const result = await response.json()
      setDocuments(result.documents || [])
    } catch (err) {
      console.error('Error fetching documents:', err)
    }
  }

  const confirmDelete = async () => {
    if (!docToDelete) return

    try {
      const { data: { session } } = await supabase.auth.getSession()
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/${docToDelete}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${session?.access_token}` }
      }).catch(err => {
        throw new Error('Connection failed. Backend server might be offline.')
      })

      if (response && response.ok) {
        setDocuments(documents.filter(doc => doc.id !== docToDelete))
        setSuccess('Archive successfully purged')
        setDocToDelete(null)
        setTimeout(() => setSuccess(null), 3000)
      } else {
        throw new Error('Purge failed')
      }
    } catch (err) {
      setError('Failed to delete document from vault')
      setDocToDelete(null)
      setTimeout(() => setError(null), 5000)
    }
  }

  const handleDeleteTrigger = async (id: string) => {
    setDocToDelete(id)
  }

  const handleUploadSuccess = () => {
    fetchDocuments()
    setSuccess('Secure synchronization complete')
    setTimeout(() => setSuccess(null), 4000)
  }

  const handleUploadError = (err: string) => {
    setError(err)
    setTimeout(() => setError(null), 5000)
  }

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
    if (activeTab === 'synced') return matchesSearch && doc.processing_status === 'completed'
    return matchesSearch
  })

  const stats = {
    count: documents.length,
    processed: documents.filter(d => d.processing_status === 'completed').length
  }

  return (
    <>
      <Head>
        <title>Clinical Vault | Vaidya AI</title>
      </Head>
      <DashboardLayout user={user}>
        {loading ? (
          <div className={`${styles.innerLoader} ${styles.noBorder}`}>
            <div className={styles.spinner}></div>
            <p style={{ fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.01em' }}>Initializing Clinical Workspace...</p>
          </div>
        ) : (
          <div className={`${styles.documentsContainer} ${styles.noBorder} ${isUploadModalOpen || docToDelete ? styles.blurredPage : ''}`}>
            {/* Header Action Unit */}
            <motion.header
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className={styles.heroHeader}
            >
              <div className={styles.headerIntro}>
                <h1 style={{ color: 'var(--text-main)' }}>Clinical Vault</h1>
                <p style={{ color: 'var(--text-secondary)' }}>Manage medical archives with AI-ready precision.</p>
              </div>

              <div className={styles.headerControls}>
                <div className={styles.searchBox}>
                  <Search size={20} className={styles.searchIcon} />
                  <input
                    type="text"
                    placeholder="Search medical tags, files, datasets..."
                    className={styles.searchInput}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <button
                  className={styles.uploadActionBtn}
                  onClick={() => setIsUploadModalOpen(true)}
                >
                  <Plus size={20} strokeWidth={3} />
                  New Archive
                </button>
              </div>
            </motion.header>

            <main className={styles.mainWorkspace}>
              <div className={styles.libraryGridWrap}>
                {/* Visual Tab Navigation */}
                <div className={styles.gridFilters}>
                  <div className={styles.activeFilters}>
                    <button
                      className={`${styles.filterPill} ${activeTab === 'all' ? styles.active : ''}`}
                      onClick={() => setActiveTab('all')}
                      style={{ color: activeTab === 'all' ? 'white' : '#000000' }}
                    >
                      All Documents
                    </button>
                    <button
                      className={`${styles.filterPill} ${activeTab === 'synced' ? styles.active : ''}`}
                      onClick={() => setActiveTab('synced')}
                      style={{ color: activeTab === 'synced' ? 'white' : '#000000' }}
                    >
                      Synced ({stats.processed})
                    </button>
                  </div>

                  <button className={styles.filterPill} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ListFilter size={14} style={{ color: 'inherit' }} />
                    Sort: Most Recent
                  </button>
                </div>

                <div className={styles.scrollableArea} data-lenis-prevent>
                  <DocumentList
                    documents={filteredDocuments}
                    onDelete={handleDeleteTrigger}
                    loading={false}
                  />
                </div>
              </div>

              {/* Sophisticated Sidebar - Cleaned Up */}
              <aside className={styles.insightSidebar}>
                <div className={styles.statsCluster}>
                  <div className={styles.statCard}>
                    <span className={styles.statValue}>{stats.count}</span>
                    <span className={styles.statTag}>Archives</span>
                  </div>
                  <div className={styles.statCard}>
                    <span className={styles.statValue}>{stats.processed}</span>
                    <span className={styles.statTag}>AI-Ready</span>
                  </div>
                </div>

                <div className={styles.intelWidget}>
                  <div className={styles.intelHeader}>
                    <div className={styles.intelIcon}>
                      <Zap size={20} />
                    </div>
                    <h3 style={{ color: 'var(--text-main, #111827)' }}>Medical Insight</h3>
                  </div>
                  <div className={styles.intelBody}>
                    <p style={{ color: 'var(--text-secondary, #6b7280)' }}>Your vault uses 256-bit encryption. Documents are automatically indexed for sub-second retrieval in clinical chats.</p>
                    <div className={styles.intelList}>
                      <div className={styles.intelItem}>
                        <Database size={14} />
                        <span>{documents.length > 0 ? (documents.length * 156).toLocaleString() : '0'} Vector Points Indexed</span>
                      </div>
                      <div className={styles.intelItem}>
                        <Activity size={14} />
                        {documents.some(d => d.processing_status === 'processing') ? (
                          <span style={{ color: '#F59E0B' }}>Syncing Active...</span>
                        ) : (
                          <span style={{ color: 'var(--text-secondary, #6b7280)' }}>Cloud OCR Synchronized</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className={styles.storageBarSection}>
                    <div className={styles.storageMeta}>
                      <span style={{ color: 'var(--text-secondary, #6b7280)' }}>Secure Vault Capacity</span>
                      <span style={{ color: 'var(--text-secondary, #6b7280)' }}>
                        {(() => {
                          const totalBytes = documents.reduce((acc, doc) => acc + (doc.file_size || 0), 0)
                          const limitBytes = 2 * 1024 * 1024 * 1024 // 2GB Limit
                          const percentage = Math.min((totalBytes / limitBytes) * 100, 100).toFixed(1)
                          return `${percentage}% Used`
                        })()}
                      </span>
                    </div>
                    <div className={styles.storageProgress}>
                      <div
                        className={styles.storageFill}
                        style={{
                          width: (() => {
                            const totalBytes = documents.reduce((acc, doc) => acc + (doc.file_size || 0), 0)
                            const limitBytes = 2 * 1024 * 1024 * 1024 // 2GB Limit
                            const percentage = Math.min((totalBytes / limitBytes) * 100, 100)
                            return `${percentage}%`
                          })()
                        }}
                      />
                    </div>
                  </div>
                </div>
              </aside>
            </main>
          </div>
        )}
      </DashboardLayout>

      {/* New Centered Prompt Upload Modal */}
      <AnimatePresence>
        {isUploadModalOpen && (
          <div className="modal-root-overlay">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="vault-modal-backdrop"
              onClick={() => setIsUploadModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="modal-content-container"
            >
              <DocumentUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                onClose={() => setIsUploadModalOpen(false)}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {docToDelete && (
          <div className="modal-root-overlay">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="vault-modal-backdrop"
              onClick={() => setDocToDelete(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="confirm-modal-box"
            >
              <div className="confirm-icon-wrap">
                <Trash2 size={32} />
              </div>
              <h2>Purge Archive?</h2>
              <p>This will permanently remove the medical record and all associated AI embeddings. This action cannot be undone.</p>

              <div className="confirm-buttons">
                <button className="burn-btn" onClick={confirmDelete}>
                  Confirm Purge
                </button>
                <button className="keep-btn" onClick={() => setDocToDelete(null)}>
                  Keep Archive
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {success && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className={styles.alertPop}
          >
            <ShieldCheck size={18} />
            {success}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className={`${styles.alertPop} ${styles.error}`}
          >
            <AlertTriangle size={18} />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      <style jsx global>{`
          /* COMPREHENSIVE BORDER RESET - PREVENT BLACK BORDER FLASH */
          *:not(.spinner):not([class*="spinner"]) {
              border-color: transparent !important;
              border-style: solid !important;
              border-width: 0 !important;
          }
          
          /* Only show borders when explicitly defined */
          [class*="border"], [style*="border"] {
              border-color: inherit !important;
              border-style: inherit !important;
              border-width: inherit !important;
          }
          
          /* Specific override for known border classes */
          .border, .border-1, .border-2, .border-4, .border-8 {
              border-color: inherit !important;
          }
          
          /* Fix spinner visibility - strong override */
          .spinner {
              border: 2px solid var(--border-strong, #d1d5db) !important;
              border-top: 3px solid #6366F1 !important;
              border-style: solid !important;
              border-width: 2px !important;
              border-radius: 50% !important;
          }
          
          .modal-root-overlay {
              position: fixed; 
              inset: 0; 
              z-index: 9999; 
              display: flex; 
              align-items: center; 
              justify-content: center; 
              padding: 20px;
              backdrop-filter: blur(12px) saturate(160%);
              -webkit-backdrop-filter: blur(12px) saturate(160%);
          }
          .vault-modal-backdrop {
              position: absolute; 
              inset: 0; 
              background: rgba(0, 0, 0, 0.4);
          }
          .modal-content-container {
              position: relative; 
              z-index: 10000; 
              width: 100%; 
              max-width: 520px;
          }
          
          /* Confirmation Modal Specifics */
          .confirm-modal-box {
              background: var(--bg-card, #ffffff);
              padding: 48px;
              border-radius: 32px;
              width: 100%;
              max-width: 440px;
              z-index: 10001;
              box-shadow: 0 40px 100px -20px rgba(0,0,0,0.2);
              border: 1px solid var(--border-subtle, #e5e7eb);
          }

          .confirm-icon-wrap {
              width: 72px;
              height: 72px;
              background: rgba(239, 68, 68, 0.1);
              color: #EF4444;
              border-radius: 20px;
              display: flex;
              align-items: center;
              justify-content: center;
              margin: 0 auto 24px;
          }

          .confirm-modal-box h2 {
              font-size: 24px;
              font-weight: 800;
              color: var(--text-main, #111827);
              margin: 0 0 12px;
              letter-spacing: -0.02em;
          }

          .confirm-modal-box p {
              color: var(--text-secondary, #6b7280);
              font-size: 15px;
              line-height: 1.6;
              font-weight: 500;
              margin: 0 0 32px;
          }

          .confirm-buttons {
              display: flex;
              flex-direction: column;
              gap: 12px;
          }

          .burn-btn {
              padding: 16px;
              background: #EF4444;
              color: white;
              border: none;
              border-radius: 16px;
              font-weight: 700;
              cursor: pointer;
              transition: all 0.2s;
          }

          .burn-btn:hover {
              background: #EF4444;
              transform: translateY(-2px);
              box-shadow: 0 8px 20px -4px rgba(239, 68, 68, 0.3);
          }

          .keep-btn {
              padding: 16px;
              background: var(--accent-soft, #f9fafb);
              color: var(--text-secondary, #6b7280);
              border: 1px solid var(--border-subtle, #e5e7eb);
              border-radius: 16px;
              font-weight: 700;
              cursor: pointer;
              transition: all 0.2s;
          }

          .keep-btn:hover {
              background: var(--bg-card, #ffffff);
              color: var(--text-main, #111827);
              border-color: var(--border-subtle, #e5e7eb);
          }
      `}</style>
    </>
  )
}
