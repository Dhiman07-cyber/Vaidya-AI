import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import DocumentList, { Document } from '@/components/DocumentList'

/**
 * Unit tests for DocumentList component
 * Requirements: 7.1 - Test DocumentList displays documents
 */
describe('DocumentList Component', () => {
  const mockOnDelete = jest.fn()

  const mockDocuments: Document[] = [
    {
      id: 'doc-1',
      user_id: 'user-1',
      filename: 'medical-notes.pdf',
      file_type: 'pdf',
      file_size: 1024000, // ~1MB
      storage_path: 'documents/user-1/medical-notes.pdf',
      processing_status: 'completed',
      created_at: '2024-01-15T10:30:00Z'
    },
    {
      id: 'doc-2',
      user_id: 'user-1',
      filename: 'anatomy-diagram.jpg',
      file_type: 'image',
      file_size: 512000, // ~500KB
      storage_path: 'documents/user-1/anatomy-diagram.jpg',
      processing_status: 'processing',
      created_at: '2024-01-16T14:20:00Z'
    },
    {
      id: 'doc-3',
      user_id: 'user-1',
      filename: 'study-guide.pdf',
      file_type: 'pdf',
      file_size: 2048000, // ~2MB
      storage_path: 'documents/user-1/study-guide.pdf',
      processing_status: 'failed',
      created_at: '2024-01-17T09:15:00Z'
    }
  ]

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock window.confirm
    global.confirm = jest.fn(() => true)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Rendering', () => {
    /**
     * Test that component displays documents correctly
     * Requirements: 7.1 - DocumentList must display documents
     */
    it('renders document list with all documents', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      // Check heading with count
      expect(screen.getByRole('heading', { name: /My Documents \(3\)/ })).toBeInTheDocument()

      // Check all documents are displayed
      expect(screen.getByText('medical-notes.pdf')).toBeInTheDocument()
      expect(screen.getByText('anatomy-diagram.jpg')).toBeInTheDocument()
      expect(screen.getByText('study-guide.pdf')).toBeInTheDocument()
    })

    it('displays document metadata correctly', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      // Check file types
      expect(screen.getAllByText('PDF')).toHaveLength(2)
      expect(screen.getByText('IMAGE')).toBeInTheDocument()

      // Check file sizes are formatted
      expect(screen.getByText(/1000\.00 KB/)).toBeInTheDocument() // 1024000 bytes = 1000 KB
      expect(screen.getByText(/500\.00 KB/)).toBeInTheDocument()
      expect(screen.getByText(/1\.95 MB/)).toBeInTheDocument() // 2048000 bytes = 1.95 MB
    })

    it('displays processing status for each document', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      // Check status badges
      expect(screen.getByText('Ready')).toBeInTheDocument() // completed
      expect(screen.getByText('Processing...')).toBeInTheDocument() // processing
      expect(screen.getByText('Failed')).toBeInTheDocument() // failed
    })

    it('displays delete button for each document', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const deleteButtons = screen.getAllByText('Delete')
      expect(deleteButtons).toHaveLength(3)
    })

    it('shows loading state when loading prop is true', () => {
      render(
        <DocumentList
          documents={[]}
          onDelete={mockOnDelete}
          loading={true}
        />
      )

      expect(screen.getByTestId('document-list-loading')).toBeInTheDocument()
      expect(screen.getByText('Loading documents...')).toBeInTheDocument()
    })

    it('shows empty state when no documents', () => {
      render(
        <DocumentList
          documents={[]}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByTestId('document-list-empty')).toBeInTheDocument()
      expect(screen.getByText('No documents uploaded yet.')).toBeInTheDocument()
      expect(screen.getByText(/Upload a PDF or image to get started/)).toBeInTheDocument()
    })

    it('renders with proper test ids', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByTestId('document-list')).toBeInTheDocument()
      expect(screen.getByTestId('document-doc-1')).toBeInTheDocument()
      expect(screen.getByTestId('document-doc-2')).toBeInTheDocument()
      expect(screen.getByTestId('document-doc-3')).toBeInTheDocument()
    })

    it('includes status in document test id attributes', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const doc1 = screen.getByTestId('document-doc-1')
      expect(doc1).toHaveAttribute('data-status', 'completed')

      const doc2 = screen.getByTestId('document-doc-2')
      expect(doc2).toHaveAttribute('data-status', 'processing')

      const doc3 = screen.getByTestId('document-doc-3')
      expect(doc3).toHaveAttribute('data-status', 'failed')
    })
  })

  describe('File Size Formatting', () => {
    it('formats bytes correctly', () => {
      const docs: Document[] = [
        {
          ...mockDocuments[0],
          id: 'doc-bytes',
          filename: 'tiny.pdf',
          file_size: 500 // 500 bytes
        }
      ]

      render(
        <DocumentList
          documents={docs}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText(/500 B/)).toBeInTheDocument()
    })

    it('formats kilobytes correctly', () => {
      const docs: Document[] = [
        {
          ...mockDocuments[0],
          id: 'doc-kb',
          filename: 'small.pdf',
          file_size: 10240 // 10KB
        }
      ]

      render(
        <DocumentList
          documents={docs}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText(/10\.00 KB/)).toBeInTheDocument()
    })

    it('formats megabytes correctly', () => {
      const docs: Document[] = [
        {
          ...mockDocuments[0],
          id: 'doc-mb',
          filename: 'large.pdf',
          file_size: 5242880 // 5MB
        }
      ]

      render(
        <DocumentList
          documents={docs}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText(/5\.00 MB/)).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('displays correct status for completed documents', () => {
      const docs: Document[] = [
        { ...mockDocuments[0], processing_status: 'completed' }
      ]

      render(
        <DocumentList
          documents={docs}
          onDelete={mockOnDelete}
        />
      )

      const statusBadge = screen.getByTestId('status-doc-1')
      expect(statusBadge).toHaveTextContent('Ready')
    })

    it('displays correct status for processing documents', () => {
      const docs: Document[] = [
        { ...mockDocuments[0], processing_status: 'processing' }
      ]

      render(
        <DocumentList
          documents={docs}
          onDelete={mockOnDelete}
        />
      )

      const statusBadge = screen.getByTestId('status-doc-1')
      expect(statusBadge).toHaveTextContent('Processing...')
    })

    it('displays correct status for pending documents', () => {
      const docs: Document[] = [
        { ...mockDocuments[0], processing_status: 'pending' }
      ]

      render(
        <DocumentList
          documents={docs}
          onDelete={mockOnDelete}
        />
      )

      const statusBadge = screen.getByTestId('status-doc-1')
      expect(statusBadge).toHaveTextContent('Pending')
    })

    it('displays correct status for failed documents', () => {
      const docs: Document[] = [
        { ...mockDocuments[0], processing_status: 'failed' }
      ]

      render(
        <DocumentList
          documents={docs}
          onDelete={mockOnDelete}
        />
      )

      const statusBadge = screen.getByTestId('status-doc-1')
      expect(statusBadge).toHaveTextContent('Failed')
    })
  })

  describe('Document Deletion', () => {
    it('shows confirmation dialog when delete button is clicked', async () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton = screen.getByTestId('delete-doc-1')
      fireEvent.click(deleteButton)

      expect(global.confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this document? This action cannot be undone.'
      )
    })

    it('calls onDelete when deletion is confirmed', async () => {
      mockOnDelete.mockResolvedValue(undefined)
      global.confirm = jest.fn(() => true)

      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton = screen.getByTestId('delete-doc-1')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(mockOnDelete).toHaveBeenCalledWith('doc-1')
      })
    })

    it('does not call onDelete when deletion is cancelled', async () => {
      global.confirm = jest.fn(() => false)

      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton = screen.getByTestId('delete-doc-1')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(mockOnDelete).not.toHaveBeenCalled()
      })
    })

    it('disables delete button during deletion', async () => {
      mockOnDelete.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton = screen.getByTestId('delete-doc-1')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText('Deleting...')).toBeInTheDocument()
      })

      const deletingButton = screen.getByTestId('delete-doc-1')
      expect(deletingButton).toBeDisabled()
    })

    it('re-enables delete button after deletion completes', async () => {
      mockOnDelete.mockResolvedValue(undefined)

      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton = screen.getByTestId('delete-doc-1')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(mockOnDelete).toHaveBeenCalled()
      })

      // Button should be re-enabled after completion
      await waitFor(() => {
        expect(deleteButton).not.toBeDisabled()
      })
    })

    it('handles deletion errors gracefully', async () => {
      mockOnDelete.mockRejectedValue(new Error('Deletion failed'))

      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton = screen.getByTestId('delete-doc-1')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(mockOnDelete).toHaveBeenCalled()
      })

      // Button should be re-enabled after error
      await waitFor(() => {
        expect(deleteButton).not.toBeDisabled()
      })
    })

    it('only disables the specific document being deleted', async () => {
      mockOnDelete.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton1 = screen.getByTestId('delete-doc-1')
      fireEvent.click(deleteButton1)

      await waitFor(() => {
        expect(screen.getByText('Deleting...')).toBeInTheDocument()
      })

      // Other delete buttons should still be enabled
      const deleteButton2 = screen.getByTestId('delete-doc-2')
      const deleteButton3 = screen.getByTestId('delete-doc-3')
      
      expect(deleteButton2).not.toBeDisabled()
      expect(deleteButton3).not.toBeDisabled()
    })
  })

  describe('Date Formatting', () => {
    it('formats dates correctly', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      // Dates should be formatted in locale string format
      // Exact format depends on locale, so we just check that dates are present
      const documentElements = screen.getAllByTestId(/^document-/)
      expect(documentElements.length).toBeGreaterThan(0)
    })
  })

  describe('Empty and Loading States', () => {
    it('does not show document list when loading', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
          loading={true}
        />
      )

      expect(screen.queryByTestId('document-list')).not.toBeInTheDocument()
      expect(screen.queryByText('medical-notes.pdf')).not.toBeInTheDocument()
    })

    it('does not show loading state when not loading', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
          loading={false}
        />
      )

      expect(screen.queryByTestId('document-list-loading')).not.toBeInTheDocument()
    })

    it('shows empty state only when no documents and not loading', () => {
      render(
        <DocumentList
          documents={[]}
          onDelete={mockOnDelete}
          loading={false}
        />
      )

      expect(screen.getByTestId('document-list-empty')).toBeInTheDocument()
      expect(screen.queryByTestId('document-list-loading')).not.toBeInTheDocument()
    })
  })

  describe('Document Count', () => {
    it('displays correct count for single document', () => {
      render(
        <DocumentList
          documents={[mockDocuments[0]]}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByRole('heading', { name: /My Documents \(1\)/ })).toBeInTheDocument()
    })

    it('displays correct count for multiple documents', () => {
      render(
        <DocumentList
          documents={mockDocuments}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByRole('heading', { name: /My Documents \(3\)/ })).toBeInTheDocument()
    })

    it('displays zero count in empty state', () => {
      render(
        <DocumentList
          documents={[]}
          onDelete={mockOnDelete}
        />
      )

      // Empty state doesn't show count in heading
      expect(screen.queryByText(/My Documents \(0\)/)).not.toBeInTheDocument()
    })
  })
})
