import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListItems } from '../api/generated/items/items';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const ItemsFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Категория">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Оружие</label>
          <label><input type="checkbox" disabled /> Артефакты</label>
          <label><input type="checkbox" disabled /> Броня</label>
          <label><input type="checkbox" disabled /> Еда</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Редкость">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Обычный</label>
          <label><input type="checkbox" disabled /> Легендарный</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-note">* Фильтры временно неактивны</div>
  </>
);

const ItemsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/items'] });
    };
  }, []);

  const { data, isLoading, error } = useListItems({ page: 1, page_size: 20 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(item => ({
    slug: item.slug,
    name: item.names?.[0] || 'Без имени',
  })) || [];

  const handleAddClick = () => {
    if (user) {
      navigate('/create/item');
    } else {
      setShowAuthModal(true);
    }
  };

  return (
    <>
      <GenericCatalogPage
        title="Items"
        entityType="item"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new item
          </button>
        }
      >
        <ItemsFilters />
      </GenericCatalogPage>
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/item');
          }}
        />
      )}
    </>
  );
};

export default ItemsPage;