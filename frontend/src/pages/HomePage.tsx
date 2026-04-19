import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <div className="home-page">
      <h1>The Lord of the Rings</h1>
      <h1>Wikipedia</h1>
      <div className="categories-list">
        <li><Link to="/characters">Characters</Link></li>
        <li><Link to="/races">Races</Link></li>
        <li><Link to="/locations">Locations</Link></li>
        <li><Link to="/events">Events</Link></li>
        <li><Link to="/organizations">Organizations</Link></li>
        <li><Link to="/timelines">Timelines</Link></li>
        <li><Link to="/items">Items</Link></li>
        <li><Link to="/languages">Languages</Link></li>
        <li><Link to="/scripts">Scripts</Link></li>
      </div>
    </div>
  );
};

export default HomePage;