import { useState } from 'react'

export interface Document {
  id: string
  user_id: string
  filename: string
  file_type: string
  file_size: number
  storage_path: string
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
}

interface DocumentListProps {
  documents: Document[]
  onDelete: (documentId: string) => Promise<void>
  loading?: boolean
}

/**
 * DocumentList Component
 * Displays user documents with processing status and delete functionality
 * Requirements: 7.1
 */
export default function DocumentList({ documents, onDelete, loading }: DocumentListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return '#28a745'
      case 'processing':
        return '#ffc107'
      case 'pending':
        return '#17a2b8'
      case 'failed':
        return '#dc3545'
      default:
        return '#6c757d'
    }
  }

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'Ready'
      case 'processing':
        return 'Processing...'
      case 'pending':
        return 'Pending'
      case 'failed':
        return 'Failed'
      default:
        return status
    }
  }

  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
      return
    }

    setDeletingId(documentId)
    try {
      await onDelete(documentId)
    } catch (error) {
      // Error handling is done in parent component
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return (
      <div
        data-testid="document-list-loading"
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center',
          color: '#6c757d'
        }}
      >
        Loading documents...
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div
        data-testid="document-list-empty"
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center',
          color: '#6c757d'
        }}
      >
        <p style={{ margin: 0 }}>No documents uploaded yet.</p>
        <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
          Upload a PDF or image to get started.
        </p>
      </div>
    )
  }

  return (
    <div
      data-testid="document-list"
      style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}
    >
      <h2 style={{ marginTop: 0, marginBottom: '16px', fontSize: '20px' }}>
        My Documents ({documents.length})
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {documents.map((doc) => (
          <div
            key={doc.id}
            data-testid={`document-${doc.id}`}
            data-status={doc.processing_status}
            style={{
              border: '1px solid #dee2e6',
              borderRadius: '6px',
              padding: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '16px',
              backgroundColor: '#f8f9fa'
            }}
          >
            {/* Document Info */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: '16px',
                fontWeight: '500',
                color: '#212529',
                marginBottom: '4px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {doc.filename}
              </div>
              <div style={{
                fontSize: '13px',
                color: '#6c757d',
                display: 'flex',
                gap: '12px',
                flexWrap: 'wrap'
              }}>
                <span>{doc.file_type.toUpperCase()}</span>
                <span>•</span>
                <span>{formatFileSize(doc.file_size)}</span>
                <span>•</span>
                <span>{formatDate(doc.created_at)}</span>
              </div>
            </div>

            {/* Status Badge */}
            <div
              data-testid={`status-${doc.id}`}
              style={{
                padding: '6px 12px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: '500',
                color: 'white',
                backgroundColor: getStatusColor(doc.processing_status),
                whiteSpace: 'nowrap'
              }}
            >
              {getStatusLabel(doc.processing_status)}
            </div>

            {/* Delete Button */}
            <button
              onClick={() => handleDelete(doc.id)}
              disabled={deletingId === doc.id}
              data-testid={`delete-${doc.id}`}
              style={{
                padding: '8px 16px',
                backgroundColor: deletingId === doc.id ? '#6c757d' : '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: deletingId === doc.id ? 'not-allowed' : 'pointer',
                fontSize: '13px',
                fontWeight: '500',
                whiteSpace: 'nowrap'
              }}
            >
              {deletingId === doc.id ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
