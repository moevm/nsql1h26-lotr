import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FaChevronRight, FaChevronDown } from 'react-icons/fa';
import { mockCategoriesTree } from '../mocks/categoriesTree';
import { mockCategoryEntities } from '../mocks/categoryEntities';

interface CategoryNode {
  slug: string;
  name: string;
  pageCount: number;
  children: CategoryNode[];
}

interface EntityPreview {
  slug: string;
  type: string;
  name: string;
  imageUrl: string;
}

// Компонент дерева категорий
const CategoryTree: React.FC<{
  nodes: CategoryNode[];
  selectedSlug: string | null;
  onSelect: (slug: string) => void;
  expanded: Record<string, boolean>;
  onToggleExpand: (slug: string) => void;
}> = ({ nodes, selectedSlug, onSelect, expanded, onToggleExpand }) => {
  return (
    <ul className="category-tree-root">
      {nodes.map(node => (
        <li key={node.slug} className="category-tree-node">
          <div className={`category-tree-item ${selectedSlug === node.slug ? 'selected' : ''}`}>
            {node.children.length > 0 && (
              <span className="expand-icon" onClick={() => onToggleExpand(node.slug)}>
                {expanded[node.slug] ? <FaChevronDown size="12px" /> : <FaChevronRight size="12px" />}
              </span>
            )}
            <span className="category-name" onClick={() => onSelect(node.slug)}>
                {node.name}
            </span>
          </div>
          {node.children.length > 0 && expanded[node.slug] && (
            <CategoryTree
              nodes={node.children}
              selectedSlug={selectedSlug}
              onSelect={onSelect}
              expanded={expanded}
              onToggleExpand={onToggleExpand}
            />
          )}
        </li>
      ))}
    </ul>
  );
};

// Группировка сущностей по первой букве
const groupByFirstLetter = (entities: EntityPreview[]) => {
  const groups: Record<string, EntityPreview[]> = {};
  for (const entity of entities) {
    const firstChar = entity.name.charAt(0).toUpperCase();
    if (!groups[firstChar]) groups[firstChar] = [];
    groups[firstChar].push(entity);
  }
  const sortedLetters = Object.keys(groups).sort((a, b) => a.localeCompare(b));
  return { groups, sortedLetters };
};

const CategoriesPage: React.FC = () => {
  const [tree, setTree] = useState<CategoryNode[]>([]);
  const [loadingTree, setLoadingTree] = useState(true);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<any>(null);
  const [loadingEntities, setLoadingEntities] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Загружаем дерево категорий (моки)
  useEffect(() => {
    setTimeout(() => {
      setTree(mockCategoriesTree);
      setLoadingTree(false);
      // Раскрываем корневые категории по умолчанию
      const initialExpanded: Record<string, boolean> = {};
      mockCategoriesTree.forEach(root => {
        initialExpanded[root.slug] = true;
      });
      setExpanded(initialExpanded);
      // Если есть корневая категория, выбираем первую для отображения
      if (mockCategoriesTree.length > 0) {
        setSelectedSlug(mockCategoriesTree[0].slug);
      }
    }, 300);
  }, []);

  // Загружаем сущности выбранной категории
  useEffect(() => {
    if (!selectedSlug) {
      setSelectedCategory(null);
      return;
    }
    setLoadingEntities(true);
    setTimeout(() => {
      const data = mockCategoryEntities[selectedSlug];
      if (data) {
        setSelectedCategory(data);
      } else {
        setSelectedCategory({
          name: selectedSlug,
          description: null,
          pages: { results: [] }
        });
      }
      setLoadingEntities(false);
    }, 300);
  }, [selectedSlug]);

  const handleSelectCategory = (slug: string) => {
    setSelectedSlug(slug);
  };

  const handleToggleExpand = (slug: string) => {
    setExpanded(prev => ({ ...prev, [slug]: !prev[slug] }));
  };

  // Группируем сущности для алфавитного отображения
  const entities = selectedCategory?.pages?.results || [];
  const { groups, sortedLetters } = groupByFirstLetter(entities);

  if (loadingTree) return <div className="loader">Загрузка категорий...</div>;

  return (
    <div className="catalog-page">
      {/* Левая часть: список сущностей выбранной категории */}
      <div className="characters-list-container">
        {!selectedSlug && (
          <div className="catalog-header">
            <h1 className="catalog-title">Категории</h1>
            <p>Выберите категорию справа</p>
          </div>
        )}

        {selectedSlug && loadingEntities && <div className="loader">Загрузка...</div>}

        {selectedCategory && !loadingEntities && (
          <>
            <div className="catalog-header">
              <h1 className="catalog-title">{selectedCategory.name}</h1>
            </div>

            {entities.length === 0 && <p>В этой категории пока нет сущностей.</p>}

            {sortedLetters.map(letter => (
              <div key={letter} className="letter-group">
                <h2 className="letter-header">{letter}</h2>
                <div className="names-grid">
                  {groups[letter].map(entity => (
                    <Link
                      key={entity.slug}
                      to={`/entity/${entity.type}/${entity.slug}`}
                      className="character-link"
                    >
                      {entity.name}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Правая часть: дерево категорий */}
      <aside className="filters-sidebar">
        <h2 className="filters-main-title">Категории</h2>
        <div className="filter-card">
          <CategoryTree
            nodes={tree}
            selectedSlug={selectedSlug}
            onSelect={handleSelectCategory}
            expanded={expanded}
            onToggleExpand={handleToggleExpand}
          />
        </div>
      </aside>
    </div>
  );
};

export default CategoriesPage;