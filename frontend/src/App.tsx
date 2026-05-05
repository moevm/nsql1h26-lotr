import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { FaChartColumn, FaMagnifyingGlassChart } from "react-icons/fa6";
import { SiRelay } from "react-icons/si";
import { FaUserCircle } from "react-icons/fa";
import { IoMdMore } from "react-icons/io";
import { BiSolidCategory } from "react-icons/bi";
import './App.css';
import HomePage from './pages/HomePage';
import CharactersPage from './pages/CharactersPage';
import RacesPage from './pages/RacesPage';
import LocationsPage from './pages/LocationsPage';
import EventsPage from './pages/EventsPage';
import OrganizationsPage from './pages/OrganizationsPage';
import TimelinesPage from './pages/TimelinesPage';
import ItemsPage from './pages/ItemsPage';
import LanguagesPage from './pages/LanguagesPage';
import ScriptsPage from './pages/ScriptsPage';
import CategoriesPage from './pages/CategoriesPage';
import AuthModal from './components/AuthModal';
import ProfilePage from './pages/ProfilePage';
import { useAuth, AuthProvider } from './context/AuthContext';
import EntityPage from './pages/EntityPage';
import EditPage from './pages/EditPage';
import CreatePage from './pages/CreatePage';
import AnalyticsPage from './pages/AnalyticsPage';
import GlobalStatsPage from './pages/GlobalStatsPage';
import CustomStatsPage from './pages/CustomStatsPage';
import SearchBar from './components/SearchBar';
import { ToastProvider } from './context/ToastContext';


// Компонент, который использует авторизацию
const AppContent: React.FC = () => {
  const { user } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);

  const handleProfileClick = () => {
    if (!user) {
      setShowAuthModal(true);
    }
  };

  return (
    <BrowserRouter>
      <div className="navbar">
        <Link to="/" className="logo-link">
          <img src="/logo.png" alt="LOTR Wiki" className="logo-img" />
        </Link>
        <SearchBar />
        <Link to="/categories" className="nav-btn">
          <div className="icon-with-text">
            <BiSolidCategory />
            Categories
          </div>
        </Link>
        <Link to="/analytics" className="nav-btn">
          <div className="icon-with-text">
            <SiRelay />
            Analytics
          </div>
        </Link>
        <Link to="/global-stats" className="nav-btn">
          <div className="icon-with-text">
            <FaChartColumn />
            Global statistics
          </div>
        </Link>
        <Link to="/custom-stats" className="nav-btn">
          <div className="icon-with-text">
            <FaMagnifyingGlassChart />
            Custom statistics
          </div>
        </Link>
        <Link to={user ? "/profile" : "#"} className="nav-btn" onClick={handleProfileClick}>
          <div className="icon-with-text">
            <FaUserCircle />
          </div>
        </Link>
        <button className="nav-btn">
          <div className="icon-with-text">
            <IoMdMore />
          </div>
        </button>
      </div>

      <div className="main-container">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/categories" element={<CategoriesPage />} />

          <Route path="/characters" element={<CharactersPage />} />
          <Route path="/races" element={<RacesPage />} />
          <Route path="/locations" element={<LocationsPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/organizations" element={<OrganizationsPage />} />
          <Route path="/timelines" element={<TimelinesPage />} />
          <Route path="/items" element={<ItemsPage />} />
          <Route path="/languages" element={<LanguagesPage />} />
          <Route path="/scripts" element={<ScriptsPage />} />
          <Route path="/create/:type" element={<CreatePage />} />

          <Route path="/pages/:slug" element={<EntityPage />} />
          <Route path="/edit/:slug" element={<EditPage />} />

          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/global-stats" element={<GlobalStatsPage />} />
          <Route path="/custom-stats" element={<CustomStatsPage />} />
        </Routes>
      </div>

      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => setShowAuthModal(false)}
        />
      )}
    </BrowserRouter>
  );
};

// Главный компонент
const App: React.FC = () => {
  return (
    <AuthProvider>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </AuthProvider>
  );
};

export default App;