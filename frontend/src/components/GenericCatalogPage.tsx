// src/components/GenericCatalogPage.tsx
import { Link } from 'react-router-dom';

interface Entity {
  slug: string;
  name: string;
  preview?: string[];
}

interface GenericCatalogPageProps {
  title: string;
  entityType: string;
  data: Entity[];
  headerActions?: React.ReactNode;
  children?: React.ReactNode;
}

const GenericCatalogPage: React.FC<GenericCatalogPageProps> = ({ 
  title, entityType, data, headerActions, children 
}) => {
  // Не сортируем и не группируем – используем порядок из props (уже отсортирован на бэкенде)
  return (
    <div className="catalog-page">
      <div className="characters-list-container">
        <div className="catalog-header">
          <h1 className="catalog-title">{title}</h1>
          {headerActions && <div className="catalog-header-actions">{headerActions}</div>}
        </div>
        <div className="cards-grid">
          {data.map(item => (
            <Link key={item.slug} to={`/entity/${entityType}/${item.slug}`} className="link-card-link">
              <div className="link-card">
                <div className="link-card-name">{item.name}</div>
                {item.preview && item.preview.length > 0 && (
                  <div className="link-card-preview">
                    {item.preview.map((attr, idx) => (
                      <div key={idx} className="preview-item">{attr}</div>
                    ))}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
      <aside className="filters-sidebar">
        {children}
      </aside>
    </div>
  );
};

export default GenericCatalogPage;