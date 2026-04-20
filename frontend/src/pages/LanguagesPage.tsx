import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListLanguages } from '../api/generated/languages/languages';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const LanguagesFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Языковая семья">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Эльфийские</label>
          <label><input type="checkbox" disabled /> Гномьи</label>
          <label><input type="checkbox" disabled /> Людские</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const LanguagesPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/languages'] });
    };
  }, []);

  const { data, isLoading, error } = useListLanguages({ page: 1, page_size: 20 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(lang => ({
    slug: lang.slug,
    name: lang.names?.[0] || 'Без имени',
  })) || [];

  const handleAddClick = () => {
    if (user) {
      navigate('/create/language');
    } else {
      setShowAuthModal(true);
    }
  };

  return (
    <>
      <GenericCatalogPage
        title="Languages"
        entityType="language"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new language
          </button>
        }
      >
        <LanguagesFilters />
      </GenericCatalogPage>
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/language');
          }}
        />
      )}
    </>
  );
};

export default LanguagesPage;