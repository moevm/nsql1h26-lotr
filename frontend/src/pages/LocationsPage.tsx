import GenericCatalogPage from '../components/GenericCatalogPage';
import { useNavigate } from 'react-router-dom';
import { useListLocations } from '../api/generated/locations/locations';
import { FaPlus } from 'react-icons/fa';
import { useState } from 'react';
import FilterSection from '../components/FilterSection';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const LocationsFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Регион">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Эриадор</label>
          <label><input type="checkbox" disabled /> Гондор</label>
          <label><input type="checkbox" disabled /> Рохан</label>
          <label><input type="checkbox" disabled /> Мордор</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Тип">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Город</label>
          <label><input type="checkbox" disabled /> Крепость</label>
          <label><input type="checkbox" disabled /> Лес</label>
          <label><input type="checkbox" disabled /> Горы</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const LocationsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingCreation, setPendingCreation] = useState(false);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const page_size = 20;
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/locations'] });
    };
  }, []);

  const { data, isLoading, error } = useListLocations({
    page: 1,
    page_size: page_size,
  });

  // Адаптируем данные
  const response = data as any;
  const adaptedData = response?.results?.map((location: any) => {
    const previewItems: string[] = [];
    if (location.population && location.population.trim() !== '') {
      previewItems.push(`Population: ${location.population}`);
    }
    if (location.creation_date && location.creation_date.trim() !== '') {
      previewItems.push(`Creation date: ${location.creation_date}`);
    }
    if (location.notable_for && location.notable_for.trim() !== '') {
      previewItems.push(`Notable for: ${location.notable_for}`);
    }
    // Ограничим первыми 3
    const preview = previewItems.slice(0, 3);
    return {
      slug: location.slug,
      name: location.names?.[0] || 'Без имени',
      preview,
    };
  }) || [];

  const totalCount = response?.count || 0;
  const hasPrev = response?.previous !== null;
  const hasNext = response?.next !== null;

  const handlePrevPage = () => {
    if (hasPrev) setPage(p => p - 1);
  };
  const handleNextPage = () => {
    if (hasNext) setPage(p => p + 1);
  };

  const handleAddClick = () => {
    if (!user) {
      setShowAuthModal(true);
      setPendingCreation(true);
      return;
    }
    if (user.role === 'admin') {
      navigate('/create/location');
    } else {
      alert('Только администраторы могут создавать новые сущности.');
    }
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') {
        navigate('/create/location');
      } else {
        alert('Только администраторы могут создавать новые сущности.');
      }
      setPendingCreation(false);
    }
  }, [user, pendingCreation, navigate]);

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  return (
    <>
      <GenericCatalogPage
        title="Locations"
        entityType="location"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new location
          </button>
        }
      >
        <LocationsFilters />
      </GenericCatalogPage>

      <div className="pagination-container">
        <button
          className="pagination-btn"
          onClick={handlePrevPage}
          disabled={!hasPrev || isLoading}
        >
          ← Previous
        </button>
        <span className="pagination-info">
          Page {page} (total: {Math.ceil(totalCount / page_size)})
        </span>
        <button
          className="pagination-btn"
          onClick={handleNextPage}
          disabled={!hasNext || isLoading}
        >
          Next →
        </button>
      </div>

      {showAuthModal && (
        <AuthModal
          onClose={() => {
            setShowAuthModal(false);
            setPendingCreation(false);
          }}
          onSuccess={() => {
            setShowAuthModal(false);
          }}
        />
      )}
    </>
  );
};

export default LocationsPage;