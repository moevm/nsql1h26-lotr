import { useParams, useNavigate, Link } from 'react-router-dom';
import { useListCategories, useGetCategory } from '../api/generated/categories/categories';
import type { CategoryListItem, CategoryDetail } from '../api/generated/models';

// Компонент для отображения списка корневых категорий
const RootCategoriesList: React.FC<{ onSelectCategory: (slug: string) => void }> = ({ onSelectCategory }) => {
  const { data, isLoading, error } = useListCategories({ parent: 'root', page_size: 100 });
  if (isLoading) return <div className="loader">Loading categories...</div>;
  if (error) return <div className="error">Failed to load categories.</div>;
  const categories = data?.results || [];
  return (
    <ul className="root-categories-list">
      {categories.map((cat: CategoryListItem) => (
        <li key={cat.slug} className="root-category-item" onClick={() => onSelectCategory(cat.slug)}>
          <div className="root-category-name">{cat.name}</div>
        </li>
      ))}
    </ul>
  );
};

// Компонент детальной страницы категории
const CategoryDetailView: React.FC<{ slug: string }> = ({ slug }) => {
  const navigate = useNavigate();
  const { data, isLoading, error } = useGetCategory(slug, { page: 1, page_size: 20 });
  if (isLoading) return <div className="loader">Loading category...</div>;
  if (error) return <div className="error">Category not found.</div>;
  const category = data as CategoryDetail;

  const handleBack = () => {
    if (category.parent_slug) {
      navigate(`/categories/${category.parent_slug}`);
    } else {
      navigate('/categories');
    }
  };

  const handleSubcategoryClick = (subSlug: string) => {
    navigate(`/categories/${subSlug}`);
  };

  return (
    <div className="category-detail">
      <div className="category-header">
        <button className="back-button" onClick={handleBack}>← Back</button>
        <h1>{category.name}</h1>
      </div>
      {category.description && <p className="category-description">{category.description}</p>}

      {/* Подкатегории – простой список ссылок */}
      {category.children && category.children.length > 0 && (
        <div className="category-children-section">
          <h2>Subcategories</h2>
          <ul className="subcategories-list">
            {category.children.map((child) => (
              <li key={child.slug}>
                <button className="category-link" onClick={() => handleSubcategoryClick(child.slug)}>
                  {child.name}
                </button>
                <span className="badge">({child.page_count} pages)</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Страницы – простой список ссылок */}
      {category.pages && category.pages.results && category.pages.results.length > 0 && (
        <div className="category-pages-section">
          <h2>Pages</h2>
          <ul className="pages-list">
            {category.pages.results.map((page) => (
              <li key={page.slug}>
                <Link to={`/pages/${page.slug}`} className="page-link">
                  {page.name}
                </Link>
              </li>
            ))}
          </ul>
          {/* Пагинацию можно добавить позже */}
        </div>
      )}

      {(!category.children || category.children.length === 0) && (!category.pages?.results?.length) && (
        <p>No subcategories or pages found</p>
      )}
    </div>
  );
};

const CategoriesPage: React.FC = () => {
  const { slug } = useParams<{ slug?: string }>();
  const navigate = useNavigate();

  const handleSelectCategory = (categorySlug: string) => {
    navigate(`/categories/${categorySlug}`);
  };

  if (slug) {
    return <CategoryDetailView slug={slug} />;
  } else {
    return (
      <div className="categories-root-page">
        <h1 className="catalog-title">Categories</h1>
        <RootCategoriesList onSelectCategory={handleSelectCategory} />
      </div>
    );
  }
};

export default CategoriesPage;