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
  const [pendingCreation, setPendingCreation] = useState(false);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const page_size = 20;
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/languages'] });
    };
  }, []);

  const { data, isLoading, error } = useListLanguages({ 
    page: 1, 
    page_size: page_size 
  });

  const response = data as any;
  const adaptedData = response?.results?.map((lang: any) => {
    const previewItems: string[] = [];
    if (lang.family && lang.family.trim() !== '') {
      previewItems.push(`Family: ${lang.family}`);
    }
    const preview = previewItems.slice(0, 1);
    return {
      slug: lang.slug,
      name: lang.names?.[0] || 'Без имени',
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
      navigate('/create/language');
    } else {
      alert('Только администраторы могут создавать новые сущности.');
    }
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') {
        navigate('/create/language');
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

export default LanguagesPage;