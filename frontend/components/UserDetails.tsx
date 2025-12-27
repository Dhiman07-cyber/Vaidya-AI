import { useState } from 'react'

export interface User {
  id: string
  email: string
  name: string
  plan: string
  role: string | null
  disabled: boolean
  created_at: string
}

interface UserDetailsProps {
  user: User
  onClose: () => void
  onPlanChange: (userId: string, newPlan: string) => Promise<void>
  onResetUsage: (userId: string) => Promise<void>
  onDisableUser: (userId: string, disabled: boolean) => Promise<void>
}

/**
 * User Details Component
 * Modal for viewing and managing individual user details
 * Requirements: 13.2, 13.3, 13.4, 13.5
 */
export default function UserDetails({
  user,
  onClose,
  onPlanChange,
  onResetUsage,
  onDisableUser
}: UserDetailsProps) {
  const [selectedPlan, setSelectedPlan] = useState(user.plan)
  const [updating, setUpdating] = useState(false)

  const handlePlanChange = async () => {
    if (selectedPlan === user.plan) {
      alert('Please select a different plan')
      return
    }

    setUpdating(true)
    try {
      await onPlanChange(user.id, selectedPlan)
      onClose()
    } catch (err) {
      console.error('Failed to update plan:', err)
    } finally {
      setUpdating(false)
    }
  }

  const handleResetUsage = async () => {
    setUpdating(true)
    try {
      await onResetUsage(user.id)
    } catch (err) {
      console.error('Failed to reset usage:', err)
    } finally {
      setUpdating(false)
    }
  }

  const handleDisableToggle = async () => {
    setUpdating(true)
    try {
      await onDisableUser(user.id, !user.disabled)
      onClose()
    } catch (err) {
      console.error('Failed to toggle user status:', err)
    } finally {
      setUpdating(false)
    }
  }

  return (
    <>
      {/* Modal Overlay */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}
      >
        {/* Modal Content */}
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '30px',
            maxWidth: '600px',
            width: '90%',
            maxHeight: '90vh',
            overflow: 'auto'
          }}
        >
          {/* Header */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px',
            paddingBottom: '15px',
            borderBottom: '2px solid #dee2e6'
          }}>
            <h2 style={{ margin: 0 }}>User Details</h2>
            <button
              onClick={onClose}
              style={{
                padding: '8px 16px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Close
            </button>
          </div>

          {/* User Information */}
          <div style={{ marginBottom: '30px' }}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                Name:
              </label>
              <p style={{ margin: 0, padding: '8px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                {user.name}
              </p>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                Email:
              </label>
              <p style={{ margin: 0, padding: '8px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                {user.email}
              </p>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                User ID:
              </label>
              <p style={{
                margin: 0,
                padding: '8px',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                fontSize: '12px',
                fontFamily: 'monospace'
              }}>
                {user.id}
              </p>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                Created:
              </label>
              <p style={{ margin: 0, padding: '8px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                {new Date(user.created_at).toLocaleString()}
              </p>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                Status:
              </label>
              <span style={{
                padding: '6px 12px',
                borderRadius: '4px',
                fontSize: '14px',
                fontWeight: 'bold',
                backgroundColor: user.disabled ? '#dc3545' : '#28a745',
                color: 'white'
              }}>
                {user.disabled ? 'DISABLED' : 'ACTIVE'}
              </span>
            </div>
          </div>

          {/* Plan Management */}
          <div style={{
            marginBottom: '30px',
            padding: '20px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '15px' }}>Change Plan</h3>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                Current Plan: <span style={{ color: '#007bff' }}>{user.plan.toUpperCase()}</span>
              </label>
              <select
                value={selectedPlan}
                onChange={(e) => setSelectedPlan(e.target.value)}
                disabled={updating}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '4px',
                  border: '1px solid #ced4da',
                  fontSize: '14px'
                }}
              >
                <option value="free">Free</option>
                <option value="student">Student</option>
                <option value="pro">Pro</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button
              onClick={handlePlanChange}
              disabled={updating || selectedPlan === user.plan}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: selectedPlan === user.plan ? '#6c757d' : '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: selectedPlan === user.plan ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              {updating ? 'Updating...' : 'Update Plan'}
            </button>
          </div>

          {/* Actions */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '15px'
          }}>
            <button
              onClick={handleResetUsage}
              disabled={updating}
              style={{
                padding: '12px',
                backgroundColor: '#ffc107',
                color: '#000',
                border: 'none',
                borderRadius: '4px',
                cursor: updating ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              Reset Usage
            </button>

            <button
              onClick={handleDisableToggle}
              disabled={updating}
              style={{
                padding: '12px',
                backgroundColor: user.disabled ? '#28a745' : '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: updating ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              {user.disabled ? 'Enable User' : 'Disable User'}
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
