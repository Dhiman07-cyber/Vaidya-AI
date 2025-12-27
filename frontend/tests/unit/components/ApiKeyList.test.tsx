import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ApiKeyList, { ApiKey } from '@/components/ApiKeyList'

/**
 * Unit tests for ApiKeyList component
 * Requirements: 14.3 - Test ApiKeyList masks key values
 */
describe('ApiKeyList Component', () => {
  const mockApiKeys: ApiKey[] = [
    {
      id: 'key-1',
      provider: 'gemini',
      feature: 'chat',
      key_value: 'AIzaSyEncryptedKey123456789',
      priority: 10,
      status: 'active',
      failure_count: 0,
      last_used_at: '2024-01-01T12:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'key-2',
      provider: 'openai',
      feature: 'flashcard',
      key_value: 'sk-EncryptedOpenAIKey987654321',
      priority: 5,
      status: 'degraded',
      failure_count: 3,
      last_used_at: '2024-01-02T10:00:00Z',
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
    {
      id: 'key-3',
      provider: 'ollama',
      feature: 'mcq',
      key_value: 'ollama-key-abc123',
      priority: 0,
      status: 'disabled',
      failure_count: 10,
      last_used_at: null,
      created_at: '2024-01-03T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    },
  ]

  const mockOnStatusToggle = jest.fn()
  const mockOnDeleteKey = jest.fn()
  const mockOnPriorityChange = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders API keys correctly with all required information', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Check that providers are rendered
      expect(screen.getByText('GEMINI')).toBeInTheDocument()
      expect(screen.getByText('OPENAI')).toBeInTheDocument()
      expect(screen.getByText('OLLAMA')).toBeInTheDocument()

      // Check that features are rendered
      expect(screen.getByText('chat')).toBeInTheDocument()
      expect(screen.getByText('flashcard')).toBeInTheDocument()
      expect(screen.getByText('mcq')).toBeInTheDocument()
    })

    /**
     * Test that API key values are masked
     * Requirements: 14.3 - API keys must be masked in UI (show only last 4 characters)
     */
    it('masks API key values to show only last 4 characters', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Check that keys are masked with **** prefix and last 4 chars
      expect(screen.getByText('****6789')).toBeInTheDocument()  // AIzaSyEncryptedKey123456789
      expect(screen.getByText('****4321')).toBeInTheDocument()  // sk-EncryptedOpenAIKey987654321
      expect(screen.getByText('****c123')).toBeInTheDocument()  // ollama-key-abc123

      // Ensure full keys are NOT displayed
      expect(screen.queryByText('AIzaSyEncryptedKey123456789')).not.toBeInTheDocument()
      expect(screen.queryByText('sk-EncryptedOpenAIKey987654321')).not.toBeInTheDocument()
      expect(screen.queryByText('ollama-key-abc123')).not.toBeInTheDocument()
    })

    it('renders priority values correctly', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Check priority values
      expect(screen.getByText('10')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('0')).toBeInTheDocument()
    })

    it('renders status badges correctly', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Check status badges
      expect(screen.getByText('ACTIVE')).toBeInTheDocument()
      expect(screen.getByText('DEGRADED')).toBeInTheDocument()
      expect(screen.getByText('DISABLED')).toBeInTheDocument()
    })

    it('renders failure counts correctly', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Check failure counts (displayed as badges)
      const failureBadges = screen.getAllByText(/^(0|3|10)$/)
      expect(failureBadges).toHaveLength(3)
    })

    it('renders last used timestamps correctly', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Check that timestamps are formatted
      expect(screen.getByText(/1\/1\/2024/)).toBeInTheDocument()
      expect(screen.getByText(/1\/2\/2024/)).toBeInTheDocument()
      expect(screen.getByText('Never')).toBeInTheDocument()  // null last_used_at
    })

    it('renders action buttons for each key', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Check for toggle buttons (Disable/Enable)
      expect(screen.getByRole('button', { name: 'Disable' })).toBeInTheDocument()
      const enableButtons = screen.getAllByRole('button', { name: 'Enable' })
      expect(enableButtons).toHaveLength(2)  // degraded and disabled keys

      // Check for delete buttons
      const deleteButtons = screen.getAllByRole('button', { name: 'Delete' })
      expect(deleteButtons).toHaveLength(3)
    })
  })

  describe('Loading State', () => {
    it('displays loading message when loading is true', () => {
      render(
        <ApiKeyList
          apiKeys={[]}
          loading={true}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      expect(screen.getByText('Loading API keys...')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('displays no keys message when apiKeys array is empty', () => {
      render(
        <ApiKeyList
          apiKeys={[]}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      expect(screen.getByText('No API keys found')).toBeInTheDocument()
      expect(screen.getByText('Add your first API key to get started')).toBeInTheDocument()
    })
  })

  describe('Status Toggle', () => {
    it('triggers status toggle when disable button is clicked', async () => {
      mockOnStatusToggle.mockResolvedValue(undefined)

      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Click disable button for active key
      const disableButton = screen.getByRole('button', { name: 'Disable' })
      fireEvent.click(disableButton)

      await waitFor(() => {
        expect(mockOnStatusToggle).toHaveBeenCalledWith('key-1', 'disabled')
      })
    })

    it('triggers status toggle when enable button is clicked', async () => {
      mockOnStatusToggle.mockResolvedValue(undefined)

      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Click enable button for disabled key
      const enableButtons = screen.getAllByRole('button', { name: 'Enable' })
      fireEvent.click(enableButtons[1])  // disabled key

      await waitFor(() => {
        expect(mockOnStatusToggle).toHaveBeenCalledWith('key-3', 'active')
      })
    })
  })

  describe('Key Deletion', () => {
    it('triggers delete when delete button is clicked', async () => {
      mockOnDeleteKey.mockResolvedValue(undefined)

      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Click delete button for first key
      const deleteButtons = screen.getAllByRole('button', { name: 'Delete' })
      fireEvent.click(deleteButtons[0])

      await waitFor(() => {
        expect(mockOnDeleteKey).toHaveBeenCalledWith('key-1')
      })
    })
  })

  describe('Priority Editing', () => {
    it('shows priority edit controls when edit button is clicked', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Click edit button for first key
      const editButtons = screen.getAllByRole('button', { name: 'Edit' })
      fireEvent.click(editButtons[0])

      // Check that input and save/cancel buttons appear
      expect(screen.getByDisplayValue('10')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '✓' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '✕' })).toBeInTheDocument()
    })

    it('triggers priority change when save button is clicked', async () => {
      mockOnPriorityChange.mockResolvedValue(undefined)

      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Click edit button
      const editButtons = screen.getAllByRole('button', { name: 'Edit' })
      fireEvent.click(editButtons[0])

      // Change priority value
      const input = screen.getByDisplayValue('10')
      fireEvent.change(input, { target: { value: '20' } })

      // Click save button
      const saveButton = screen.getByRole('button', { name: '✓' })
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockOnPriorityChange).toHaveBeenCalledWith('key-1', 20)
      })
    })

    it('cancels priority edit when cancel button is clicked', () => {
      render(
        <ApiKeyList
          apiKeys={mockApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Click edit button
      const editButtons = screen.getAllByRole('button', { name: 'Edit' })
      fireEvent.click(editButtons[0])

      // Change priority value
      const input = screen.getByDisplayValue('10')
      fireEvent.change(input, { target: { value: '20' } })

      // Click cancel button
      const cancelButton = screen.getByRole('button', { name: '✕' })
      fireEvent.click(cancelButton)

      // Edit controls should be hidden
      expect(screen.queryByDisplayValue('20')).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: '✓' })).not.toBeInTheDocument()

      // Priority change should not be called
      expect(mockOnPriorityChange).not.toHaveBeenCalled()
    })
  })

  describe('Edge Cases', () => {
    it('handles short key values correctly', () => {
      const shortKeyApiKeys: ApiKey[] = [
        {
          ...mockApiKeys[0],
          key_value: 'abc',  // Less than 4 characters
        },
      ]

      render(
        <ApiKeyList
          apiKeys={shortKeyApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Should display **** for short keys
      expect(screen.getByText('****')).toBeInTheDocument()
    })

    it('handles empty key value correctly', () => {
      const emptyKeyApiKeys: ApiKey[] = [
        {
          ...mockApiKeys[0],
          key_value: '',
        },
      ]

      render(
        <ApiKeyList
          apiKeys={emptyKeyApiKeys}
          loading={false}
          onStatusToggle={mockOnStatusToggle}
          onDeleteKey={mockOnDeleteKey}
          onPriorityChange={mockOnPriorityChange}
        />
      )

      // Should display **** for empty keys
      expect(screen.getByText('****')).toBeInTheDocument()
    })
  })
})
