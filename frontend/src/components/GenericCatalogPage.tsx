import { Link } from 'react-router-dom';

interface Entity {
  slug: string;
  name: string;
}

interface GenericCatalogPageProps {
  title: string;
  entityType: string;
  data: Entity[];
  headerActions?: React.ReactNode;   // элемент справа от заголовка
  children?: React.ReactNode;   // фильтры
}

const sortByName = (a: Entity, b: Entity) => a.name.localeCompare(b.name);

const groupByFirstLetter = (items: Entity[]) => {
  const groups: Record<string, Entity[]> = {};
  for (const item of items) {
    const firstChar = item.name.charAt(0).toUpperCase();
    if (!groups[firstChar]) groups[firstChar] = [];
    groups[firstChar].push(item);
  }
  const sortedLetters = Object.keys(groups).sort((a, b) => a.localeCompare(b));
  return { groups, sortedLetters };
};

const GenericCatalogPage: React.FC<GenericCatalogPageProps> = ({ 
  title, entityType, data, headerActions, children 
}) => {
  const sortedData = [...data].sort((a,b) => a.name.localeCompare(b.name));
  const { groups, sortedLetters } = groupByFirstLetter(sortedData);

  return (
    <div className="catalog-page">
      <div className="characters-list-container">
        <div className="catalog-header">
          <h1 className="catalog-title">{title}</h1>
          {headerActions && <div className="catalog-header-actions">{headerActions}</div>}
        </div>
        {sortedLetters.map(letter => (
          <div key={letter} className="letter-group">
            <h2 className="letter-header">{letter}</h2>
            <div className="names-grid">
              {groups[letter].map(item => (
                <Link key={item.slug} to={`/entity/${entityType}/${item.slug}`} className="character-link">
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
      <aside className="filters-sidebar">
        {children}
      </aside>
    </div>
  );
};

export default GenericCatalogPage;