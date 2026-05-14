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
import GlobalStatsPage from './pages/GlobalStatsPage';
import CustomStatsPage from './pages/CustomStatsPage';
import SearchBar from './components/SearchBar';
import { ToastProvider } from './context/ToastContext';
import AdminDropdown from './components/AdminDropdown';
import ErrorModal from './components/ErrorModal';
import AdminPanelPage from './pages/AdminPanelPage';
import PublicProfilePage from './pages/PublicProfilePage';
import AnalyticsDropdown from './components/AnalyticsDropdown';
import GraphPage from './pages/GraphPage';
import ShortestPathPage from './pages/ShortestPathPage';

// Компонент, который использует авторизацию
const AppContent: React.FC = () => {
  const { user } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [errorModal, setErrorModal] = useState<{ message: string; statusCode?: number } | null>(null);
  const [isAnalyticsDropdownOpen, setIsAnalyticsDropdownOpen] = useState(false);

  const handleAnalyticsClick = () => {
    setIsAnalyticsDropdownOpen(prev => !prev);
  };
  const closeAnalyticsDropdown = () => setIsAnalyticsDropdownOpen(false);

  const showError = (message: string, statusCode?: number) => {
    setErrorModal({ message, statusCode });
  };

  const handleProfileClick = () => {
    if (!user) {
      setShowAuthModal(true);
    }
  };

  const handleMoreClick = () => {
    if (user?.role === 'admin') {
      setIsDropdownOpen(prev => !prev);
    }
  };

  const closeDropdown = () => setIsDropdownOpen(false);

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
        <div className="nav-btn more-btn-wrapper" onClick={handleAnalyticsClick}>
          <div className="icon-with-text">
            <SiRelay />
            Analytics
          </div>
          <AnalyticsDropdown isOpen={isAnalyticsDropdownOpen} onClose={closeAnalyticsDropdown} />
        </div>
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
        {user?.role === 'admin' && (
          <div className="nav-btn more-btn-wrapper" onClick={handleMoreClick}>
            <div className="icon-with-text">
              <IoMdMore />
            </div>
            {isDropdownOpen && <AdminDropdown isOpen={isDropdownOpen} onClose={closeDropdown} onError={showError}/>}
          </div>
        )}
      </div>

      <div className="main-container">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/categories" element={<CategoriesPage />} />
          <Route path="/categories/:slug" element={<CategoriesPage />} />

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
          <Route path="/global-stats" element={<GlobalStatsPage />} />
          <Route path="/custom-stats" element={<CustomStatsPage />} />
          <Route path="/admin" element={<AdminPanelPage />} />
          <Route path="/users/:username" element={<PublicProfilePage />} />
          <Route path="/analytics/graph" element={<GraphPage />} />
          <Route path="/analytics/shortest-path" element={<ShortestPathPage />} />
        </Routes>
      </div>

      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => setShowAuthModal(false)}
        />
      )}
      {errorModal && (
        <ErrorModal
          message={errorModal.message}
          statusCode={errorModal.statusCode}
          onClose={() => setErrorModal(null)}
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