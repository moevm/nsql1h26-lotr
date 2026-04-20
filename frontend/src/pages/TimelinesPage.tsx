import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListTimelines } from '../api/generated/timelines/timelines';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';

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

  const { data, isLoading, error } = useListTimelines({ page: 1, page_size: 100 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(timeline => ({
    slug: timeline.slug,
    name: timeline.names?.[0] || 'Без имени',
  })) || [];

  const handleAddClick = () => {
    if (user) {
      navigate('/create/timeline');
    } else {
      setShowAuthModal(true);
    }
  };

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
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/timeline');
          }}
        />
      )}
    </>
  );
};

export default TimelinesPage;