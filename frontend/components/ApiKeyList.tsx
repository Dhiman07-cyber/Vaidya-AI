import { useState } from 'react'

export interface ApiKey {
  id: string
  provider: string
  feature: string
  key_value: string  // Encrypted/masked
  priority: number
  status: string
  failure_count: number
  last_used_at: string | null
  created_at: string
  updated_at: string
}

interface ApiKeyListProps {
  apiKeys: ApiKey[]
  loading: boolean
  onStatusToggle: (keyId: string, newStatus: string) => Promise<void>
  onDeleteKey: (keyId: string) => Promise<void>
  onPriorityChange: (keyId: string, newPriority: number) => Promise<void>
}

/**
 * API Key List Component
 * Displays list of API keys with management actions
 * Requirements: 14.1, 14.3
 */
export default function ApiKeyList({
  apiKeys,
  loading,
  onStatusToggle,
  onDeleteKey,
  onPriorityChange
}: ApiKeyListProps) {
  const [editingPriority, setEditingPriority] = useState<string | null>(null)
  const [priorityValue, setPriorityValue] = useState<number>(0)

  /**
   * Mask API key value to show only last 4 characters
   * Requirements: 14.3
   */
  const maskKeyValue = (keyValue: string): string => {
    if (!keyValue || keyValue.length <= 4) {
      return '****'
    }
    return '****' + keyValue.slice(-4)
  }

  const handlePriorityEdit = (keyId: string, currentPriority: number) => {
    setEditingPriority(keyId)
    setPriorityValue(currentPriority)
  }

  const handlePrioritySave = async (keyId: string) => {
    await onPriorityChange(keyId, priorityValue)
    setEditingPriority(null)
  }

  const handlePriorityCancel = () => {
    setEditingPriority(null)
    setPriorityValue(0)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return '#28a745'
      case 'degraded':
        return '#ffc107'
      case 'disabled':
        return '#dc3545'
      default:
        return '#6c757d'
    }
  }

  const getNextStatus = (currentStatus: string): string => {
    switch (currentStatus) {
      case 'active':
        return 'disabled'
      case 'disabled':
        return 'active'
      case 'degraded':
        return 'active'
      default:
        return 'active'
    }
  }

  if (loading) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <p>Loading API keys...</p>
      </div>
    )
  }

  if (apiKeys.length === 0) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <p style={{ color: '#6c757d' }}>No API keys found</p>
        <p style={{ color: '#6c757d', fontSize: '14px', marginTop: '10px' }}>
          Add your first API key to get started
        </p>
      </div>
    )
  }

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      border: '1px solid #dee2e6',
      overflow: 'hidden'
    }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse'
      }}>
        <thead>
          <tr style={{
            backgroundColor: '#f8f9fa',
            borderBottom: '2px solid #dee2e6'
          }}>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Provider</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Feature</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Key</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Priority</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Status</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Failures</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Last Used</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {apiKeys.map((key) => (
            <tr
              key={key.id}
              style={{
                borderBottom: '1px solid #dee2e6'
              }}
            >
              <td style={{ padding: '12px' }}>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  backgroundColor: '#007bff',
                  color: 'white'
                }}>
                  {key.provider.toUpperCase()}
                </span>
              </td>
              <td style={{ padding: '12px', fontSize: '14px' }}>{key.feature}</td>
              <td style={{ padding: '12px', fontFamily: 'monospace', fontSize: '13px', color: '#6c757d' }}>
                {maskKeyValue(key.key_value)}
              </td>
              <td style={{ padding: '12px' }}>
                {editingPriority === key.id ? (
                  <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                    <input
                      type="number"
                      value={priorityValue}
                      onChange={(e) => setPriorityValue(parseInt(e.target.value) || 0)}
                      style={{
                        width: '60px',
                        padding: '4px 8px',
                        border: '1px solid #ced4da',
                        borderRadius: '4px',
                        fontSize: '13px'
                      }}
                      min="0"
                      max="100"
                    />
                    <button
                      onClick={() => handlePrioritySave(key.id)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      ✓
                    </button>
                    <button
                      onClick={handlePriorityCancel}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                    <span style={{ fontWeight: 'bold' }}>{key.priority}</span>
                    <button
                      onClick={() => handlePriorityEdit(key.id, key.priority)}
                      style={{
                        padding: '2px 6px',
                        backgroundColor: '#6c757d',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '11px'
                      }}
                    >
                      Edit
                    </button>
                  </div>
                )}
              </td>
              <td style={{ padding: '12px' }}>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  backgroundColor: getStatusColor(key.status),
                  color: 'white'
                }}>
                  {key.status.toUpperCase()}
                </span>
              </td>
              <td style={{ padding: '12px' }}>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  backgroundColor: key.failure_count > 0 ? '#dc3545' : '#28a745',
                  color: 'white'
                }}>
                  {key.failure_count}
                </span>
              </td>
              <td style={{ padding: '12px', fontSize: '13px', color: '#6c757d' }}>
                {key.last_used_at ? new Date(key.last_used_at).toLocaleString() : 'Never'}
              </td>
              <td style={{ padding: '12px' }}>
                <div style={{ display: 'flex', gap: '5px' }}>
                  <button
                    onClick={() => onStatusToggle(key.id, getNextStatus(key.status))}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: key.status === 'active' ? '#ffc107' : '#28a745',
                      color: key.status === 'active' ? '#000' : 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px',
                      fontWeight: 'bold'
                    }}
                    title={`Toggle to ${getNextStatus(key.status)}`}
                  >
                    {key.status === 'active' ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => onDeleteKey(key.id)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px',
                      fontWeight: 'bold'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
