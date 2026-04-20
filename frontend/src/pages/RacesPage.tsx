import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListRaces } from '../api/generated/races/races';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';

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

  const { data, isLoading, error } = useListRaces({ page: 1, page_size: 100 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(race => {
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

  const handleAddClick = () => {
    if (user) {
      navigate('/create/race');
    } else {
      setShowAuthModal(true);
    }
  };

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
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/race');
          }}
        />
      )}
    </>
  );
};

export default RacesPage;