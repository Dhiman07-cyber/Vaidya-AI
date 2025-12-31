import { useState, useRef } from 'react'

interface DocumentUploadProps {
  onUploadSuccess: () => void
  onUploadError: (error: string) => void
}

/**
 * DocumentUpload Component
 * Handles file upload with progress tracking
 * Requirements: 7.1
 */
export default function DocumentUpload({ onUploadSuccess, onUploadError }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Validate file type
      const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp']
      if (!validTypes.includes(file.type)) {
        onUploadError('Invalid file type. Please upload a PDF or image file.')
        return
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        onUploadError('File too large. Maximum size is 10MB.')
        return
      }

      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      onUploadError('Please select a file first')
      return
    }

    setUploading(true)
    setProgress(0)

    try {
      // Get auth token from Supabase
      const { createClient } = await import('@supabase/supabase-js')
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
      const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
      const supabase = createClient(supabaseUrl, supabaseAnonKey)
      
      const session = await supabase.auth.getSession()
      const token = session.data.session?.access_token

      if (!token) {
        throw new Error('Not authenticated')
      }

      // Create form data
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Upload with progress tracking
      const xhr = new XMLHttpRequest()

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100
          setProgress(Math.round(percentComplete))
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status === 201) {
          setSelectedFile(null)
          if (fileInputRef.current) {
            fileInputRef.current.value = ''
          }
          onUploadSuccess()
        } else {
          const response = JSON.parse(xhr.responseText)
          const errorMessage = response.detail?.error?.message || 'Upload failed'
          onUploadError(errorMessage)
        }
        setUploading(false)
        setProgress(0)
      })

      xhr.addEventListener('error', () => {
        onUploadError('Network error during upload')
        setUploading(false)
        setProgress(0)
      })

      xhr.open('POST', `${process.env.NEXT_PUBLIC_API_URL}/api/documents`)
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      xhr.send(formData)
    } catch (error: any) {
      onUploadError(error.message || 'Upload failed')
      setUploading(false)
      setProgress(0)
    }
  }

  const handleCancel = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div
      data-testid="document-upload"
      style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}
    >
      <h2 style={{ marginTop: 0, marginBottom: '16px', fontSize: '20px' }}>
        Upload Document
      </h2>

      <div style={{ marginBottom: '16px' }}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,image/*"
          onChange={handleFileSelect}
          disabled={uploading}
          data-testid="file-input"
          style={{
            display: 'block',
            width: '100%',
            padding: '8px',
            border: '1px solid #ced4da',
            borderRadius: '4px',
            fontSize: '14px',
            cursor: uploading ? 'not-allowed' : 'pointer'
          }}
        />
        <div style={{
          fontSize: '12px',
          color: '#6c757d',
          marginTop: '8px'
        }}>
          Supported formats: PDF, JPG, PNG, GIF, BMP (max 10MB)
        </div>
      </div>

      {selectedFile && !uploading && (
        <div style={{
          padding: '12px',
          backgroundColor: '#e7f3ff',
          borderRadius: '4px',
          marginBottom: '16px',
          fontSize: '14px'
        }}>
          <strong>Selected:</strong> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
        </div>
      )}

      {uploading && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{
            fontSize: '14px',
            color: '#495057',
            marginBottom: '8px'
          }}>
            Uploading... {progress}%
          </div>
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#e9ecef',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div
              data-testid="progress-bar"
              style={{
                width: `${progress}%`,
                height: '100%',
                backgroundColor: '#007bff',
                transition: 'width 0.3s ease'
              }}
            />
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '12px' }}>
        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          data-testid="upload-button"
          style={{
            padding: '10px 20px',
            backgroundColor: selectedFile && !uploading ? '#28a745' : '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: selectedFile && !uploading ? 'pointer' : 'not-allowed',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>

        {selectedFile && !uploading && (
          <button
            onClick={handleCancel}
            data-testid="cancel-button"
            style={{
              padding: '10px 20px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}
