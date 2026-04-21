import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListTimelines } from '../api/generated/timelines/timelines';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const TimelinesFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Эпоха">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Первая</label>
          <label><input type="checkbox" disabled /> Вторая</label>
          <label><input type="checkbox" disabled /> Третья</label>
          <label><input type="checkbox" disabled /> Четвёртая</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Длительность">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Менее 100 лет</label>
          <label><input type="checkbox" disabled /> 100–500 лет</label>
          <label><input type="checkbox" disabled /> Более 500 лет</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const TimelinesPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingCreation, setPendingCreation] = useState(false);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const page_size = 20;
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/timelines'] });
    };
  }, []);

  const { data, isLoading, error } = useListTimelines({ 
    page: 1, 
    page_size: page_size 
  });

  const response = data as any;
  const adaptedData = response?.results?.map((timeline: any) => {
    const previewItems: string[] = [];
    if (timeline.abbreviation && timeline.abbreviation.trim() !== '') {
      previewItems.push(`Abbreviation: ${timeline.abbreviation}`);
    }
    if (timeline.start_date && timeline.start_date.trim() !== '') {
      previewItems.push(`Start date: ${timeline.start_date}`);
    }
    if (timeline.end_date && timeline.end_date.trim() !== '') {
      previewItems.push(`End date: ${timeline.end_date}`);
    }
    // Ограничим первыми 3
    const preview = previewItems.slice(0, 3);
    return {
      slug: timeline.slug,
      name: timeline.names?.[0] || 'Без имени',
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
      navigate('/create/timeline');
    } else {
      alert('Только администраторы могут создавать новые сущности.');
    }
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') {
        navigate('/create/timeline');
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
        title="Времена и эпохи"
        entityType="timeline"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Добавить эпоху
          </button>
        }
      >
        <TimelinesFilters />
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

export default TimelinesPage;