import React, { useEffect, useState } from 'react';
import './Filtered.css';
import LoadingScreen from './LoadingScreen';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '';

function Rejected({ user }) {
  const [data, setData] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");

  const access = localStorage.getItem('access');

  const columnMap = {
    consultation_id: 'ID Consultation',
    client: 'Client',
    intitule_projet: 'Intitulé du projet',
    lien: 'Lien',
    source: 'Source',
  };

  // Fetch rejected data
  const fetchRejectedData = () => {
    axios.get(`${API_BASE}/sorter/api/rejected_data/`)
      .then(res => setData(res.data))
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

  useEffect(() => {
    fetchRejectedData();
    fetchKeywords();
    const interval = setInterval(() => {
      fetchRejectedData();
    }, 40 * 60 * 1000); // 40 minutes
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
    fetchRejectedData();
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
    fetchRejectedData();
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
      <div className="main-content">
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

export default Rejected;
