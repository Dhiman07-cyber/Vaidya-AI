import { useState, useEffect } from 'react'
import styles from '@/styles/ClinicalMapViewer.module.css'

interface MapNode {
  id: string
  label: string
  type: 'main' | 'symptom' | 'diagnosis' | 'treatment' | 'complication'
  x: number
  y: number
}

interface MapConnection {
  from: string
  to: string
  label?: string
}

interface ClinicalMapViewerProps {
  title: string
  nodes: MapNode[]
  connections: MapConnection[]
}

export default function ClinicalMapViewer({ title, nodes, connections }: ClinicalMapViewerProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  console.log('ClinicalMapViewer rendering with:', { title, nodesCount: nodes?.length || 0, connectionsCount: connections?.length || 0 })
  console.log('Nodes:', nodes)
  console.log('Connections:', connections)

  // Safety check
  if (!nodes || nodes.length === 0) {
    return (
      <div className={styles.container}>
        <div style={{ padding: '2rem', textAlign: 'center', color: '#999' }}>
          No nodes to display
        </div>
      </div>
    )
  }

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'main': return '#667eea'
      case 'symptom': return '#f093fb'
      case 'diagnosis': return '#4facfe'
      case 'treatment': return '#43e97b'
      case 'complication': return '#fa709a'
      default: return '#6c757d'
    }
  }

  const getNodeSize = (type: string) => {
    return type === 'main' ? 100 : 70
  }

  const getNodeLabel = (type: string) => {
    switch (type) {
      case 'symptom': return 'Symptoms'
      case 'diagnosis': return 'Diagnosis'
      case 'treatment': return 'Treatment'
      case 'complication': return 'Risk Factors'
      default: return type
    }
  }

  return (
    <div className={styles.container}>
      <svg className={styles.svg} viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid meet">
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#999" />
          </marker>
          
          {/* Glow filter for selected nodes */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Draw connections */}
        <g className={styles.connections}>
          {connections.map((conn, idx) => {
            const fromNode = nodes.find(n => n.id === conn.from)
            const toNode = nodes.find(n => n.id === conn.to)
            
            if (!fromNode || !toNode) return null

            const isHighlighted = selectedNode === conn.from || selectedNode === conn.to

            return (
              <g key={idx}>
                <line
                  x1={fromNode.x}
                  y1={fromNode.y}
                  x2={toNode.x}
                  y2={toNode.y}
                  stroke={isHighlighted ? '#667eea' : '#d0d0d0'}
                  strokeWidth={isHighlighted ? 2.5 : 2}
                  markerEnd="url(#arrowhead)"
                  opacity={isHighlighted ? 1 : 0.5}
                />
                {conn.label && (
                  <text
                    x={(fromNode.x + toNode.x) / 2}
                    y={(fromNode.y + toNode.y) / 2}
                    fill="#666"
                    fontSize="11"
                    textAnchor="middle"
                    className={styles.connectionLabel}
                  >
                    {conn.label}
                  </text>
                )}
              </g>
            )
          })}
        </g>

        {/* Draw nodes */}
        <g className={styles.nodes}>
          {nodes.map((node) => {
            const size = getNodeSize(node.type)
            const color = getNodeColor(node.type)
            const isSelected = selectedNode === node.id
            const isHovered = hoveredNode === node.id

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => setSelectedNode(isSelected ? null : node.id)}
                style={{ cursor: 'pointer' }}
                filter={isSelected ? 'url(#glow)' : undefined}
              >
                {/* Node background */}
                <rect
                  x={-size / 2}
                  y={-size / 2.5}
                  width={size}
                  height={size / 1.5}
                  rx="8"
                  fill={color}
                  stroke={isSelected || isHovered ? '#fff' : color}
                  strokeWidth={isSelected || isHovered ? 3 : 1}
                  opacity={isSelected || isHovered ? 1 : 0.95}
                  className={styles.nodeRect}
                />
                
                {/* Node label - type */}
                {node.type !== 'main' && (
                  <text
                    textAnchor="middle"
                    dy="-0.5em"
                    fill="white"
                    fontSize={node.type === 'main' ? '14' : '10'}
                    fontWeight="600"
                    className={styles.nodeTypeLabel}
                  >
                    {getNodeLabel(node.type)}
                  </text>
                )}
                
                {/* Node label - content */}
                <text
                  textAnchor="middle"
                  dy={node.type === 'main' ? '0.3em' : '0.8em'}
                  fill="white"
                  fontSize={node.type === 'main' ? '16' : '12'}
                  fontWeight={node.type === 'main' ? '700' : '600'}
                  className={styles.nodeText}
                >
                  {node.label.length > 20 ? node.label.substring(0, 20) + '...' : node.label}
                </text>
                
                {/* Additional details for multi-line labels */}
                {node.label.length > 20 && (
                  <text
                    textAnchor="middle"
                    dy="2em"
                    fill="white"
                    fontSize="10"
                    fontWeight="400"
                    className={styles.nodeSubtext}
                    opacity="0.9"
                  >
                    {node.label.substring(20, 40)}...
                  </text>
                )}
              </g>
            )
          })}
        </g>
      </svg>

      {selectedNode && (
        <div className={styles.nodeDetails}>
          <h4>{nodes.find(n => n.id === selectedNode)?.label}</h4>
          <p className={styles.nodeType}>
            Type: {getNodeLabel(nodes.find(n => n.id === selectedNode)?.type || '')}
          </p>
          <button onClick={() => setSelectedNode(null)} className={styles.closeBtn}>
            Close
          </button>
        </div>
      )}
    </div>
  )
}

/**
 * Parse clinical map data from text format
 * Expected format:
 * MAIN: Topic Name
 * SYMPTOM: Symptom 1
 * SYMPTOM: Symptom 2
 * DIAGNOSIS: Diagnosis method
 * TREATMENT: Treatment option
 * COMPLICATION: Possible complication
 * CONNECTION: from -> to [label]
 */
export function parseClinicalMapData(text: string): { nodes: MapNode[], connections: MapConnection[] } {
  console.log('Parsing clinical map data:', text)
  
  const lines = text.split('\n').filter(line => line.trim())
  const nodes: MapNode[] = []
  const connections: MapConnection[] = []
  
  let nodeCounter = 0
  const nodePositions: { [key: string]: { x: number, y: number } } = {}
  
  // First pass: create nodes
  lines.forEach(line => {
    const match = line.match(/^(MAIN|SYMPTOM|DIAGNOSIS|TREATMENT|COMPLICATION):\s*(.+)$/i)
    if (match) {
      const type = match[1].toLowerCase() as MapNode['type']
      const label = match[2].trim()
      const id = `node-${nodeCounter++}`
      
      // Calculate position based on type - arranged in a radial pattern around center
      let x = 600, y = 400
      const typeIndex = nodes.filter(n => n.type === type).length
      
      switch (type) {
        case 'main':
          x = 600
          y = 400
          break
        case 'symptom':
          // Top left area
          x = 250 + (typeIndex * 180)
          y = 200 + (typeIndex % 2) * 80
          break
        case 'diagnosis':
          // Right side
          x = 850 + (typeIndex * 120)
          y = 250 + (typeIndex * 100)
          break
        case 'treatment':
          // Bottom right
          x = 850 + (typeIndex * 120)
          y = 550 + (typeIndex % 2) * 60
          break
        case 'complication':
          // Bottom left
          x = 250 + (typeIndex * 180)
          y = 600 + (typeIndex % 2) * 60
          break
      }
      
      nodes.push({ id, label, type, x, y })
      nodePositions[label.toLowerCase()] = { x, y }
    }
  })
  
  console.log('Parsed nodes:', nodes)
  
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
        connections.push({
          from: fromNode.id,
          to: toNode.id,
          label
        })
      }
    }
  })
  
  console.log('Parsed connections:', connections)
  
  return { nodes, connections }
}
