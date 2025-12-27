import { useState } from 'react'
import UserDetails from './UserDetails'

export interface User {
  id: string
  email: string
  name: string
  plan: string
  role: string | null
  disabled: boolean
  created_at: string
}

interface UserListProps {
  users: User[]
  loading: boolean
  onPlanChange: (userId: string, newPlan: string) => Promise<void>
  onResetUsage: (userId: string) => Promise<void>
  onDisableUser: (userId: string, disabled: boolean) => Promise<void>
}

/**
 * User List Component
 * Displays list of users with management actions
 * Requirements: 13.1, 13.2
 */
export default function UserList({
  users,
  loading,
  onPlanChange,
  onResetUsage,
  onDisableUser
}: UserListProps) {
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  if (loading) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <p>Loading users...</p>
      </div>
    )
  }

  if (users.length === 0) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <p style={{ color: '#6c757d' }}>No users found</p>
      </div>
    )
  }

  return (
    <div>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #dee2e6',
        overflow: 'hidden'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse'
        }}>
          <thead>
            <tr style={{
              backgroundColor: '#f8f9fa',
              borderBottom: '2px solid #dee2e6'
            }}>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Name</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Email</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Plan</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Status</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Created</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr
                key={user.id}
                style={{
                  borderBottom: '1px solid #dee2e6',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f8f9fa'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'white'
                }}
              >
                <td style={{ padding: '12px' }}>{user.name}</td>
                <td style={{ padding: '12px' }}>{user.email}</td>
                <td style={{ padding: '12px' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    backgroundColor: 
                      user.plan === 'admin' ? '#dc3545' :
                      user.plan === 'pro' ? '#28a745' :
                      user.plan === 'student' ? '#007bff' :
                      '#6c757d',
                    color: 'white'
                  }}>
                    {user.plan.toUpperCase()}
                  </span>
                </td>
                <td style={{ padding: '12px' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    backgroundColor: user.disabled ? '#dc3545' : '#28a745',
                    color: 'white'
                  }}>
                    {user.disabled ? 'DISABLED' : 'ACTIVE'}
                  </span>
                </td>
                <td style={{ padding: '12px', fontSize: '14px', color: '#6c757d' }}>
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td style={{ padding: '12px' }}>
                  <button
                    onClick={() => setSelectedUser(user)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#007bff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '13px'
                    }}
                  >
                    Manage
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* User Details Modal */}
      {selectedUser && (
        <UserDetails
          user={selectedUser}
          onClose={() => setSelectedUser(null)}
          onPlanChange={onPlanChange}
          onResetUsage={onResetUsage}
          onDisableUser={onDisableUser}
        />
      )}
    </div>
  )
}
