import React from 'react';
import './LoadingScreen.css';

function LoadingScreen() {
  return (
    <div className="loading-screen">
      <img src="/Progress_Eng.png" alt="Progress Engineering" className="loading-logo" />
      <p>Data loading, please wait...</p>
    </div>
  );
}

export default LoadingScreen;
