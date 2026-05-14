import { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaProjectDiagram, FaRoute } from 'react-icons/fa';

interface AnalyticsDropdownProps {
  isOpen: boolean;
  onClose: () => void;
}

const AnalyticsDropdown: React.FC<AnalyticsDropdownProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  const handleGraph = () => {
    onClose();
    navigate('/analytics/graph');
  };

  const handleShortestPath = () => {
    onClose();
    navigate('/analytics/shortest-path');
  };

  if (!isOpen) return null;

  return (
    <div className="dropdown-menu" ref={menuRef}>
      <button onClick={handleGraph} className="dropdown-item">
        <FaProjectDiagram /> Graph
      </button>
      <button onClick={handleShortestPath} className="dropdown-item">
        <FaRoute /> Shortest path
      </button>
    </div>
  );
};

export default AnalyticsDropdown;