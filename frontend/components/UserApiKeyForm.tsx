import { useState, useEffect } from 'react'

interface UserApiKeyFormProps {
  currentKey: string | null
  onSubmit: (key: string) => Promise<void>
  onRemove: () => Promise<void>
}

/**
 * User API Key Form Component
 * Form for managing user's personal API key
 * Requirements: 27.1, 27.5
 */
export default function UserApiKeyForm({ currentKey, onSubmit, onRemove }: UserApiKeyFormProps) {
  const [key, setKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [removing, setRemoving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  /**
   * Validate API key input
   * Requirements: 27.1
   */
  const validateKey = (keyValue: string): string | null => {
    if (!keyValue || keyValue.trim() === '') {
      return 'API key is required'
    }
    if (keyValue.length < 10) {
      return 'API key must be at least 10 characters'
    }
    return null
  }

  /**
   * Mask API key for display
   * Requirements: 27.1
   */
  const maskKey = (keyValue: string): string => {
    if (!keyValue || keyValue.length < 4) {
      return '****'
    }
    return '****' + keyValue.slice(-4)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate key
    const validationError = validateKey(key)
    if (validationError) {
      setError(validationError)
      return
    }

    setSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      await onSubmit(key.trim())
      setSuccess('Personal API key saved successfully')
      setKey('') // Clear input after successful save
      setShowKey(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API key')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRemove = async () => {
    if (!confirm('Are you sure you want to remove your personal API key? You will fall back to shared keys.')) {
      return
    }

    setRemoving(true)
    setError(null)
    setSuccess(null)

    try {
      await onRemove()
      setSuccess('Personal API key removed successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove API key')
    } finally {
      setRemoving(false)
    }
  }

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '24px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ marginTop: 0, marginBottom: '16px' }}>Personal API Key</h3>
      
      <p style={{
        fontSize: '14px',
        color: '#6c757d',
        marginBottom: '20px'
      }}>
        Provide your own API key to use instead of shared keys. Your key will be encrypted and used with priority over shared keys.
      </p>

      {/* Current Key Status */}
      {currentKey && (
        <div style={{
          padding: '12px',
          backgroundColor: '#d4edda',
          color: '#155724',
          borderRadius: '4px',
          marginBottom: '20px',
          fontSize: '14px'
        }}>
          <strong>Current Key:</strong> {maskKey(currentKey)}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderRadius: '4px',
          marginBottom: '20px',
          fontSize: '14px'
        }}>
          {error}
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div style={{
          padding: '12px',
          backgroundColor: '#d4edda',
          color: '#155724',
          borderRadius: '4px',
          marginBottom: '20px',
          fontSize: '14px'
        }}>
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* API Key Input */}
        <div style={{ marginBottom: '20px' }}>
          <label
            htmlFor="user-api-key-input"
            style={{
              display: 'block',
              marginBottom: '8px',
              fontWeight: 'bold',
              fontSize: '14px'
            }}
          >
            {currentKey ? 'Update API Key' : 'Add API Key'}
          </label>
          <div style={{ position: 'relative' }}>
            <input
              id="user-api-key-input"
              type={showKey ? 'text' : 'password'}
              value={key}
              onChange={(e) => setKey(e.target.value)}
              disabled={submitting || removing}
              placeholder="Enter your API key"
              style={{
                width: '100%',
                padding: '10px',
                paddingRight: '80px',
                borderRadius: '4px',
                border: '1px solid #ced4da',
                fontSize: '14px',
                fontFamily: 'monospace'
              }}
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              disabled={submitting || removing}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                padding: '4px 8px',
                backgroundColor: 'transparent',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                color: '#495057'
              }}
            >
              {showKey ? 'Hide' : 'Show'}
            </button>
          </div>
          <p style={{
            fontSize: '12px',
            color: '#6c757d',
            marginTop: '5px',
            marginBottom: 0
          }}>
            Your key will be encrypted before storage and validated before saving
          </p>
        </div>

        {/* Form Actions */}
        <div style={{
          display: 'flex',
          gap: '10px',
          justifyContent: 'flex-start'
        }}>
          <button
            type="submit"
            disabled={submitting || removing || !key}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: (submitting || removing || !key) ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 'bold',
              opacity: (submitting || removing || !key) ? 0.6 : 1
            }}
          >
            {submitting ? 'Saving...' : (currentKey ? 'Update Key' : 'Add Key')}
          </button>

          {currentKey && (
            <button
              type="button"
              onClick={handleRemove}
              disabled={submitting || removing}
              style={{
                padding: '10px 20px',
                backgroundColor: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: (submitting || removing) ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                opacity: (submitting || removing) ? 0.6 : 1
              }}
            >
              {removing ? 'Removing...' : 'Remove Key'}
            </button>
          )}
        </div>
      </form>

      {/* Usage Information */}
      <div style={{
        marginTop: '24px',
        padding: '16px',
        backgroundColor: '#f8f9fa',
        borderRadius: '4px',
        fontSize: '13px',
        color: '#495057'
      }}>
        <h4 style={{ marginTop: 0, marginBottom: '8px', fontSize: '14px' }}>How it works:</h4>
        <ul style={{ marginBottom: 0, paddingLeft: '20px' }}>
          <li>Your personal API key will be used for all your requests</li>
          <li>If your key fails, the system will automatically fall back to shared keys</li>
          <li>Your key is never shared with other users</li>
          <li>You can update or remove your key at any time</li>
        </ul>
      </div>
    </div>
  )
}
