import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/router'
import AdminDashboard from '@/pages/admin/index'
import UsersPage from '@/pages/admin/users'
import AuditLogsPage from '@/pages/admin/audit-logs'
import { supabase } from '@/lib/supabase'

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}))

// Mock the supabase client
jest.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(),
      onAuthStateChange: jest.fn(),
    },
  },
}))

// Mock fetch globally
global.fetch = jest.fn()

describe('Admin Route Protection', () => {
  const mockPush = jest.fn()
  const mockRouter = {
    push: mockPush,
    pathname: '/admin',
    query: {},
    asPath: '/admin',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(global.fetch as jest.Mock).mockClear()
  })

  describe('Non-admin users', () => {
    it('redirects non-authenticated users to login page', async () => {
      const mockGetSession = supabase.auth.getSession as jest.Mock
      const mockOnAuthStateChange = supabase.auth.onAuthStateChange as jest.Mock
      
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      })

      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })

    it('redirects authenticated non-admin users to chat page from admin dashboard', async () => {
      const mockGetSession = supabase.auth.getSession as jest.Mock
      const mockOnAuthStateChange = supabase.auth.onAuthStateChange as jest.Mock
      
      const mockUser = {
        id: '123',
        email: 'user@example.com',
        user_metadata: { name: 'Regular User' },
      }
      
      const mockSession = {
        user: mockUser,
        access_token: 'mock-token',
      }
      
      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      })

      // Mock API call to return 403 (non-admin)
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 403,
      })

      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/admin/users?limit=1'),
          expect.objectContaining({
            headers: {
              'Authorization': 'Bearer mock-token'
            }
          })
        )
        expect(mockPush).toHaveBeenCalledWith('/chat')
      })
    })

    it('redirects authenticated non-admin users to chat page from users page', async () => {
      const mockGetSession = supabase.auth.getSession as jest.Mock
      const mockOnAuthStateChange = supabase.auth.onAuthStateChange as jest.Mock
      
      const mockUser = {
        id: '123',
        email: 'user@example.com',
        user_metadata: { name: 'Regular User' },
      }
      
      const mockSession = {
        user: mockUser,
        access_token: 'mock-token',
      }
      
      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      })

      // Mock API call to return 403 (non-admin)
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 403,
      })

      render(<UsersPage />)
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/admin/users?limit=100'),
          expect.objectContaining({
            headers: {
              'Authorization': 'Bearer mock-token'
            }
          })
        )
        expect(mockPush).toHaveBeenCalledWith('/chat')
      })
    })

    it('redirects authenticated non-admin users to chat page from audit logs page', async () => {
      const mockGetSession = supabase.auth.getSession as jest.Mock
      const mockOnAuthStateChange = supabase.auth.onAuthStateChange as jest.Mock
      
      const mockUser = {
        id: '123',
        email: 'user@example.com',
        user_metadata: { name: 'Regular User' },
      }
      
      const mockSession = {
        user: mockUser,
        access_token: 'mock-token',
      }
      
      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      })

      // Mock API call to return 403 (non-admin)
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 403,
      })

      render(<AuditLogsPage />)
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/admin/audit-logs'),
          expect.objectContaining({
            headers: {
              'Authorization': 'Bearer mock-token'
            }
          })
        )
        expect(mockPush).toHaveBeenCalledWith('/chat')
      })
    })
  })

  describe('Admin users', () => {
    it('allows admin users to access admin dashboard', async () => {
      const mockGetSession = supabase.auth.getSession as jest.Mock
      const mockOnAuthStateChange = supabase.auth.onAuthStateChange as jest.Mock
      
      const mockUser = {
        id: 'admin-123',
        email: 'admin@example.com',
        user_metadata: { name: 'Admin User' },
      }
      
      const mockSession = {
        user: mockUser,
        access_token: 'admin-token',
      }
      
      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      })

      // Mock API call to return 200 (admin)
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ([]),
      })

      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/admin/users?limit=1'),
          expect.objectContaining({
            headers: {
              'Authorization': 'Bearer admin-token'
            }
          })
        )
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
        expect(mockPush).not.toHaveBeenCalled()
      })
    })

    it('allows admin users to access users management page', async () => {
      const mockGetSession = supabase.auth.getSession as jest.Mock
      const mockOnAuthStateChange = supabase.auth.onAuthStateChange as jest.Mock
      
      const mockUser = {
        id: 'admin-123',
        email: 'admin@example.com',
        user_metadata: { name: 'Admin User' },
      }
      
      const mockSession = {
        user: mockUser,
        access_token: 'admin-token',
      }
      
      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      })

      const mockUsers = [
        {
          id: 'user-1',
          email: 'user1@example.com',
          name: 'User One',
          plan: 'free',
          role: null,
          disabled: false,
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      // Mock API call to return 200 (admin) with users
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockUsers,
      })

      render(<UsersPage />)
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/admin/users?limit=100'),
          expect.objectContaining({
            headers: {
              'Authorization': 'Bearer admin-token'
            }
          })
        )
        expect(screen.getByRole('heading', { name: 'User Management' })).toBeInTheDocument()
        expect(mockPush).not.toHaveBeenCalled()
      })
    })

    it('allows admin users to access audit logs page', async () => {
      const mockGetSession = supabase.auth.getSession as jest.Mock
      const mockOnAuthStateChange = supabase.auth.onAuthStateChange as jest.Mock
      
      const mockUser = {
        id: 'admin-123',
        email: 'admin@example.com',
        user_metadata: { name: 'Admin User' },
      }
      
      const mockSession = {
        user: mockUser,
        access_token: 'admin-token',
      }
      
      mockGetSession.mockResolvedValue({
        data: { session: mockSession },
        error: null,
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      })

      const mockLogs = [
        {
          id: 'log-1',
          admin_id: 'admin-123',
          action_type: 'update_plan',
          target_type: 'user',
          target_id: 'user-1',
          details: { old_plan: 'free', new_plan: 'student' },
          timestamp: '2024-01-01T00:00:00Z',
        },
      ]

      // Mock API call to return 200 (admin) with logs
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockLogs,
      })

      render(<AuditLogsPage />)
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/admin/audit-logs'),
          expect.objectContaining({
            headers: {
              'Authorization': 'Bearer admin-token'
            }
          })
        )
        expect(screen.getByRole('heading', { name: 'Audit Logs' })).toBeInTheDocument()
        expect(mockPush).not.toHaveBeenCalled()
      })
    })
  })

  describe('Loading states', () => {
    it('shows loading state while checking admin access', () => {
      const mockGetSession = supabase.auth.getSession as jest.Mock
      const mockOnAuthStateChange = supabase.auth.onAuthStateChange as jest.Mock
      
      mockGetSession.mockImplementation(() => new Promise(() => {})) // Never resolves
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      })

      render(<AdminDashboard />)
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })
})
