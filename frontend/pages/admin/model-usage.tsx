import Head from 'next/head'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { supabase, AuthUser } from '@/lib/supabase'
import AdminLayout from '@/components/AdminLayout'

interface UsageStats {
  total_calls: number
  successful_calls: number
  failed_calls: number
  total_tokens: number
  fallback_calls: number
  fallback_rate: number
  success_rate: number
  by_provider: Record<string, any>
  by_feature: Record<string, any>
  by_model: Record<string, any>
}

interface UsageLog {
  id: string
  user_id: string | null
  provider: string
  model: string
  feature: string
  success: boolean
  tokens_used: number
  error: string | null
  key_id: string | null
  was_fallback: boolean
  attempt_number: number
  response_time_ms: number | null
  timestamp: string
}

/**
 * Model Usage Dashboard
 * View API key usage, fallbacks, and performance metrics
 */
export default function ModelUsagePage() {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [isAdmin, setIsAdmin] = useState(false)
  const [stats, setStats] = useState<UsageStats | null>(null)
  const [logs, setLogs] = useState<UsageLog[]>([])
  const [statsLoading, setStatsLoading] = useState(false)
  const [logsLoading, setLogsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Filters
  const [providerFilter, setProviderFilter] = useState<string>('')
  const [featureFilter, setFeatureFilter] = useState<string>('')
  const [showOnlyFallbacks, setShowOnlyFallbacks] = useState(false)
  const [showOnlyFailures, setShowOnlyFailures] = useState(false)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const getAuthToken = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
  }

  useEffect(() => {
    const checkAdminAccess = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      
      if (!session) {
        router.push('/')
        return
      }

      setUser(session.user as AuthUser)
      
      try {
        // Verify admin status and load data
        await Promise.all([loadStats(), loadLogs()])
        setIsAdmin(true)
        setLoading(false)
      } catch (err) {
        console.error('Failed to load model usage data:', err)
        if (err instanceof Error && err.message.includes('403')) {
          router.push('/chat')
        } else {
          setError(err instanceof Error ? err.message : 'Failed to load data')
          setLoading(false)
        }
      }
    }

    checkAdminAccess()
  }, [router])

  const loadStats = async () => {
    try {
      setStatsLoading(true)
      setError(null)
      
      const authToken = await getAuthToken()
      if (!authToken) {
        throw new Error('No authentication token available')
      }

      const params = new URLSearchParams()
      if (providerFilter) params.append('provider', providerFilter)
      if (featureFilter) params.append('feature', featureFilter)

      const response = await fetch(`${API_URL}/api/admin/model-usage/stats?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      if (response.status === 403) {
        throw new Error('403: Access denied')
      }

      if (!response.ok) {
        throw new Error('Failed to load usage stats')
      }

      const data = await response.json()
      setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
      setError(err instanceof Error ? err.message : 'Failed to load stats')
    } finally {
      setStatsLoading(false)
    }
  }

  const loadLogs = async () => {
    try {
      setLogsLoading(true)
      setError(null)
      
      const authToken = await getAuthToken()
      if (!authToken) {
        throw new Error('No authentication token available')
      }

      const params = new URLSearchParams()
      params.append('limit', '100')
      if (providerFilter) params.append('provider', providerFilter)
      if (featureFilter) params.append('feature', featureFilter)

      const response = await fetch(`${API_URL}/api/admin/model-usage/logs?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to load usage logs')
      }

      const data = await response.json()
      setLogs(data.logs || data)
    } catch (err) {
      console.error('Failed to load logs:', err)
      setError(err instanceof Error ? err.message : 'Failed to load logs')
    } finally {
      setLogsLoading(false)
    }
  }

  const handleRefresh = () => {
    loadStats()
    loadLogs()
  }

  const filteredLogs = logs.filter(log => {
    if (showOnlyFallbacks && !log.was_fallback) return false
    if (showOnlyFailures && log.success) return false
    return true
  })

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <p>Loading...</p>
      </div>
    )
  }

  if (!user || !isAdmin) {
    return null
  }

  return (
    <>
      <Head>
        <title>Model Usage - Admin Panel</title>
        <meta name="description" content="View model usage and API key activity" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <AdminLayout user={user}>
        <div style={{ padding: '30px' }}>
          <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ marginBottom: '10px' }}>Model Usage Dashboard</h1>
              <p style={{ color: '#6c757d', margin: 0 }}>
                Track API key usage, fallbacks, and performance
              </p>
            </div>
            <button
              onClick={handleRefresh}
              style={{
                padding: '10px 20px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Refresh
            </button>
          </div>

          {error && (
            <div style={{
              padding: '15px',
              backgroundColor: '#f8d7da',
              color: '#721c24',
              borderRadius: '4px',
              marginBottom: '20px'
            }}>
              {error}
            </div>
          )}

          {/* Statistics Cards */}
          {stats && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px',
              marginBottom: '30px'
            }}>
              <div style={{
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '1px solid #dee2e6'
              }}>
                <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '5px' }}>Total Calls</div>
                <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats.total_calls}</div>
              </div>

              <div style={{
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '1px solid #dee2e6'
              }}>
                <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '5px' }}>Success Rate</div>
                <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#28a745' }}>
                  {stats.success_rate.toFixed(1)}%
                </div>
              </div>

              <div style={{
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '1px solid #dee2e6'
              }}>
                <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '5px' }}>Fallback Rate</div>
                <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#ffc107' }}>
                  {stats.fallback_rate.toFixed(1)}%
                </div>
              </div>

              <div style={{
                padding: '20px',
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '1px solid #dee2e6'
              }}>
                <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '5px' }}>Total Tokens</div>
                <div style={{ fontSize: '32px', fontWeight: 'bold' }}>
                  {stats.total_tokens.toLocaleString()}
                </div>
              </div>
            </div>
          )}

          {/* Filters */}
          <div style={{
            marginBottom: '20px',
            padding: '20px',
            backgroundColor: 'white',
            borderRadius: '8px',
            border: '1px solid #dee2e6'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '15px' }}>Filters</h3>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '15px',
              marginBottom: '15px'
            }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Provider:
                </label>
                <select
                  value={providerFilter}
                  onChange={(e) => setProviderFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    border: '1px solid #ced4da',
                    fontSize: '14px'
                  }}
                >
                  <option value="">All Providers</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="huggingface">Hugging Face</option>
                  <option value="gemini">Gemini</option>
                  <option value="openai">OpenAI</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Feature:
                </label>
                <select
                  value={featureFilter}
                  onChange={(e) => setFeatureFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    border: '1px solid #ced4da',
                    fontSize: '14px'
                  }}
                >
                  <option value="">All Features</option>
                  <option value="chat">Chat</option>
                  <option value="flashcard">Flashcards</option>
                  <option value="mcq">MCQs</option>
                  <option value="explain">Explain</option>
                  <option value="highyield">High-Yield</option>
                  <option value="conceptmap">Concept Map</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '15px', marginBottom: '15px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <input
                  type="checkbox"
                  checked={showOnlyFallbacks}
                  onChange={(e) => setShowOnlyFallbacks(e.target.checked)}
                />
                Show only fallbacks
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <input
                  type="checkbox"
                  checked={showOnlyFailures}
                  onChange={(e) => setShowOnlyFailures(e.target.checked)}
                />
                Show only failures
              </label>
            </div>

            <button
              onClick={handleRefresh}
              style={{
                padding: '8px 16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Apply Filters
            </button>
          </div>

          {/* Usage Logs Table */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            border: '1px solid #dee2e6',
            overflow: 'hidden'
          }}>
            <div style={{ padding: '20px', borderBottom: '1px solid #dee2e6' }}>
              <h3 style={{ margin: 0 }}>Recent API Calls</h3>
            </div>

            {logsLoading ? (
              <div style={{ padding: '40px', textAlign: 'center' }}>
                <p>Loading logs...</p>
              </div>
            ) : filteredLogs.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center' }}>
                <p style={{ color: '#6c757d' }}>No logs found</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  minWidth: '1000px'
                }}>
                  <thead>
                    <tr style={{
                      backgroundColor: '#f8f9fa',
                      borderBottom: '2px solid #dee2e6'
                    }}>
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Timestamp</th>
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Provider</th>
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Model</th>
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Feature</th>
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Status</th>
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Tokens</th>
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Fallback</th>
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Attempt</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLogs.map((log) => (
                      <tr
                        key={log.id}
                        style={{
                          borderBottom: '1px solid #dee2e6',
                          backgroundColor: log.was_fallback ? '#fff3cd' : 'white'
                        }}
                      >
                        <td style={{ padding: '12px', fontSize: '13px' }}>
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            backgroundColor: '#e9ecef',
                            color: '#495057'
                          }}>
                            {log.provider}
                          </span>
                        </td>
                        <td style={{ padding: '12px', fontSize: '13px', fontFamily: 'monospace' }}>
                          {log.model}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            backgroundColor: '#d1ecf1',
                            color: '#0c5460'
                          }}>
                            {log.feature}
                          </span>
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            backgroundColor: log.success ? '#d4edda' : '#f8d7da',
                            color: log.success ? '#155724' : '#721c24'
                          }}>
                            {log.success ? 'SUCCESS' : 'FAILED'}
                          </span>
                        </td>
                        <td style={{ padding: '12px', fontSize: '13px', textAlign: 'right' }}>
                          {log.tokens_used.toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          {log.was_fallback && (
                            <span style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: 'bold',
                              backgroundColor: '#ffc107',
                              color: '#000'
                            }}>
                              FALLBACK
                            </span>
                          )}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', fontSize: '13px' }}>
                          {log.attempt_number}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div style={{
              padding: '15px',
              backgroundColor: '#f8f9fa',
              borderTop: '1px solid #dee2e6',
              textAlign: 'center',
              color: '#6c757d',
              fontSize: '14px'
            }}>
              Showing {filteredLogs.length} log{filteredLogs.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </AdminLayout>
    </>
  )
}
