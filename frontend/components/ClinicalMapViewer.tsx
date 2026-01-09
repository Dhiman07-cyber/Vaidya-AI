import { useState } from 'react'
import styles from '@/styles/ClinicalMapViewer.module.css'

export interface MapNode {
  id: string
  label: string
  type: 'main' | 'symptom' | 'diagnosis' | 'treatment' | 'complication'
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

export default function ClinicalMapViewer({ title, nodes, connections }: ClinicalMapViewerProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

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

  const getNodeLabel = (type: string) => {
    switch (type) {
      case 'symptom': return 'Symptoms'
      case 'diagnosis': return 'Diagnosis'
      case 'treatment': return 'Treatment'
      case 'complication': return 'Risk Factors'
      default: return ''
    }
  }

  return (
    <div className={styles.container}>
      <svg className={styles.svg} viewBox="0 0 800 500" preserveAspectRatio="xMidYMid meet">
        <defs>
          <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.1"/>
          </filter>
        </defs>

        {/* Draw connections */}
        <g>
          {connections.map((conn, idx) => {
            const fromNode = nodes.find(n => n.id === conn.from)
            const toNode = nodes.find(n => n.id === conn.to)
            if (!fromNode || !toNode) return null
            const isHighlighted = selectedNode === conn.from || selectedNode === conn.to

            return (
              <line
                key={idx}
                x1={fromNode.x}
                y1={fromNode.y}
                x2={toNode.x}
                y2={toNode.y}
                stroke={isHighlighted ? '#667eea' : '#e0e0e0'}
                strokeWidth={isHighlighted ? 2 : 1.5}
              />
            )
          })}
        </g>

        {/* Draw nodes */}
        <g>
          {nodes.map((node) => {
            const color = getNodeColor(node.type)
            const isSelected = selectedNode === node.id
            const isHovered = hoveredNode === node.id
            const isMain = node.type === 'main'
            const width = isMain ? 110 : 85
            const height = isMain ? 45 : 38

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
                  rx="6"
                  fill={color}
                  filter="url(#shadow)"
                  stroke={isSelected || isHovered ? '#fff' : 'none'}
                  strokeWidth={2}
                />
                {!isMain && (
                  <text
                    textAnchor="middle"
                    dy="-0.2em"
                    fill="white"
                    fontSize="7"
                    fontWeight="600"
                    opacity="0.9"
                    style={{ textTransform: 'uppercase', letterSpacing: '0.3px' }}
                  >
                    {getNodeLabel(node.type)}
                  </text>
                )}
                <text
                  textAnchor="middle"
                  dy={isMain ? '0.35em' : '0.9em'}
                  fill="white"
                  fontSize={isMain ? '12' : '9'}
                  fontWeight={isMain ? '700' : '600'}
                >
                  {node.label.length > 18 ? node.label.substring(0, 18) + '...' : node.label}
                </text>
              </g>
            )
          })}
        </g>
      </svg>

      {selectedNode && (
        <div className={styles.nodeDetails}>
          <h4>{nodes.find(n => n.id === selectedNode)?.label}</h4>
          <p className={styles.nodeType}>
            {getNodeLabel(nodes.find(n => n.id === selectedNode)?.type || '')}
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
    const match = line.match(/^(MAIN|SYMPTOM|DIAGNOSIS|TREATMENT|COMPLICATION):\s*(.+)$/i)
    if (match) {
      const type = match[1].toLowerCase() as MapNode['type']
      const label = match[2].trim()
      const id = `node-${nodeCounter++}`
      
      // Better positioning - compact radial layout
      let x = 400, y = 250
      const typeIndex = nodes.filter(n => n.type === type).length
      
      switch (type) {
        case 'main':
          x = 400
          y = 250
          break
        case 'symptom':
          // Left side, stacked vertically
          x = 120 + (typeIndex % 2) * 100
          y = 100 + typeIndex * 55
          break
        case 'diagnosis':
          // Top right
          x = 600 + (typeIndex % 2) * 90
          y = 80 + typeIndex * 55
          break
        case 'treatment':
          // Bottom right
          x = 600 + (typeIndex % 2) * 90
          y = 350 + typeIndex * 50
          break
        case 'complication':
          // Bottom left
          x = 120 + (typeIndex % 2) * 100
          y = 380 + typeIndex * 50
          break
      }
      
      nodes.push({ id, label, type, x, y })
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
