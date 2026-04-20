import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListScripts } from '../api/generated/scripts/scripts';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';

const ScriptsFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Тип письменности">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Эльфийские</label>
          <label><input type="checkbox" disabled /> Гномьи</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const ScriptsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);

  const { data, isLoading, error } = useListScripts({ page: 1, page_size: 100 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(script => ({
    slug: script.slug,
    name: script.names?.[0] || 'Без имени',
  })) || [];

  const handleAddClick = () => {
    if (user) {
      navigate('/create/script');
    } else {
      setShowAuthModal(true);
    }
  };

  return (
    <>
      <GenericCatalogPage
        title="Scripts"
        entityType="script"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new script
          </button>
        }
      >
        <ScriptsFilters />
      </GenericCatalogPage>
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/script');
          }}
        />
      )}
    </>
  );
};

export default ScriptsPage;