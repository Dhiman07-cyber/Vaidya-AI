import { useState, useMemo } from 'react'
import styles from '@/styles/ClinicalMapViewer.module.css'

export interface MapNode {
  id: string
  label: string
  type: 'main' | 'symptom' | 'diagnosis' | 'treatment' | 'complication' | 'category'
  description?: string
  x: number
  y: number
}

export interface MapConnection {
  from: string
  to: string
  label?: string
}

interface ClinicalMapViewerProps {
  title: string
  nodes: MapNode[]
  connections: MapConnection[]
}

// Medical icons as SVG paths for common conditions
const getMedicalIcon = (topic: string): string => {
  const topicLower = topic.toLowerCase()
  if (topicLower.includes('pulmonary') || topicLower.includes('lung') || topicLower.includes('respiratory')) {
    return 'lungs'
  }
  if (topicLower.includes('heart') || topicLower.includes('cardiac') || topicLower.includes('cardio')) {
    return 'heart'
  }
  if (topicLower.includes('brain') || topicLower.includes('neuro') || topicLower.includes('stroke')) {
    return 'brain'
  }
  if (topicLower.includes('kidney') || topicLower.includes('renal')) {
    return 'kidney'
  }
  if (topicLower.includes('liver') || topicLower.includes('hepat')) {
    return 'liver'
  }
  if (topicLower.includes('diabetes') || topicLower.includes('glucose') || topicLower.includes('insulin')) {
    return 'diabetes'
  }
  return 'medical'
}

// SVG icon components
const LungsIcon = () => (
  <g transform="translate(-20, -20) scale(0.8)">
    <path d="M25 8c-2 0-4 1-5 3v20c0 4 3 7 7 7s7-3 7-7V15c0-4-4-7-9-7z" fill="#ff8a8a" stroke="#e05555" strokeWidth="1.5"/>
    <path d="M25 8c2 0 4 1 5 3v20c0 4-3 7-7 7s-7-3-7-7V15c0-4 4-7 9-7z" fill="#ff8a8a" stroke="#e05555" strokeWidth="1.5"/>
    <path d="M25 5v8M22 8h6" stroke="#e05555" strokeWidth="2" strokeLinecap="round"/>
  </g>
)

const HeartIcon = () => (
  <g transform="translate(-18, -16) scale(0.75)">
    <path d="M24 44c-1-1-16-12-16-24 0-6 5-11 11-11 4 0 7 2 9 5 2-3 5-5 9-5 6 0 11 5 11 11 0 12-15 23-16 24l-4 3-4-3z" fill="#ff6b6b" stroke="#e05555" strokeWidth="2"/>
  </g>
)

const BrainIcon = () => (
  <g transform="translate(-18, -18) scale(0.7)">
    <ellipse cx="25" cy="25" rx="18" ry="16" fill="#ffb3d9" stroke="#d63384" strokeWidth="2"/>
    <path d="M15 20c0-3 2-5 5-5s5 2 5 5M25 15c0-3 2-5 5-5s5 2 5 5M12 28c-2 0-4-2-4-4s2-4 4-4M38 28c2 0 4-2 4-4s-2-4-4-4" stroke="#d63384" strokeWidth="1.5" fill="none"/>
  </g>
)

const MedicalIcon = () => (
  <g transform="translate(-15, -15) scale(0.6)">
    <rect x="10" y="18" width="30" height="14" rx="2" fill="#667eea"/>
    <rect x="18" y="10" width="14" height="30" rx="2" fill="#667eea"/>
  </g>
)

const renderIcon = (iconType: string) => {
  switch (iconType) {
    case 'lungs': return <LungsIcon />
    case 'heart': return <HeartIcon />
    case 'brain': return <BrainIcon />
    default: return <MedicalIcon />
  }
}

export default function ClinicalMapViewer({ title, nodes, connections }: ClinicalMapViewerProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  // Get the main node to determine the icon
  const mainNode = nodes.find(n => n.type === 'main')
  const iconType = mainNode ? getMedicalIcon(mainNode.label) : 'medical'

  // Reorganize nodes with category intermediaries - improved layout
  const { displayNodes, displayConnections } = useMemo(() => {
    if (!nodes || nodes.length === 0) return { displayNodes: [], displayConnections: [] }

    const mainNodeData = nodes.find(n => n.type === 'main')
    if (!mainNodeData) return { displayNodes: nodes, displayConnections: connections }

    // Center position - larger canvas
    const centerX = 600
    const centerY = 400

    // Create category nodes with better angular distribution
    // Symptoms: top-left, Diagnosis: top-right, Treatment: bottom-left, Risk Factors: bottom-right
    const categories = [
      { type: 'symptom', label: 'Symptoms', angle: 225 },      // top-left
      { type: 'diagnosis', label: 'Diagnosis', angle: 315 },   // top-right  
      { type: 'treatment', label: 'Treatment', angle: 135 },   // bottom-left
      { type: 'complication', label: 'Risk Factors', angle: 45 } // bottom-right
    ]

    const newNodes: MapNode[] = []
    const newConnections: MapConnection[] = []

    // Add main node at center
    newNodes.push({
      ...mainNodeData,
      x: centerX,
      y: centerY
    })

    // Process each category
    categories.forEach(cat => {
      const categoryNodes = nodes.filter(n => n.type === cat.type)
      if (categoryNodes.length === 0) return

      // Calculate category node position - increased radius
      const catRadius = 200
      const catAngleRad = (cat.angle * Math.PI) / 180
      const catX = centerX + Math.cos(catAngleRad) * catRadius
      const catY = centerY - Math.sin(catAngleRad) * catRadius // Negative for correct orientation

      const categoryNodeId = `category-${cat.type}`
      
      // Add category node
      newNodes.push({
        id: categoryNodeId,
        label: cat.label,
        type: 'category',
        x: catX,
        y: catY
      })

      // Connect main to category
      newConnections.push({
        from: mainNodeData.id,
        to: categoryNodeId
      })

      // Position detail nodes in a fan pattern from category
      const detailRadius = 140
      const nodeCount = categoryNodes.length
      
      // Calculate spread angle based on number of nodes (more nodes = wider spread)
      const maxSpread = 90 // max degrees for the fan
      const spreadPerNode = Math.min(35, maxSpread / Math.max(nodeCount - 1, 1))
      const totalSpread = spreadPerNode * (nodeCount - 1)
      const startAngle = cat.angle - totalSpread / 2

      categoryNodes.forEach((node, idx) => {
        const detailAngle = nodeCount === 1 ? cat.angle : startAngle + idx * spreadPerNode
        const detailAngleRad = (detailAngle * Math.PI) / 180
        const detailX = catX + Math.cos(detailAngleRad) * detailRadius
        const detailY = catY - Math.sin(detailAngleRad) * detailRadius

        newNodes.push({
          ...node,
          x: detailX,
          y: detailY
        })

        // Connect category to detail
        newConnections.push({
          from: categoryNodeId,
          to: node.id
        })
      })
    })

    return { displayNodes: newNodes, displayConnections: newConnections }
  }, [nodes, connections])

  if (!nodes || nodes.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🗺️</div>
          <p>No nodes to display</p>
        </div>
      </div>
    )
  }

  const getNodeStyle = (type: string) => {
    switch (type) {
      case 'main': return { fill: '#fff', stroke: '#667eea', strokeWidth: 0, textColor: '#2d3748' }
      case 'category': return { fill: '#f8fafc', stroke: '#cbd5e1', strokeWidth: 2, textColor: '#475569' }
      case 'symptom': return { fill: '#fef3c7', stroke: '#f59e0b', strokeWidth: 2, textColor: '#92400e' }
      case 'diagnosis': return { fill: '#dbeafe', stroke: '#3b82f6', strokeWidth: 2, textColor: '#1e40af' }
      case 'treatment': return { fill: '#d1fae5', stroke: '#10b981', strokeWidth: 2, textColor: '#065f46' }
      case 'complication': return { fill: '#fce7f3', stroke: '#ec4899', strokeWidth: 2, textColor: '#9d174d' }
      default: return { fill: '#f1f5f9', stroke: '#94a3b8', strokeWidth: 2, textColor: '#475569' }
    }
  }

  const getCategoryLabel = (type: string) => {
    switch (type) {
      case 'symptom': return 'Symptoms'
      case 'diagnosis': return 'Diagnosis'
      case 'treatment': return 'Treatment'
      case 'complication': return 'Risk Factors'
      default: return ''
    }
  }

  // Calculate curved path between two points
  const getCurvedPath = (x1: number, y1: number, x2: number, y2: number) => {
    const midX = (x1 + x2) / 2
    const midY = (y1 + y2) / 2
    const dx = x2 - x1
    const dy = y2 - y1
    const dist = Math.sqrt(dx * dx + dy * dy)
    const curvature = dist * 0.15
    
    // Perpendicular offset for curve
    const nx = -dy / dist * curvature
    const ny = dx / dist * curvature
    
    const ctrlX = midX + nx
    const ctrlY = midY + ny
    
    return `M ${x1} ${y1} Q ${ctrlX} ${ctrlY} ${x2} ${y2}`
  }

  return (
    <div className={styles.container}>
      <svg className={styles.svg} viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid meet">
        <defs>
          <filter id="softShadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="3" stdDeviation="5" floodColor="#000" floodOpacity="0.1"/>
          </filter>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
          <linearGradient id="centerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffeef5"/>
            <stop offset="100%" stopColor="#ffe4ec"/>
          </linearGradient>
        </defs>

        {/* Draw connections with curved lines */}
        <g>
          {displayConnections.map((conn, idx) => {
            const fromNode = displayNodes.find(n => n.id === conn.from)
            const toNode = displayNodes.find(n => n.id === conn.to)
            if (!fromNode || !toNode) return null
            
            const isHighlighted = selectedNode === conn.from || selectedNode === conn.to
            const isFromMain = fromNode.type === 'main'
            
            return (
              <path
                key={idx}
                d={getCurvedPath(fromNode.x, fromNode.y, toNode.x, toNode.y)}
                fill="none"
                stroke={isHighlighted ? '#667eea' : '#d1d5db'}
                strokeWidth={isFromMain ? 2.5 : 2}
                opacity={isHighlighted ? 1 : 0.6}
              />
            )
          })}
        </g>

        {/* Draw nodes */}
        <g>
          {displayNodes.map((node) => {
            const style = getNodeStyle(node.type)
            const isSelected = selectedNode === node.id
            const isHovered = hoveredNode === node.id
            const isMain = node.type === 'main'
            const isCategory = node.type === 'category'

            if (isMain) {
              // Main node with icon - circular design (larger)
              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => setSelectedNode(isSelected ? null : node.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Outer glow on hover */}
                  {(isHovered || isSelected) && (
                    <circle
                      r="78"
                      fill="none"
                      stroke="#667eea"
                      strokeWidth="2"
                      opacity="0.3"
                    />
                  )}
                  {/* Main circle background */}
                  <circle
                    r="70"
                    fill="url(#centerGradient)"
                    filter="url(#softShadow)"
                  />
                  {/* Icon */}
                  <g transform="translate(0, -14) scale(1.2)">
                    {renderIcon(iconType)}
                  </g>
                  {/* Label - handle long text */}
                  <text
                    textAnchor="middle"
                    y="42"
                    fill="#2d3748"
                    fontSize="14"
                    fontWeight="700"
                    fontFamily="system-ui, -apple-system, sans-serif"
                  >
                    {node.label.length > 20 ? (
                      <>
                        <tspan x="0" dy="0">{node.label.substring(0, 12)}</tspan>
                        <tspan x="0" dy="16">{node.label.substring(12, 24)}</tspan>
                      </>
                    ) : node.label}
                  </text>
                </g>
              )
            }

            if (isCategory) {
              // Category nodes - pill shaped, larger
              const width = 110
              const height = 38
              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => setSelectedNode(isSelected ? null : node.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect
                    x={-width / 2}
                    y={-height / 2}
                    width={width}
                    height={height}
                    rx={height / 2}
                    fill={style.fill}
                    stroke={isHovered || isSelected ? '#667eea' : style.stroke}
                    strokeWidth={style.strokeWidth}
                    filter="url(#softShadow)"
                  />
                  <text
                    textAnchor="middle"
                    dy="0.35em"
                    fill={style.textColor}
                    fontSize="13"
                    fontWeight="600"
                    fontFamily="system-ui, -apple-system, sans-serif"
                  >
                    {node.label}
                  </text>
                </g>
              )
            }

            // Detail nodes - pill shaped with colored borders (larger)
            const labelLength = node.label.length
            const width = Math.max(100, Math.min(160, labelLength * 8 + 30))
            const height = 36

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => setSelectedNode(isSelected ? null : node.id)}
                style={{ cursor: 'pointer' }}
              >
                {/* Hover/selected highlight */}
                {(isHovered || isSelected) && (
                  <rect
                    x={-width / 2 - 4}
                    y={-height / 2 - 4}
                    width={width + 8}
                    height={height + 8}
                    rx={(height + 8) / 2}
                    fill="none"
                    stroke={style.stroke}
                    strokeWidth="1.5"
                    opacity="0.4"
                  />
                )}
                <rect
                  x={-width / 2}
                  y={-height / 2}
                  width={width}
                  height={height}
                  rx={height / 2}
                  fill={style.fill}
                  stroke={style.stroke}
                  strokeWidth={style.strokeWidth}
                  filter="url(#softShadow)"
                />
                <text
                  textAnchor="middle"
                  dy="0.35em"
                  fill={style.textColor}
                  fontSize="12"
                  fontWeight="600"
                  fontFamily="system-ui, -apple-system, sans-serif"
                >
                  {node.label.length > 16 ? node.label.substring(0, 16) + '...' : node.label}
                </text>
              </g>
            )
          })}
        </g>

        {/* Tooltip for hovered node with description */}
        {hoveredNode && (() => {
          const node = displayNodes.find(n => n.id === hoveredNode)
          if (!node || !node.description || node.type === 'main' || node.type === 'category') return null
          
          const tooltipWidth = 180
          const tooltipHeight = 50
          const tooltipX = node.x + 80
          const tooltipY = node.y - 25
          
          return (
            <g transform={`translate(${tooltipX}, ${tooltipY})`}>
              <rect
                x="0"
                y="0"
                width={tooltipWidth}
                height={tooltipHeight}
                rx="8"
                fill="white"
                stroke="#e2e8f0"
                strokeWidth="1"
                filter="url(#softShadow)"
              />
              <text
                x="12"
                y="30"
                fill="#64748b"
                fontSize="11"
                fontFamily="system-ui, -apple-system, sans-serif"
              >
                {node.description.length > 35 ? node.description.substring(0, 35) + '...' : node.description}
              </text>
            </g>
          )
        })()}
      </svg>

      {/* Selected node details panel */}
      {selectedNode && (() => {
        const node = displayNodes.find(n => n.id === selectedNode)
        if (!node) return null
        const style = getNodeStyle(node.type)
        
        return (
          <div className={styles.nodeDetails} style={{ borderColor: style.stroke }}>
            <div className={styles.nodeDetailsHeader}>
              <span 
                className={styles.nodeTypeBadge} 
                style={{ background: style.fill, color: style.textColor, borderColor: style.stroke }}
              >
                {node.type === 'category' ? node.label : getCategoryLabel(node.type)}
              </span>
            </div>
            <h4>{node.label}</h4>
            {node.description && (
              <p className={styles.nodeDescription}>{node.description}</p>
            )}
            <button onClick={() => setSelectedNode(null)} className={styles.closeBtn}>
              Close
            </button>
          </div>
        )
      })()}
    </div>
  )
}

/**
 * Parse clinical map data from text format
 * Supports format: TYPE: Label | Description
 */
export function parseClinicalMapData(text: string): { nodes: MapNode[], connections: MapConnection[] } {
  let contentText = text
  if (text && text.startsWith('{')) {
    try {
      const parsed = JSON.parse(text)
      contentText = parsed.content || text
    } catch (e) {
      // Not valid JSON, use as-is
    }
  }
  
  const lines = contentText.split('\n').filter(line => line.trim())
  const nodes: MapNode[] = []
  const connections: MapConnection[] = []
  
  let nodeCounter = 0
  
  // First pass: create nodes
  lines.forEach(line => {
    // Support format: TYPE: Label | Description
    const match = line.match(/^(MAIN|SYMPTOM|DIAGNOSIS|TREATMENT|COMPLICATION):\s*(.+?)(?:\s*\|\s*(.+))?$/i)
    if (match) {
      const type = match[1].toLowerCase() as MapNode['type']
      const label = match[2].trim()
      const description = match[3]?.trim()
      const id = `node-${nodeCounter++}`
      
      // Initial positions (will be recalculated by the component)
      let x = 450, y = 280
      const typeIndex = nodes.filter(n => n.type === type).length
      
      switch (type) {
        case 'main':
          x = 450
          y = 280
          break
        case 'symptom':
          x = 150 + (typeIndex % 2) * 80
          y = 120 + typeIndex * 60
          break
        case 'diagnosis':
          x = 650 + (typeIndex % 2) * 80
          y = 100 + typeIndex * 60
          break
        case 'treatment':
          x = 650 + (typeIndex % 2) * 80
          y = 380 + typeIndex * 55
          break
        case 'complication':
          x = 150 + (typeIndex % 2) * 80
          y = 400 + typeIndex * 55
          break
      }
      
      nodes.push({ id, label, type, description, x, y })
    }
  })
  
  // Second pass: create connections
  lines.forEach(line => {
    const match = line.match(/^CONNECTION:\s*(.+?)\s*->\s*(.+?)(?:\s*\[(.+)\])?$/i)
    if (match) {
      const fromLabel = match[1].trim().toLowerCase()
      const toLabel = match[2].trim().toLowerCase()
      const label = match[3]?.trim()
      
      const fromNode = nodes.find(n => n.label.toLowerCase() === fromLabel)
      const toNode = nodes.find(n => n.label.toLowerCase() === toLabel)
      
      if (fromNode && toNode) {
        connections.push({ from: fromNode.id, to: toNode.id, label })
      }
    }
  })
  
  return { nodes, connections }
}
