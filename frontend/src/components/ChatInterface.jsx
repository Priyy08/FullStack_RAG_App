// import React, { useState } from 'react';

// function ChatInterface({ onQuerySubmit, isLoading }) {
//   const [query, setQuery] = useState('');

//   const handleSubmit = (e) => {
//     e.preventDefault();
//     onQuerySubmit(query);
//   };

//   return (
//     <div className="chat-section">
//       <h2>2. Ask a Question</h2>
//       <form onSubmit={handleSubmit}>
//         <input
//           type="text"
//           value={query}
//           onChange={(e) => setQuery(e.target.value)}
//           placeholder="Ask about the content of your documents..."
//           style={{ width: '80%', padding: '8px' }}
//           disabled={isLoading}
//         />
//         <button type="submit" disabled={isLoading}>
//           {isLoading ? 'Asking...' : 'Ask'}
//         </button>
//       </form>
//     </div>
//   );
// }

// export default ChatInterface;

import React, { useState } from 'react';
import { FiSend } from "react-icons/fi";

function ChatInterface({ onQuerySubmit, isLoading }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onQuerySubmit(query);
  };

  return (
    <section className="chat-section">
      <h2>2. Ask a Question</h2>
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          className="chat-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., What are the main risks identified across these reports?"
          disabled={isLoading}
        />
        <button type="submit" className="button" disabled={isLoading || !query}>
          <FiSend />
          <span>Ask</span>
        </button>
      </form>
    </section>
  );
}

export default ChatInterface;