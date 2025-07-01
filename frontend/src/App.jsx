// import React, { useState } from 'react';
// import axios from 'axios';
// import UploadForm from './components/UploadForm';
// import ChatInterface from './components/ChatInterface';
// import ResultsDisplay from './components/ResultsDisplay';
// import './App.css';

// const API_URL = 'http://localhost:8000';

// function App() {
//   const [results, setResults] = useState(null);
//   const [isLoading, setIsLoading] = useState(false);
//   const [error, setError] = useState('');

//   const handleQuerySubmit = async (query) => {
//     if (!query) return;
//     setIsLoading(true);
//     setError('');
//     setResults(null);
    
//     const formData = new FormData();
//     formData.append('query', query);

//     try {
//       const response = await axios.post(`${API_URL}/query`, formData);
//       setResults(response.data);
//     } catch (err) {
//       setError('Failed to get answer. Please try again.');
//       console.error(err);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <div className="container">
//       <h1>Wasserstoff AI Intern Project</h1>
//       <UploadForm apiUrl={API_URL} />
//       <ChatInterface onQuerySubmit={handleQuerySubmit} isLoading={isLoading} />
//       {error && <p style={{ color: 'red' }}>{error}</p>}
//       {isLoading && <p>Thinking...</p>}
//       {results && <ResultsDisplay results={results} />}
//     </div>
//   );
// }

// export default App; 

import React, { useState } from 'react';
import axios from 'axios';
import UploadForm from './components/UploadForm.jsx';
import ChatInterface from './components/ChatInterface.jsx';
import ResultsDisplay from './components/ResultsDisplay.jsx';
import { FaRobot } from "react-icons/fa";
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';


function App() {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleQuerySubmit = async (query) => {
    if (!query) return;
    setIsLoading(true);
    setError('');
    setResults(null);
    
    const formData = new FormData();
    formData.append('query', query);

    try {
      const response = await axios.post(`${API_BASE_URL}/query`, formData, {
        withCredentials: true // Add this line
      });
      setResults(response.data);
    } catch (err) {
      setError('Failed to get an answer. The server might be down or an error occurred.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <FaRobot size={36} color="var(--accent-color)" />
        <h1>Document Research & Theme Identifier</h1>
      </header>
      <main className="main-content">
        <UploadForm apiUrl={API_BASE_URL} />
        <ChatInterface onQuerySubmit={handleQuerySubmit} isLoading={isLoading} />
        {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}
        {isLoading && (
          <div className="loader-container">
            <div className="spinner"></div>
            <span>Analyzing documents...</span>
          </div>
        )}
        {results && <ResultsDisplay results={results} />}
      </main>
    </div>
  );
}

export default App;
