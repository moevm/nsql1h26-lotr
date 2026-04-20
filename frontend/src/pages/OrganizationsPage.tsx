import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListOrganizations } from '../api/generated/organizations/organizations';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';

const OrganizationsFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Тип организации">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Братство</label>
          <label><input type="checkbox" disabled /> Совет</label>
          <label><input type="checkbox" disabled /> Собрание</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const OrganizationsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);

  const { data, isLoading, error } = useListOrganizations({ page: 1, page_size: 100 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(org => ({
    slug: org.slug,
    name: org.names?.[0] || 'Без имени',
  })) || [];

  const handleAddClick = () => {
    if (user) {
      navigate('/create/organization');
    } else {
      setShowAuthModal(true);
    }
  };

  return (
    <>
      <GenericCatalogPage
        title="Organizations"
        entityType="organization"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new organization
          </button>
        }
      >
        <OrganizationsFilters />
      </GenericCatalogPage>
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/organization');
          }}
        />
      )}
    </>
  );
};

export default OrganizationsPage;