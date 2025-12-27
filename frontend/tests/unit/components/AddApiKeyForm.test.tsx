import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AddApiKeyForm from '@/components/AddApiKeyForm'

/**
 * Unit tests for AddApiKeyForm component
 * Requirements: 14.2 - Test AddApiKeyForm validates input
 */
describe('AddApiKeyForm Component', () => {
  const mockOnClose = jest.fn()
  const mockOnSubmit = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders form with all required fields', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Check form title
      expect(screen.getByRole('heading', { name: 'Add API Key' })).toBeInTheDocument()

      // Check all form fields
      expect(screen.getByLabelText(/Provider/)).toBeInTheDocument()
      expect(screen.getByLabelText(/Feature/)).toBeInTheDocument()
      expect(screen.getByLabelText(/API Key/)).toBeInTheDocument()
      expect(screen.getByLabelText(/Priority/)).toBeInTheDocument()

      // Check buttons
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Add Key' })).toBeInTheDocument()
    })

    it('renders provider dropdown with options', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      const providerSelect = screen.getByLabelText(/Provider/)
      expect(providerSelect).toBeInTheDocument()

      // Check that default value is gemini
      expect(providerSelect).toHaveValue('gemini')
    })

    it('renders feature dropdown with options', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      const featureSelect = screen.getByLabelText(/Feature/)
      expect(featureSelect).toBeInTheDocument()

      // Check that default value is chat
      expect(featureSelect).toHaveValue('chat')
    })

    it('renders API key input as password field', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      const keyInput = screen.getByLabelText(/API Key/)
      expect(keyInput).toHaveAttribute('type', 'password')
    })

    it('renders priority input with default value 0', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      const priorityInput = screen.getByLabelText(/Priority/)
      expect(priorityInput).toHaveValue(0)
    })

    it('displays encryption and validation notice', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      expect(
        screen.getByText(/The key will be encrypted before storage and validated before saving/)
      ).toBeInTheDocument()
    })

    it('displays priority help text', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      expect(
        screen.getByText(/Higher priority keys are used first/)
      ).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    /**
     * Test that form validates required fields
     * Requirements: 14.2 - Form must validate input before submission
     */
    it('validates that API key is required', async () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Try to submit without entering API key
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('API key is required')).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    /**
     * Test that form validates API key length
     * Requirements: 14.2 - Form must validate input before submission
     */
    it('validates that API key must be at least 10 characters', async () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Enter short API key
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: 'short' } })

      // Try to submit
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('API key must be at least 10 characters')).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    /**
     * Test that form validates priority range
     * Requirements: 14.2 - Form must validate input before submission
     */
    it('validates that priority must be between 0 and 100', async () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Enter valid API key
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      // Enter invalid priority (negative)
      const priorityInput = screen.getByLabelText(/Priority/)
      fireEvent.change(priorityInput, { target: { value: '-1' } })

      // Try to submit
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Priority must be between 0 and 100')).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('validates that priority cannot exceed 100', async () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Enter valid API key
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      // Enter invalid priority (too high)
      const priorityInput = screen.getByLabelText(/Priority/)
      fireEvent.change(priorityInput, { target: { value: '101' } })

      // Try to submit
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Priority must be between 0 and 100')).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('trims whitespace from API key before validation', async () => {
      mockOnSubmit.mockResolvedValue(undefined)

      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Enter API key with whitespace
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: '  validkey123456  ' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          'gemini',
          'chat',
          'validkey123456',  // Trimmed
          0
        )
      })
    })
  })

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      mockOnSubmit.mockResolvedValue(undefined)

      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Fill in form
      const providerSelect = screen.getByLabelText(/Provider/)
      fireEvent.change(providerSelect, { target: { value: 'openai' } })

      const featureSelect = screen.getByLabelText(/Feature/)
      fireEvent.change(featureSelect, { target: { value: 'flashcard' } })

      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: 'sk-validkey123456789' } })

      const priorityInput = screen.getByLabelText(/Priority/)
      fireEvent.change(priorityInput, { target: { value: '50' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          'openai',
          'flashcard',
          'sk-validkey123456789',
          50
        )
      })
    })

    it('disables form during submission', async () => {
      mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Fill in form
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      // Check that button is disabled and shows loading text
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Adding...' })).toBeDisabled()
      })

      // Check that cancel button is also disabled
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled()
    })

    it('displays error message when submission fails', async () => {
      const errorMessage = 'API key validation failed'
      mockOnSubmit.mockRejectedValue(new Error(errorMessage))

      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Fill in form
      const keyInput = screen.getByLabelText(/API Key/)
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

      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Fill in form
      const keyInput = screen.getByLabelText(/API Key/)
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
  })

  describe('Form Cancellation', () => {
    it('calls onClose when cancel button is clicked', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      const cancelButton = screen.getByRole('button', { name: 'Cancel' })
      fireEvent.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalled()
    })

    it('does not call onClose when form is submitting', async () => {
      mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Fill in and submit form
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      // Try to cancel during submission
      const cancelButton = screen.getByRole('button', { name: 'Cancel' })
      fireEvent.click(cancelButton)

      // onClose should not be called
      expect(mockOnClose).not.toHaveBeenCalled()
    })
  })

  describe('Provider and Feature Selection', () => {
    it('allows changing provider', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      const providerSelect = screen.getByLabelText(/Provider/)
      
      // Change to OpenAI
      fireEvent.change(providerSelect, { target: { value: 'openai' } })
      expect(providerSelect).toHaveValue('openai')

      // Change to Ollama
      fireEvent.change(providerSelect, { target: { value: 'ollama' } })
      expect(providerSelect).toHaveValue('ollama')
    })

    it('allows changing feature', () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      const featureSelect = screen.getByLabelText(/Feature/)
      
      // Change to MCQ
      fireEvent.change(featureSelect, { target: { value: 'mcq' } })
      expect(featureSelect).toHaveValue('mcq')

      // Change to Image
      fireEvent.change(featureSelect, { target: { value: 'image' } })
      expect(featureSelect).toHaveValue('image')
    })
  })

  describe('Edge Cases', () => {
    it('handles empty string API key', async () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Enter empty string
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: '' } })

      // Try to submit
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('API key is required')).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('handles whitespace-only API key', async () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Enter whitespace only
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: '   ' } })

      // Try to submit
      const submitButton = screen.getByRole('button', { name: 'Add Key' })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('API key is required')).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('handles non-numeric priority input', async () => {
      render(<AddApiKeyForm onClose={mockOnClose} onSubmit={mockOnSubmit} />)

      // Enter valid API key
      const keyInput = screen.getByLabelText(/API Key/)
      fireEvent.change(keyInput, { target: { value: 'validkey123456' } })

      // Enter non-numeric priority
      const priorityInput = screen.getByLabelText(/Priority/)
      fireEvent.change(priorityInput, { target: { value: 'abc' } })

      // Priority should default to 0
      expect(priorityInput).toHaveValue(0)
    })
  })
})
