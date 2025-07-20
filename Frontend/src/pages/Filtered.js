import React, { useEffect, useState } from 'react';
import './Filtered.css';
import LoadingScreen from './LoadingScreen';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '';

function Filtered({ user }) {
  const [data, setData] = useState(null);
  const [prevCount, setPrevCount] = useState(0);
  const [showNotification, setShowNotification] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");

  const [seenIds, setSeenIds] = useState(new Set());
  const [newlyAddedIds, setNewlyAddedIds] = useState(new Set());
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  const access = localStorage.getItem('access');

  const columnMap = {
    consultation_id: 'ID Consultation',
    client: 'Client',
    intitule_projet: 'Intitulé du projet',
    lien: 'Lien',
    source: 'Source',
  };

  // Fetch filtered data
  const fetchFilteredData = () => {
    axios.get(`${API_BASE}/sorter/api/filtered_data/`)
      .then(res => {
        const newData = res.data;
        const newIdsSet = new Set(newData.map(row => row.consultation_id));
        if (isInitialLoad) {
          setSeenIds(newIdsSet);
          setIsInitialLoad(false);
          setNewlyAddedIds(new Set());
        } else {
          const addedIds = new Set([...newIdsSet].filter(id => !seenIds.has(id)));
          setNewlyAddedIds(addedIds);
          setSeenIds(newIdsSet);
          setTimeout(() => setNewlyAddedIds(new Set()), 300_000);
        }
        setData(newData);
        setPrevCount(newData.length);
        if (!isInitialLoad && newData.length > prevCount) {
          setShowNotification(true);
        }
      })
      .catch(err => {
        console.error('Error fetching data:', err);
        setData([]);
      });
  };

  // Fetch keywords
  const fetchKeywords = async () => {
    try {
      const res = await axios.get(`${API_BASE}/sorter/api/keywords/`, {
        headers: access ? { Authorization: `Bearer ${access}` } : {},
      });
      setKeywords(res.data);
    } catch (err) {
      console.error('Error fetching keywords:', err);
      setKeywords([]);
    }
  };

  // On mount: fetch and start auto-refresh
  useEffect(() => {
    fetchFilteredData();
    fetchKeywords();
    const interval = setInterval(() => {
      fetchFilteredData();
    }, 45 * 60 * 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line
  }, []);

  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return;
    if (!user || (!user.is_staff && !user.is_superuser)) return;
    await axios.post(`${API_BASE}/sorter/api/keywords/`,
      { keyword_fr: newKeyword },
      { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${access}` } }
    );
    setNewKeyword("");
    fetchKeywords();
    fetchFilteredData();
  };

  const handleDeleteKeyword = async (id) => {
    if (!user || (!user.is_staff && !user.is_superuser)) return;
    await axios.delete(`${API_BASE}/sorter/api/keywords/${id}/`, {
      headers: { Authorization: `Bearer ${access}` },
    });
    fetchKeywords();
  };

  const handleReFilter = async () => {
    if (!user || (!user.is_staff && !user.is_superuser)) return;
    await axios.post(`${API_BASE}/sorter/api/refilter/`, {}, {
      headers: { Authorization: `Bearer ${access}` },
    });
    fetchFilteredData();
  };

  if (data === null) return <div className="loading-spinner"></div>;
  if (data.length === 0) return <LoadingScreen />;

  const totalPages = Math.ceil(data.length / rowsPerPage);
  const paginatedData = data.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const headers = Object.keys(columnMap);

  return (
    <div className="filtered-container">
      {/* Notification banner above main content */}
      {showNotification && (
        <div className="notification-banner">
          New filtered opportunities have been added!
          <button className="close-btn" onClick={() => setShowNotification(false)}>❌</button>
        </div>
      )}
      <div className="main-content">
        {/* LEFT: Keywords */}
        <div className={`keyword-section${user && !user.is_staff && !user.is_superuser ? ' keyword-section-normal' : ''}`}>
          <h2>Keywords</h2>
          {(user && (user.is_staff || user.is_superuser)) && (
            <>
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                placeholder="New keyword"
              />
              <button onClick={handleAddKeyword}>Add</button>
            </>
          )}
          <ul>
            {keywords.map((kw) => (
              <li key={kw.id}>
                {kw.keyword_fr}
                {(user && (user.is_staff || user.is_superuser)) && (
                  <button onClick={() => handleDeleteKeyword(kw.id)}>❌</button>
                )}
              </li>
            ))}
          </ul>
          {(user && (user.is_staff || user.is_superuser)) && (
            <button className="refilter-btn" onClick={handleReFilter}>
              Re-filter
            </button>
          )}
        </div>
        {/* RIGHT: Table */}
        <div className="table-wrapper">
          <table className="styled-table">
            <thead>
              <tr>
                {headers.map((col) => (
                  <th key={col}>{columnMap[col]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((row, idx) => (
                <tr key={idx}>
                  {headers.map((col) => (
                    <td key={col}>
                      {col === 'lien' ? (
                        <a href={row[col]} target="_blank" rel="noopener noreferrer">Lien</a>
                      ) : (
                        row[col]
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {/* Pagination */}
          <div className="pagination">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
            >
              ⬅
            </button>
            <span className="page-number">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
            >
              ➞
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Filtered;
