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
  const [pendingCreation, setPendingCreation] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const page_size = 20;
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/items'] });
    };
  }, []);

  const { data, isLoading, error } = useListItems({ 
    page: 1, 
    page_size: page_size 
  });

  const response = data as any;
  const adaptedData = response?.results?.map((item: any) => {
    const previewItems: string[] = [];
    if (item.material && item.material.trim() !== '') {
      previewItems.push(`Material: ${item.material}`);
    }
    if (item.notable_for && item.notable_for.trim() !== '') {
      previewItems.push(`Notable for: ${item.notable_for}`);
    }
    // Ограничим первыми 2
    const preview = previewItems.slice(0, 2);
    return {
      slug: item.slug,
      name: item.names?.[0] || 'Без имени',
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
      navigate('/create/item');
    } else {
      alert('Только администраторы могут создавать новые сущности.');
    }
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') {
        navigate('/create/item');
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

export default ItemsPage;