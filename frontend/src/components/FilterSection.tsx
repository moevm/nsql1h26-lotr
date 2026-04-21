import { useState } from 'react';
import { FaChevronDown, FaChevronRight } from 'react-icons/fa';

interface FilterSectionProps {
  title: string;
  children: React.ReactNode;
}

const FilterSection: React.FC<FilterSectionProps> = ({ title, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="filter-section">
      <div className={`filter-header ${isOpen ? 'open' : ''}`} onClick={() => setIsOpen(!isOpen)}>
        <span>{isOpen ? <FaChevronDown size="1em" /> : <FaChevronRight size="1em" />}</span>
        <h3>{title}</h3>
      </div>
      {isOpen && <div className="filter-content">{children}</div>}
    </div>
  );
};

export default FilterSection;