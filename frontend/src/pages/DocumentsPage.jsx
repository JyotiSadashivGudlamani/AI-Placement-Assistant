import React, { useEffect, useState } from 'react';
import { RefreshCw, Filter } from 'lucide-react';
import { getDocuments } from '../api/documents';
import DocumentUploader from '../components/documents/DocumentUploader';
import DocumentTable from '../components/documents/DocumentTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('');

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await getDocuments(categoryFilter || null);
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [categoryFilter]);

  const handleUploadSuccess = () => {
    fetchDocuments();
  };

  const handleDocumentDeleted = (deletedId) => {
    setDocuments((prev) => prev.filter((d) => d.document_id !== deletedId));
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Upload Section */}
      <DocumentUploader onUploadSuccess={handleUploadSuccess} />

      {/* Filter and Action Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Filter Category:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs px-3 py-1.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 focus:outline-hidden"
          >
            <option value="">All Categories</option>
            <option value="placement">Placement</option>
            <option value="resume">Resume</option>
            <option value="java">Java & OOP</option>
            <option value="python">Python & AI</option>
          </select>
        </div>

        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Registry
        </button>
      </div>

      {/* Document List Table */}
      {loading ? (
        <LoadingSpinner message="Loading indexed documents..." />
      ) : (
        <DocumentTable documents={documents} onDocumentDeleted={handleDocumentDeleted} />
      )}
    </div>
  );
}
