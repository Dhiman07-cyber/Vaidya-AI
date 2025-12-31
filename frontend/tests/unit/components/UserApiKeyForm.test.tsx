import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import UserApiKeyForm from '@/components/UserApiKeyForm'

/**
 * Unit tests for UserApiKeyForm component
 * Requirements: 27.1 - Test UserApiKeyForm validates input and masks key in display
 */
describe('UserApiKeyForm Component', () => {
  const mockOnSubmit = jest.fn()
  const mockOnRemove = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock window.confirm
    global.confirm = jest.fn(() => true)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('renders form with all required elements when no key exists', () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Check form title
      expect(screen.getByRole('heading', { name: 'Personal API Key' })).toBeInTheDocument()

      // Check description
      expect(
        screen.getByText(/Provide your own API key to use instead of shared keys/)
      ).toBeInTheDocument()

      // Check form field
      expect(screen.getByLabelText(/Add API Key/)).toBeInTheDocument()

      // Check submit button
      expect(screen.getByRole('button', { name: 'Add Key' })).toBeInTheDocument()

      // Remove button should not be present
      expect(screen.queryByRole('button', { name: 'Remove Key' })).not.toBeInTheDocument()
    })

    it('renders form with update/remove options when key exists', () => {
      render(
        <UserApiKeyForm
          currentKey="test-key-12345"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Check update label
      expect(screen.getByLabelText(/Update API Key/)).toBeInTheDocument()

      // Check buttons
      expect(screen.getByRole('button', { name: 'Update Key' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Remove Key' })).toBeInTheDocument()
    })

    /**
     * Test that key is masked in display
     * Requirements: 27.1 - Key must be masked in UI
     */
    it('masks current key in display', () => {
      render(
        <UserApiKeyForm
          currentKey="test-key-12345"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Check that key is masked (shows only last 4 characters)
      expect(screen.getByText(/Current Key:/)).toBeInTheDocument()
      expect(screen.getByText(/\*\*\*\*2345/)).toBeInTheDocument()
      
      // Full key should not be visible
      expect(screen.queryByText('test-key-12345')).not.toBeInTheDocument()
    })

    it('renders password input by default', () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const keyInput = screen.getByLabelText(/Add API Key/)
      expect(keyInput).toHaveAttribute('type', 'password')
    })

    it('renders show/hide button for key input', () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      expect(screen.getByRole('button', { name: 'Show' })).toBeInTheDocument()
    })

    it('displays encryption notice', () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      expect(
        screen.getByText(/Your key will be encrypted before storage and validated before saving/)
      ).toBeInTheDocument()
    })

    it('displays usage information', () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      expect(screen.getByText(/How it works:/)).toBeInTheDocument()
      expect(
        screen.getByText(/Your personal API key will be used for all your requests/)
      ).toBeInTheDocument()
      expect(
        screen.getByText(/If your key fails, the system will automatically fall back to shared keys/)
      ).toBeInTheDocument()
    })
  })

  describe('Show/Hide Key Toggle', () => {
    it('toggles key visibility when show button is clicked', () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const keyInput = screen.getByLabelText(/Add API Key/)
      const toggleButton = screen.getByRole('button', { name: 'Show' })

      // Initially password type
      expect(keyInput).toHaveAttribute('type', 'password')

      // Click to show
      fireEvent.click(toggleButton)
      expect(keyInput).toHaveAttribute('type', 'text')
      expect(screen.getByRole('button', { name: 'Hide' })).toBeInTheDocument()

      // Click to hide again
      fireEvent.click(screen.getByRole('button', { name: 'Hide' }))
      expect(keyInput).toHaveAttribute('type', 'password')
      expect(screen.getByRole('button', { name: 'Show' })).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    /**
     * Test that form validates required fields
     * Requirements: 27.1 - Form must validate input before submission
     */
    it('validates that API key is required', async () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Submit button should be disabled when input is empty
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      expect(submitButton).toBeDisabled()
      
      // Clicking disabled button should not call onSubmit
      fireEvent.click(submitButton)
      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    /**
     * Test that form validates API key length
     * Requirements: 27.1 - Form must validate input before submission
     */
    it('validates that API key must be at least 10 characters', async () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Enter short API key
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: 'short' } })

      // Try to submit
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('API key must be at least 10 characters')).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('trims whitespace from API key before validation', async () => {
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Enter API key with whitespace
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: '  validkey123456  ' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith('validkey123456')  // Trimmed
      })
    })

    it('handles empty string API key', async () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Enter empty string
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: '' } })

      // Submit button should be disabled
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      expect(submitButton).toBeDisabled()
      
      // Clicking disabled button should not call onSubmit
      fireEvent.click(submitButton)
      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('handles whitespace-only API key', async () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Enter whitespace only
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: '   ' } })

      // Try to submit
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('API key is required')).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })
  })

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Fill in form
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: 'sk-validkey123456789' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith('sk-validkey123456789')
      })
    })

    it('disables form during submission', async () => {
      mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Fill in form
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      // Check that button is disabled and shows loading text
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Saving...' })).toBeDisabled()
      })
    })

    it('displays success message after successful submission', async () => {
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Fill in and submit form
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Personal API key saved successfully')).toBeInTheDocument()
      })
    })

    it('clears input after successful submission', async () => {
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Fill in and submit form
      const keyInput = screen.getByLabelText(/Add API Key/) as HTMLInputElement
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(keyInput.value).toBe('')
      })
    })

    it('displays error message when submission fails', async () => {
      const errorMessage = 'API key validation failed'
      mockOnSubmit.mockRejectedValue(new Error(errorMessage))

      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Fill in form
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: 'invalidkey123' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })

      // Form should be re-enabled
      expect(screen.getByRole('button', { name: 'Add Key' })).not.toBeDisabled()
    })

    it('clears previous error when resubmitting', async () => {
      mockOnSubmit.mockRejectedValueOnce(new Error('First error'))
      mockOnSubmit.mockResolvedValueOnce(undefined)

      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Fill in form
      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      // First submission (fails)
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument()
      })

      // Second submission (succeeds)
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument()
      })
    })

    it('disables submit button when input is empty', () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      expect(submitButton).toBeDisabled()
    })

    it('enables submit button when input has value', () => {
      render(
        <UserApiKeyForm
          currentKey={null}
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const keyInput = screen.getByLabelText(/Add API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      expect(submitButton).not.toBeDisabled()
    })
  })

  describe('Key Removal', () => {
    it('shows confirmation dialog when remove button is clicked', async () => {
      render(
        <UserApiKeyForm
          currentKey="test-key-12345"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const removeButton = screen.getByRole('button', { name: 'Remove Key' })
      fireEvent.click(removeButton)

      expect(global.confirm).toHaveBeenCalledWith(
        'Are you sure you want to remove your personal API key? You will fall back to shared keys.'
      )
    })

    it('calls onRemove when confirmed', async () => {
      mockOnRemove.mockResolvedValue(undefined)
      global.confirm = jest.fn(() => true)

      render(
        <UserApiKeyForm
          currentKey="test-key-12345"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const removeButton = screen.getByRole('button', { name: 'Remove Key' })
      fireEvent.click(removeButton)

      await waitFor(() => {
        expect(mockOnRemove).toHaveBeenCalled()
      })
    })

    it('does not call onRemove when cancelled', async () => {
      global.confirm = jest.fn(() => false)

      render(
        <UserApiKeyForm
          currentKey="test-key-12345"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const removeButton = screen.getByRole('button', { name: 'Remove Key' })
      fireEvent.click(removeButton)

      await waitFor(() => {
        expect(mockOnRemove).not.toHaveBeenCalled()
      })
    })

    it('displays success message after successful removal', async () => {
      mockOnRemove.mockResolvedValue(undefined)

      render(
        <UserApiKeyForm
          currentKey="test-key-12345"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const removeButton = screen.getByRole('button', { name: 'Remove Key' })
      fireEvent.click(removeButton)

      await waitFor(() => {
        expect(screen.getByText('Personal API key removed successfully')).toBeInTheDocument()
      })
    })

    it('displays error message when removal fails', async () => {
      const errorMessage = 'Failed to remove key'
      mockOnRemove.mockRejectedValue(new Error(errorMessage))

      render(
        <UserApiKeyForm
          currentKey="test-key-12345"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const removeButton = screen.getByRole('button', { name: 'Remove Key' })
      fireEvent.click(removeButton)

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })
    })

    it('disables buttons during removal', async () => {
      mockOnRemove.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(
        <UserApiKeyForm
          currentKey="test-key-12345"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      const removeButton = screen.getByRole('button', { name: 'Remove Key' })
      fireEvent.click(removeButton)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Removing...' })).toBeDisabled()
      })

      // Update button should also be disabled
      expect(screen.getByRole('button', { name: 'Update Key' })).toBeDisabled()
    })
  })

  describe('Key Masking', () => {
    /**
     * Test that keys are properly masked
     * Requirements: 27.1 - Keys must be masked in display
     */
    it('masks short keys correctly', () => {
      render(
        <UserApiKeyForm
          currentKey="abc"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Short keys should show ****
      expect(screen.getByText(/\*\*\*\*/)).toBeInTheDocument()
    })

    it('masks normal keys showing last 4 characters', () => {
      render(
        <UserApiKeyForm
          currentKey="sk-1234567890abcdef"
          onSubmit={mockOnSubmit}
          onRemove={mockOnRemove}
        />
      )

      // Should show ****cdef
      expect(screen.getByText(/\*\*\*\*cdef/)).toBeInTheDocument()
      expect(screen.queryByText('sk-1234567890abcdef')).not.toBeInTheDocument()
    })
  })
})
