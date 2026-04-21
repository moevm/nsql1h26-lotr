import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListRaces } from '../api/generated/races/races';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const RacesFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Продолжительность жизни">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Бессмертные</label>
          <label><input type="checkbox" disabled /> 100-200 лет</label>
          <label><input type="checkbox" disabled /> 70-100 лет</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Отличительные черты">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Маленький рост</label>
          <label><input type="checkbox" disabled /> Бородатые</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const RacesPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingCreation, setPendingCreation] = useState(false);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const page_size = 20;
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/races'] });
    };
  }, []);

  const { data, isLoading, error } = useListRaces({ 
    page: 1, 
    page_size: page_size 
  });

  const response = data as any;
  const adaptedData = response?.results?.map((race: any) => {
    const previewItems: string[] = [];
    if (race.lifespan && race.lifespan.trim() !== '') {
      previewItems.push(`Lifespan: ${race.lifespan}`);
    }
    if (race.distinctions && race.distinctions.trim() !== '') {
      previewItems.push(`Distinctions: ${race.distinctions}`);
    }
    if (race.avg_height && race.avg_height.trim() !== '') {
      previewItems.push(`Average height: ${race.avg_height}`);
    }
    // Ограничим первыми 3
    const preview = previewItems.slice(0, 3);
    return {
      slug: race.slug,
      name: race.names?.[0] || 'Без имени',
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
      navigate('/create/race');
    } else {
      alert('Только администраторы могут создавать новые сущности.');
    }
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') {
        navigate('/create/race');
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
        title="Races"
        entityType="race"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new race
          </button>
        }
      >
        <RacesFilters />
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

export default RacesPage;