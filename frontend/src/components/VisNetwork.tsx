import { useEffect, useRef } from 'react';
import { Network } from 'vis-network';

interface VisNetworkProps {
  nodes: Array<{ id: string; label: string; [key: string]: any }>;
  edges: Array<{ from: string; to: string; label?: string; [key: string]: any }>;
  options?: any;
}

const VisNetwork: React.FC<VisNetworkProps> = ({ nodes, edges, options }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    if (!networkRef.current) {
      const data = { nodes, edges };
      networkRef.current = new Network(containerRef.current, data, options);
    } else {
      // Обновляем данные без пересоздания сети
      networkRef.current.setData({ nodes, edges });
    }
  }, [nodes, edges, options]);

  return <div ref={containerRef} style={{ height: '100%', width: '100%' }} />;
};

export default VisNetwork;