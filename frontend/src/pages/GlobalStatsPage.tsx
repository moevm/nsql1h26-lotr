import { useGlobalStats } from '../api/generated/analytics/analytics';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { Link } from 'react-router-dom';


const GlobalStatsPage: React.FC = () => {
  const { data, isLoading, error } = useGlobalStats();

  if (isLoading) return <div className="loader">Loading statistics...</div>;
  if (error) return <div className="error">Failed to load statistics.</div>;
  if (!data) return null;

  const counts = data.counts;
  const charactersByRace = data.characters_by_race || [];
  const charactersByGender = data.characters_by_gender || [];
  const isAliveStats = data.is_alive_stats;
  const eventsByTimeline = data.events_by_timeline || [];
  const locationsByType = data.locations_by_type || [];
  const itemsByType = data.items_by_type || [];
  const topConnected = data.top_connected;
  const mostLiked = data.most_liked || [];
  const mostCommented = data.most_commented || [];

  // Функция для рендера столбчатой диаграммы
  const renderBarChart = (data: any[], nameKey: string, valueKey: string, title: string) => (
    <div className="distribution-item">
      <h3>{title}</h3>
      <div className="chart-with-legend">
        <div className="chart-container" style={{ height: '300px', width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#555" />
              <XAxis dataKey={nameKey} angle={-45} textAnchor="end" height={80} interval={0} tick={{ fill: '#f5e7d9', fontSize: 12 }} />
              <YAxis tick={{ fill: '#f5e7d9' }} />
              <Tooltip contentStyle={{ backgroundColor: '#2c2a28', border: 'none', borderRadius: '8px' }} />
              <Bar dataKey={valueKey} fill="#805b38" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="legend-container">
          {data.map((item, idx) => (
            <div key={idx} className="legend-item">
              <span className="legend-label">{item[nameKey]}:</span>
              <span className="legend-value">{item[valueKey]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Специальный случай для isAliveStats (два значения)
  const aliveData = [
    { name: 'Alive', value: isAliveStats?.alive || 0 },
    { name: 'Deceased', value: isAliveStats?.deceased || 0 },
  ];

  return (
    <div className="global-stats-page">
      <h1 className="global-stats-title">Global Statistics</h1>

      {/* General statistics */}
      <section className="stats-section">
        <h2>General statistics</h2>
        <div className="stats-grid">
          <div className="stat-item"><span>Total entities:</span> <strong>{counts.total}</strong></div>
          <div className="stat-item"><span>Characters:</span> <strong>{counts.characters}</strong></div>
          <div className="stat-item"><span>Races:</span> <strong>{counts.races}</strong></div>
          <div className="stat-item"><span>Locations:</span> <strong>{counts.locations}</strong></div>
          <div className="stat-item"><span>Events:</span> <strong>{counts.events}</strong></div>
          <div className="stat-item"><span>Organizations:</span> <strong>{counts.organizations}</strong></div>
          <div className="stat-item"><span>Timelines:</span> <strong>{counts.timelines}</strong></div>
          <div className="stat-item"><span>Items:</span> <strong>{counts.items}</strong></div>
          <div className="stat-item"><span>Languages:</span> <strong>{counts.languages}</strong></div>
          <div className="stat-item"><span>Scripts:</span> <strong>{counts.scripts}</strong></div>
        </div>
      </section>

      {/* Distributions – все столбчатые диаграммы */}
      <section className="stats-section">
        <h2>Distributions</h2>
        <div className="distribution-list">
          {charactersByRace.length > 0 && renderBarChart(charactersByRace, 'name', 'count', 'Characters by race')}
          {charactersByGender.length > 0 && renderBarChart(charactersByGender, 'gender', 'count', 'Characters by gender')}
          {isAliveStats && renderBarChart(aliveData, 'name', 'value', 'Alive vs Deceased')}
          {eventsByTimeline.length > 0 && renderBarChart(eventsByTimeline, 'name', 'count', 'Events by timeline')}
          {locationsByType.length > 0 && renderBarChart(locationsByType, 'type', 'count', 'Locations by type')}
          {itemsByType.length > 0 && renderBarChart(itemsByType, 'type', 'count', 'Items by type')}
        </div>
      </section>

      {/* Top connected entities */}
      <section className="stats-section">
        <h2>Top connected entities</h2>
        <div className="top-connected-grid">
          {topConnected?.characters?.length > 0 && (
            <div className="top-card">
              <h3>Characters</h3>
              <ol>
                {topConnected.characters.slice(0, 5).map((item, idx) => (
                  <li key={idx}>
                    <Link to={`/pages/${item.slug}`}>
                      <strong>{item.name} </strong>
                    </Link>
                    ({item.connections_count} relations)
                  </li>
                ))}
              </ol>
            </div>
          )}
          {topConnected?.locations?.length > 0 && (
            <div className="top-card">
              <h3>Locations</h3>
              <ol>
                {topConnected.locations.slice(0, 5).map((item, idx) => (
                  <li key={idx}>
                    <Link to={`/pages/${item.slug}`}>
                      <strong>{item.name} </strong>
                    </Link>
                    ({item.connections_count} relations)
                  </li>
                ))}
              </ol>
            </div>
          )}
          {topConnected?.events?.length > 0 && (
            <div className="top-card">
              <h3>Events</h3>
              <ol>
                {topConnected.events.slice(0, 5).map((item, idx) => (
                  <li key={idx}>
                    <Link to={`/pages/${item.slug}`}>
                      <strong>{item.name} </strong>
                    </Link>
                    ({item.connections_count} relations)
                  </li>
                ))}
              </ol>
            </div>
          )}
          {topConnected?.organizations?.length > 0 && (
            <div className="top-card">
              <h3>Organizations</h3>
              <ol>
                {topConnected.organizations.slice(0, 5).map((item, idx) => (
                  <li key={idx}>
                    <Link to={`/pages/${item.slug}`}>
                      <strong>{item.name} </strong>
                    </Link>
                    ({item.connections_count} relations)
                  </li>
                ))}
              </ol>
            </div>
          )}
          {topConnected?.items?.length > 0 && (
            <div className="top-card">
              <h3>Items</h3>
              <ol>
                {topConnected.items.slice(0, 5).map((item, idx) => (
                  <li key={idx}>
                    <Link to={`/pages/${item.slug}`}>
                      <strong>{item.name} </strong>
                    </Link>
                    ({item.connections_count} relations)
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </section>

      {/* Most liked and most commented */}
      <section className="stats-section">
        <h2>Most liked and most commented</h2>
        <div className="two-columns">
          <div className="top-card">
            <h3>Most liked pages</h3>
            <ol>
              {mostLiked.slice(0, 5).map((item, idx) => (
                <li key={idx}>
                  <Link to={`/pages/${item.slug}`}>
                    <strong>{item.name} </strong>
                  </Link>
                  ({item.type}) – {item.count} likes
                </li>
              ))}
            </ol>
          </div>
          <div className="top-card">
            <h3>Most commented pages</h3>
            <ol>
              {mostCommented.slice(0, 5).map((item, idx) => (
                <li key={idx}>
                  <Link to={`/pages/${item.slug}`}>
                    <strong>{item.name}</strong>
                  </Link>
                  ({item.type}) – {item.count} comments
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>
    </div>
  );
};

export default GlobalStatsPage;