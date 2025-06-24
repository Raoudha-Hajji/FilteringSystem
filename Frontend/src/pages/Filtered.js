import React, { useEffect, useState } from 'react';
import './Filtered.css';

function Filtered() {
  const [data, setData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const columnMap = {
    consultation_id: 'ID Consultation',
    client: 'Client',
    intitule_projet: 'Intitulé du projet',
    lien: 'Lien',
    source: 'Source',
  };

  useEffect(() => {
    fetch('http://localhost:8000/sorter/api/filtered_data/')
      .then(res => res.json())
      .then(data => setData(data))
      .catch(err => console.error('Error fetching data:', err));
  }, []);

  const totalPages = Math.ceil(data.length / rowsPerPage);
  const paginatedData = data.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const headers = Object.keys(columnMap);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  if (data.length === 0) return <div className="loading">Loading...</div>;

  return (
    <div className="filtered-container">
      <div className="button-group">
        <button className="nav-button">Opportunités Filtrées</button>
        <button className="nav-button">Opportunités Rejetées</button>
        <button className="nav-button">Vue des Données</button>
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

        {/* Pagination dots */}
        <div className="pagination-dots">
          {Array.from({ length: totalPages }, (_, i) => (
            <span
              key={i}
              className={`dot ${currentPage === i + 1 ? 'active' : ''}`}
              onClick={() => handlePageChange(i + 1)}
            ></span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Filtered;
