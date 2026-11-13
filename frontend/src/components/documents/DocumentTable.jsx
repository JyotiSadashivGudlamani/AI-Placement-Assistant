import React, { useState } from 'react';
import { FileText, Trash2, CheckCircle2, Clock, Layers } from 'lucide-react';
import { deleteDocument } from '../../api/documents';
import EmptyState from '../common/EmptyState';
import ErrorAlert from '../common/ErrorAlert';

export default function DocumentTable({ documents = [], onDocumentDeleted }) {
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState(null);

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete '${filename}' from ChromaDB and the registry?`)) {
      return;
    }

    setDeletingId(docId);
    setError(null);
    try {
      await deleteDocument(docId);
      if (onDocumentDeleted) onDocumentDeleted(docId);
    } catch (err) {
      setError(`Failed to delete document: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Just now';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  if (!documents || documents.length === 0) {
    return (
      <EmptyState
        title="No documents indexed"
        description="Upload your resumes, syllabus notes, or placement question banks above to enable semantic RAG search."
      />
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Indexed Documents</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {documents.length} document{documents.length !== 1 ? 's' : ''} stored with dense vector representations
          </p>
        </div>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError(null)} />

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
            <tr>
              <th className="px-6 py-3.5">Document</th>
              <th className="px-4 py-3.5">Category</th>
              <th className="px-4 py-3.5">Pages</th>
              <th className="px-4 py-3.5">Chunks</th>
              <th className="px-4 py-3.5">Size</th>
              <th className="px-4 py-3.5">Uploaded</th>
              <th className="px-6 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
            {documents.map((doc) => (
              <tr
                key={doc.document_id}
                className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
              >
                {/* Document Name */}
                <td className="px-6 py-4 font-medium flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-slate-900 dark:text-slate-100 font-semibold block">
                      {doc.filename}
                    </span>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">
                      {doc.file_type}
                    </span>
                  </div>
                </td>

                {/* Category */}
                <td className="px-4 py-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    {doc.category || 'placement'}
                  </span>
                </td>

                {/* Pages */}
                <td className="px-4 py-4">{doc.total_pages || 1}</td>

                {/* Chunks */}
                <td className="px-4 py-4 font-mono text-indigo-600 dark:text-indigo-400 font-medium">
                  {doc.total_chunks || 0}
                </td>

                {/* Size */}
                <td className="px-4 py-4 text-slate-500 dark:text-slate-400">
                  {formatBytes(doc.file_size_bytes)}
                </td>

                {/* Date */}
                <td className="px-4 py-4 text-slate-500 dark:text-slate-400">
                  {formatDate(doc.uploaded_at)}
                </td>

                {/* Actions */}
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => handleDelete(doc.document_id, doc.filename)}
                    disabled={deletingId === doc.document_id}
                    className="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg transition-colors cursor-pointer"
                    title="Delete document and its ChromaDB vectors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
