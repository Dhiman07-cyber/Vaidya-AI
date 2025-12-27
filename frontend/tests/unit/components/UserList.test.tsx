import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import UserList, { User } from '@/components/UserList'

describe('UserList Component', () => {
  const mockUsers: User[] = [
    {
      id: 'user-1',
      email: 'user1@example.com',
      name: 'User One',
      plan: 'free',
      role: null,
      disabled: false,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'user-2',
      email: 'user2@example.com',
      name: 'User Two',
      plan: 'student',
      role: null,
      disabled: false,
      created_at: '2024-01-02T00:00:00Z',
    },
    {
      id: 'user-3',
      email: 'admin@example.com',
      name: 'Admin User',
      plan: 'admin',
      role: 'admin',
      disabled: false,
      created_at: '2024-01-03T00:00:00Z',
    },
    {
      id: 'user-4',
      email: 'disabled@example.com',
      name: 'Disabled User',
      plan: 'pro',
      role: null,
      disabled: true,
      created_at: '2024-01-04T00:00:00Z',
    },
  ]

  const mockOnPlanChange = jest.fn()
  const mockOnResetUsage = jest.fn()
  const mockOnDisableUser = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders users correctly with all required information', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Check that all users are rendered
      expect(screen.getByText('User One')).toBeInTheDocument()
      expect(screen.getByText('user1@example.com')).toBeInTheDocument()
      expect(screen.getByText('User Two')).toBeInTheDocument()
      expect(screen.getByText('user2@example.com')).toBeInTheDocument()
      expect(screen.getByText('Admin User')).toBeInTheDocument()
      expect(screen.getByText('admin@example.com')).toBeInTheDocument()
      expect(screen.getByText('Disabled User')).toBeInTheDocument()
      expect(screen.getByText('disabled@example.com')).toBeInTheDocument()
    })

    it('renders plan badges correctly', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Check plan badges
      expect(screen.getByText('FREE')).toBeInTheDocument()
      expect(screen.getByText('STUDENT')).toBeInTheDocument()
      expect(screen.getByText('ADMIN')).toBeInTheDocument()
      expect(screen.getByText('PRO')).toBeInTheDocument()
    })

    it('renders status badges correctly', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Check status badges - should have 3 ACTIVE and 1 DISABLED
      const activeStatuses = screen.getAllByText('ACTIVE')
      expect(activeStatuses).toHaveLength(3)
      expect(screen.getByText('DISABLED')).toBeInTheDocument()
    })

    it('renders formatted creation dates', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Check that dates are formatted (exact format depends on locale)
      expect(screen.getByText('1/1/2024')).toBeInTheDocument()
      expect(screen.getByText('2/1/2024')).toBeInTheDocument()
      expect(screen.getByText('3/1/2024')).toBeInTheDocument()
      expect(screen.getByText('4/1/2024')).toBeInTheDocument()
    })

    it('renders manage buttons for each user', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      expect(manageButtons).toHaveLength(4)
    })
  })

  describe('Loading State', () => {
    it('displays loading message when loading is true', () => {
      render(
        <UserList
          users={[]}
          loading={true}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      expect(screen.getByText('Loading users...')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('displays no users message when users array is empty', () => {
      render(
        <UserList
          users={[]}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      expect(screen.getByText('No users found')).toBeInTheDocument()
    })
  })

  describe('User Details Modal', () => {
    it('opens user details modal when manage button is clicked', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[0])

      // Check that modal is opened with user details
      expect(screen.getByRole('heading', { name: 'User Details' })).toBeInTheDocument()
      // Check for user ID which is unique to the modal
      expect(screen.getByText('user-1')).toBeInTheDocument()
    })

    it('closes user details modal when close button is clicked', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Open modal
      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[0])

      // Close modal
      const closeButton = screen.getByRole('button', { name: 'Close' })
      fireEvent.click(closeButton)

      // Modal should be closed
      expect(screen.queryByRole('heading', { name: 'User Details' })).not.toBeInTheDocument()
    })
  })

  describe('Plan Change', () => {
    it('triggers plan change API call when plan is updated', async () => {
      mockOnPlanChange.mockResolvedValue(undefined)

      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Open modal for first user (free plan)
      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[0])

      // Change plan to student
      const planSelect = screen.getByRole('combobox')
      fireEvent.change(planSelect, { target: { value: 'student' } })

      // Click update button
      const updateButton = screen.getByRole('button', { name: 'Update Plan' })
      fireEvent.click(updateButton)

      await waitFor(() => {
        expect(mockOnPlanChange).toHaveBeenCalledWith('user-1', 'student')
      })
    })

    it('does not trigger API call when same plan is selected', async () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Open modal for first user (free plan)
      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[0])

      // Try to update with same plan
      const updateButton = screen.getByRole('button', { name: 'Update Plan' })
      fireEvent.click(updateButton)

      // Should not call API
      expect(mockOnPlanChange).not.toHaveBeenCalled()
    })

    it('disables update button when same plan is selected', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Open modal for first user (free plan)
      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[0])

      // Update button should be disabled initially (same plan)
      const updateButton = screen.getByRole('button', { name: 'Update Plan' })
      expect(updateButton).toBeDisabled()
    })

    it('enables update button when different plan is selected', () => {
      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Open modal for first user (free plan)
      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[0])

      // Change plan to student
      const planSelect = screen.getByRole('combobox')
      fireEvent.change(planSelect, { target: { value: 'student' } })

      // Update button should be enabled
      const updateButton = screen.getByRole('button', { name: 'Update Plan' })
      expect(updateButton).not.toBeDisabled()
    })
  })

  describe('Usage Reset', () => {
    it('triggers usage reset API call when reset button is clicked', async () => {
      mockOnResetUsage.mockResolvedValue(undefined)

      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Open modal
      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[0])

      // Click reset usage button
      const resetButton = screen.getByRole('button', { name: 'Reset Usage' })
      fireEvent.click(resetButton)

      await waitFor(() => {
        expect(mockOnResetUsage).toHaveBeenCalledWith('user-1')
      })
    })
  })

  describe('User Disable/Enable', () => {
    it('triggers disable API call for active user', async () => {
      mockOnDisableUser.mockResolvedValue(undefined)

      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Open modal for active user
      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[0])

      // Click disable button
      const disableButton = screen.getByRole('button', { name: 'Disable User' })
      fireEvent.click(disableButton)

      await waitFor(() => {
        expect(mockOnDisableUser).toHaveBeenCalledWith('user-1', true)
      })
    })

    it('triggers enable API call for disabled user', async () => {
      mockOnDisableUser.mockResolvedValue(undefined)

      render(
        <UserList
          users={mockUsers}
          loading={false}
          onPlanChange={mockOnPlanChange}
          onResetUsage={mockOnResetUsage}
          onDisableUser={mockOnDisableUser}
        />
      )

      // Open modal for disabled user (last user)
      const manageButtons = screen.getAllByRole('button', { name: 'Manage' })
      fireEvent.click(manageButtons[3])

      // Click enable button
      const enableButton = screen.getByRole('button', { name: 'Enable User' })
      fireEvent.click(enableButton)

      await waitFor(() => {
        expect(mockOnDisableUser).toHaveBeenCalledWith('user-4', false)
      })
    })
  })
})
