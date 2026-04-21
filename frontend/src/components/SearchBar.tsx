import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { axiosInstance } from '../api/axios-instance';

interface SearchResult {
  slug: string;
  type: string;
  name: string;
  image_url: string;
}

const SearchBar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();
  const searchRef = useRef<HTMLDivElement>(null);

  // Обработка клика вне области поиска для закрытия дропдауна
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounce для поиска
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      if (query.length >= 2) {
        performSearch();
      } else {
        setResults([]);
        setShowDropdown(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [query]);

  const performSearch = async () => {
    setIsLoading(true);
    try {
      const response = await axiosInstance.get('/search', {
        params: { q: query, limit: 10 },
      });
      setResults(response.data);
      setShowDropdown(true);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResultClick = (result: SearchResult) => {
    setQuery('');
    setShowDropdown(false);
    navigate(`/entity/${result.type}/${result.slug}`);
  };

  return (
    <div ref={searchRef} className="search-container">
      <input
        type="text"
        className="search"
        placeholder="Search..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => query.length >= 2 && results.length > 0 && setShowDropdown(true)}
      />
      {showDropdown && (
        <div className="search-dropdown">
          {isLoading && <div className="search-loading">Loading...</div>}
          {!isLoading && results.length === 0 && query.length >= 2 && (
            <div className="search-no-results">No results</div>
          )}
          {results.map((result) => (
            <div
              key={result.slug}
              className="search-result-item"
              onClick={() => handleResultClick(result)}
            >
              {result.image_url && <img src={result.image_url} alt={result.name} className="search-result-image" />}
              <div className="search-result-info">
                <div className="search-result-name">{result.name}</div>
                <div className="search-result-type">{result.type}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBar;