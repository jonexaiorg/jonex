import React from 'react'
import KnowledgeGraphPanel from '@/components/KnowledgeGraphPanel'

interface GraphTabProps {
  kbId: string
}

const GraphTab: React.FC<GraphTabProps> = ({ kbId }) => {
  return <KnowledgeGraphPanel kbId={kbId} />
}

export default GraphTab
