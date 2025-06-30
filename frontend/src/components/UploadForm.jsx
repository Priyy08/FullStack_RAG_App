// import React, { useState } from 'react';
// import axios from 'axios';

// function UploadForm({ apiUrl }) {
//   const [files, setFiles] = useState([]);
//   const [message, setMessage] = useState('');

//   const handleFileChange = (e) => {
//     setFiles([...e.target.files]);
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     if (files.length === 0) {
//       setMessage('Please select files to upload.');
//       return;
//     }
//     const formData = new FormData();
//     files.forEach(file => {
//       formData.append('files', file);
//     });

//     setMessage('Uploading and processing...');
//     try {
//       const response = await axios.post(`${apiUrl}/upload`, formData, {
//         headers: {
//           'Content-Type': 'multipart/form-data',
//         },
//       });
//       setMessage(`Successfully processed ${response.data.results.length} documents!`);
//     } catch (error) {
//       setMessage('Upload failed. Check console for details.');
//       console.error(error);
//     }
//   };

//   return (
//     <div className="upload-section">
//       <h2>1. Upload Documents</h2>
//       <form onSubmit={handleSubmit}>
//         <input type="file" multiple onChange={handleFileChange} />
//         <button type="submit">Upload & Ingest</button>
//       </form>
//       {message && <p>{message}</p>}
//     </div>
//   );
// }

// export default UploadForm;

import React, { useState } from 'react';
import axios from 'axios';
import { FaUpload, FaFileAlt, FaSpinner } from "react-icons/fa";

function UploadForm({ apiUrl }) {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
    setMessage(`${selectedFiles.length} file(s) selected.`);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (files.length === 0) {
      setMessage('Please select files to upload first.');
      return;
    }
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    setIsUploading(true);
    setMessage('Uploading and processing...');
    
    try {
      const response = await axios.post(`${apiUrl}/upload`, formData, { // Added /api prefix
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        withCredentials: true // Add this line
      });
      const successCount = response.data.results.filter(r => r.status === 'success').length;
      setMessage(`✅ Successfully processed ${successCount} document(s)! Ready to be queried.`);
      setFiles([]); // Clear selection after successful upload
    } catch (error) {
      setMessage('❌ Upload failed. Please check the server logs.');
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="upload-section">
      <h2>1. Create Your Knowledge Base</h2>
      <form onSubmit={handleSubmit} className="upload-form">
        <label htmlFor="file-upload" className="upload-input">
          <FaUpload size={24} color="var(--accent-color)" />
          <span>{files.length > 0 ? `${files.length} file(s) ready for upload` : 'Click or drag files here'}</span>
        </label>
        <input id="file-upload" type="file" multiple onChange={handleFileChange} />
        <button type="submit" className="button" disabled={isUploading || files.length === 0}>
          {isUploading ? <FaSpinner className="spinner" /> : <FaFileAlt />}
          {isUploading ? 'Ingesting...' : 'Upload & Ingest'}
        </button>
      </form>
      {message && <p className="upload-message">{message}</p>}
    </section>
  );
}

export default UploadForm;
