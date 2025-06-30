// import React from 'react';

// function ResultsDisplay({ results }) {
//   if (!results) return null;

//   const { individual_answers, themed_summary } = results;

//   return (
//     <div className="results-section">
//       <h2>Results</h2>
      
//       <h3>Individual Document Answers</h3>
//       <table>
//         <thead>
//           <tr>
//             <th>Document ID</th>
//             <th>Extracted Answer</th>
//             <th>Citation</th>
//           </tr>
//         </thead>
//         <tbody>
//           {individual_answers.map((item, index) => (
//             <tr key={index}>
//               <td>{item.document_id}</td>
//               <td>{item.extracted_answer}</td>
//               <td>{item.citation}</td>
//             </tr>
//           ))}
//         </tbody>
//       </table>

//       <h3>Synthesized (Theme) Answer</h3>
//       <div className="theme-summary">
//         {themed_summary}
//       </div>
//     </div>
//   );
// }

// export default ResultsDisplay;

import React from 'react';
import { FaBook, FaQuoteLeft, FaTags } from 'react-icons/fa';
import { VscReferences } from "react-icons/vsc";

function ResultsDisplay({ results }) {
  if (!results) return null;

  const { individual_answers, themed_summary } = results;

  return (
    <section className="results-section">
      {/* Thematic Summary */}
      <h2><FaTags /> Thematic Summary</h2>
      <div className="themed-summary">
        {themed_summary || "No thematic summary could be generated."}
      </div>

      {/* Individual Document Answers */}
      <div className="individual-answers-container">
        <h2><VscReferences /> Individual Document Answers</h2>
        {individual_answers && individual_answers.length > 0 ? (
          individual_answers.map((item, index) => (
            <div key={index} className="individual-answer-card">
              <div className="card-header">
                <span className="document-id">
                  <FaBook color="var(--secondary-text-color)" /> 
                  {item.document_id}
                </span>
                <span className="citation">{item.citation}</span>
              </div>
              <p className="extracted-answer">
                <FaQuoteLeft size={12} style={{ marginRight: '0.5rem', color: 'var(--border-color)' }} />
                {item.extracted_answer}
              </p>
            </div>
          ))
        ) : (
          <p>No individual answers were extracted from the documents.</p>
        )}
      </div>
    </section>
  );
}

export default ResultsDisplay;