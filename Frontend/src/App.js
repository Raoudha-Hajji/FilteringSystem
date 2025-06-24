// src/App.js
import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Filtered from './pages/Filtered';
import Rejected from './pages/Rejected';
import Visualization from './pages/visualization';

function App() {
  return (
    <BrowserRouter>
      <nav style={{ marginBottom: '1rem' }}>
        <Link to="/filtered" style={{ marginRight: '1rem' }}>Filtered </Link>
        <Link to="/rejected" style={{ marginRight: '1rem' }}>Rejected </Link>
        <Link to="/visualization">Visualization</Link>
      </nav>
      <Routes>
        <Route path="/filtered" element={<Filtered />} />
        <Route path="/rejected" element={<Rejected />} />
        <Route path="/visualization" element={<Visualization />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
