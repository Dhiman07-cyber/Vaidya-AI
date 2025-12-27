import { render, screen, fireEvent } from '@testing-library/react'
import AuditLogTable, { AuditLog } from '@/components/AuditLogTable'

describe('AuditLogTable Component', () => {
  const mockLogs: AuditLog[] = [
    {
      id: 'log-1',
      admin_id: 'admin-123-456-789',
      action_type: 'update_plan',
      target_type: 'user',
      target_id: 'user-abc-def-ghi',
      details: { old_plan: 'free', new_plan: 'student' },
      timestamp: '2024-01-01T10:00:00Z',
    },
    {
      id: 'log-2',
      admin_id: 'admin-987-654-321',
      action_type: 'reset_usage',
      target_type: 'user',
      target_id: 'user-xyz-123-456',
      details: null,
      timestamp: '2024-01-02T11:30:00Z',
    },
    {
      id: 'log-3',
      admin_id: 'admin-111-222-333',
      action_type: 'add_api_key',
      target_type: 'api_key',
      target_id: 'key-aaa-bbb-ccc',
      details: { provider: 'gemini', feature: 'chat' },
      timestamp: '2024-01-03T14:15:00Z',
    },
    {
      id: 'log-4',
      admin_id: 'admin-444-555-666',
      action_type: 'disable_user',
      target_type: 'user',
      target_id: 'user-ddd-eee-fff',
      details: { reason: 'policy violation' },
      timestamp: '2024-01-04T16:45:00Z',
    },
  ]

  describe('Rendering', () => {
    it('renders audit logs correctly with all required columns', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Check table headers
      expect(screen.getByText('Timestamp')).toBeInTheDocument()
      expect(screen.getByText('Admin ID')).toBeInTheDocument()
      expect(screen.getByText('Action')).toBeInTheDocument()
      expect(screen.getByText('Target Type')).toBeInTheDocument()
      expect(screen.getByText('Target ID')).toBeInTheDocument()

      // Check that logs are rendered
      expect(screen.getByText('UPDATE PLAN')).toBeInTheDocument()
      expect(screen.getByText('RESET USAGE')).toBeInTheDocument()
      expect(screen.getByText('ADD API KEY')).toBeInTheDocument()
      expect(screen.getByText('DISABLE USER')).toBeInTheDocument()
    })

    it('renders truncated admin IDs', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Admin IDs should be truncated to first 8 characters
      expect(screen.getByText('admin-12...')).toBeInTheDocument()
      expect(screen.getByText('admin-98...')).toBeInTheDocument()
    })

    it('renders truncated target IDs', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Target IDs should be truncated to first 12 characters
      expect(screen.getByText('user-abc-def...')).toBeInTheDocument()
      expect(screen.getByText('user-xyz-123...')).toBeInTheDocument()
    })

    it('renders target types as badges', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      const userBadges = screen.getAllByText('user')
      expect(userBadges.length).toBeGreaterThan(0)
      
      expect(screen.getByText('api_key')).toBeInTheDocument()
    })

    it('renders formatted timestamps', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Timestamps should be formatted (exact format depends on locale)
      // Just check that some date-like text is present
      const timestamps = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/)
      expect(timestamps.length).toBeGreaterThan(0)
    })

    it('renders log count summary', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      expect(screen.getByText('Showing 4 logs')).toBeInTheDocument()
    })

    it('renders singular log count when only one log', () => {
      render(<AuditLogTable logs={[mockLogs[0]]} loading={false} />)

      expect(screen.getByText('Showing 1 log')).toBeInTheDocument()
    })
  })

  describe('Action Type Colors', () => {
    it('applies correct color for delete/disable actions', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      const disableAction = screen.getByText('DISABLE USER')
      expect(disableAction).toHaveStyle({ backgroundColor: '#dc3545' })
    })

    it('applies correct color for add/enable/create actions', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      const addAction = screen.getByText('ADD API KEY')
      expect(addAction).toHaveStyle({ backgroundColor: '#28a745' })
    })

    it('applies correct color for update/reset actions', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      const updateAction = screen.getByText('UPDATE PLAN')
      expect(updateAction).toHaveStyle({ backgroundColor: '#ffc107' })

      const resetAction = screen.getByText('RESET USAGE')
      expect(resetAction).toHaveStyle({ backgroundColor: '#ffc107' })
    })
  })

  describe('Loading State', () => {
    it('displays loading message when loading is true', () => {
      render(<AuditLogTable logs={[]} loading={true} />)

      expect(screen.getByText('Loading audit logs...')).toBeInTheDocument()
    })

    it('does not display table when loading', () => {
      render(<AuditLogTable logs={mockLogs} loading={true} />)

      expect(screen.queryByText('Timestamp')).not.toBeInTheDocument()
      expect(screen.queryByText('UPDATE PLAN')).not.toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('displays no logs message when logs array is empty', () => {
      render(<AuditLogTable logs={[]} loading={false} />)

      expect(screen.getByText('No audit logs found')).toBeInTheDocument()
    })

    it('does not display table when no logs', () => {
      render(<AuditLogTable logs={[]} loading={false} />)

      expect(screen.queryByText('Timestamp')).not.toBeInTheDocument()
    })
  })

  describe('Expandable Details', () => {
    it('expands log details when row is clicked', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Initially, details should not be visible
      expect(screen.queryByText('Log Details')).not.toBeInTheDocument()

      // Click on first log row
      const firstRow = screen.getByText('UPDATE PLAN').closest('tr')
      fireEvent.click(firstRow!)

      // Details should now be visible
      expect(screen.getByText('Log Details')).toBeInTheDocument()
      expect(screen.getByText('log-1')).toBeInTheDocument()
      expect(screen.getByText('admin-123-456-789')).toBeInTheDocument()
    })

    it('collapses log details when row is clicked again', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Click to expand
      const firstRow = screen.getByText('UPDATE PLAN').closest('tr')
      fireEvent.click(firstRow!)
      expect(screen.getByText('Log Details')).toBeInTheDocument()

      // Click again to collapse
      fireEvent.click(firstRow!)
      expect(screen.queryByText('Log Details')).not.toBeInTheDocument()
    })

    it('displays additional details when present', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Expand first log which has details
      const firstRow = screen.getByText('UPDATE PLAN').closest('tr')
      fireEvent.click(firstRow!)

      // Check for additional details section
      expect(screen.getByText('Additional Details:')).toBeInTheDocument()
      expect(screen.getByText(/"old_plan"/)).toBeInTheDocument()
      expect(screen.getByText(/"new_plan"/)).toBeInTheDocument()
    })

    it('does not display additional details section when details is null', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Expand second log which has null details
      const secondRow = screen.getByText('RESET USAGE').closest('tr')
      fireEvent.click(secondRow!)

      // Additional details section should not be present
      expect(screen.queryByText('Additional Details:')).not.toBeInTheDocument()
    })

    it('shows expand arrow when collapsed', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      const expandArrows = screen.getAllByText('▶')
      expect(expandArrows.length).toBe(4) // All 4 logs should show expand arrow
    })

    it('shows collapse arrow when expanded', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Expand first log
      const firstRow = screen.getByText('UPDATE PLAN').closest('tr')
      fireEvent.click(firstRow!)

      // Should show collapse arrow for expanded log
      expect(screen.getByText('▼')).toBeInTheDocument()
      
      // Other logs should still show expand arrow
      const expandArrows = screen.getAllByText('▶')
      expect(expandArrows.length).toBe(3)
    })

    it('only expands one log at a time', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Expand first log
      const firstRow = screen.getByText('UPDATE PLAN').closest('tr')
      fireEvent.click(firstRow!)
      expect(screen.getByText('log-1')).toBeInTheDocument()

      // Expand second log
      const secondRow = screen.getByText('RESET USAGE').closest('tr')
      fireEvent.click(secondRow!)
      
      // First log should be collapsed, second should be expanded
      expect(screen.queryByText('log-1')).not.toBeInTheDocument()
      expect(screen.getByText('log-2')).toBeInTheDocument()
    })
  })

  describe('Action Type Formatting', () => {
    it('replaces underscores with spaces in action types', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Action types should have underscores replaced with spaces
      expect(screen.getByText('UPDATE PLAN')).toBeInTheDocument()
      expect(screen.getByText('RESET USAGE')).toBeInTheDocument()
      expect(screen.getByText('ADD API KEY')).toBeInTheDocument()
      expect(screen.getByText('DISABLE USER')).toBeInTheDocument()
    })

    it('converts action types to uppercase', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // All action types should be uppercase
      expect(screen.queryByText('update_plan')).not.toBeInTheDocument()
      expect(screen.getByText('UPDATE PLAN')).toBeInTheDocument()
    })
  })

  describe('Full Log Details Display', () => {
    it('displays all log fields in expanded view', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Expand first log
      const firstRow = screen.getByText('UPDATE PLAN').closest('tr')
      fireEvent.click(firstRow!)

      // Check all fields are displayed
      expect(screen.getByText('Log ID:')).toBeInTheDocument()
      expect(screen.getByText('Admin ID:')).toBeInTheDocument()
      expect(screen.getByText('Action Type:')).toBeInTheDocument()
      expect(screen.getByText('Target Type:')).toBeInTheDocument()
      expect(screen.getByText('Target ID:')).toBeInTheDocument()
      expect(screen.getByText('Timestamp:')).toBeInTheDocument()
    })

    it('displays full IDs in expanded view', () => {
      render(<AuditLogTable logs={mockLogs} loading={false} />)

      // Expand first log
      const firstRow = screen.getByText('UPDATE PLAN').closest('tr')
      fireEvent.click(firstRow!)

      // Full IDs should be visible (not truncated)
      expect(screen.getByText('admin-123-456-789')).toBeInTheDocument()
      expect(screen.getByText('user-abc-def-ghi')).toBeInTheDocument()
    })
  })
})
