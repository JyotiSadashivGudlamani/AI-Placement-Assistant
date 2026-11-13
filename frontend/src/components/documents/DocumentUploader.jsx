import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { uploadDocument } from '../../api/documents';
import ErrorAlert from '../common/ErrorAlert';

export default function DocumentUploader({ onUploadSuccess }) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [category, setCategory] = useState('placement');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const fileInputRef = useRef(null);

  const allowedExtensions = ['.pdf', '.docx', '.txt'];

  const validateFile = (file) => {
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      throw new Error(`Unsupported file type '${ext}'. Please upload a PDF, DOCX, or TXT file.`);
    }
    if (file.size > 15 * 1024 * 1024) {
      throw new Error(`File '${file.name}' exceeds the maximum allowed size of 15MB.`);
    }
    if (file.size === 0) {
      throw new Error(`File '${file.name}' is empty (0 bytes).`);
    }
    return true;
  };

  const handleFileSelection = (file) => {
    setError(null);
    setSuccessMessage(null);
    try {
      validateFile(file);
      setSelectedFile(file);
    } catch (err) {
      setError(err.message);
      setSelectedFile(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile || uploading) return;

    setUploading(true);
    setProgress(0);
    setError(null);
    setSuccessMessage(null);

    try {
      const data = await uploadDocument(selectedFile, category, (percent) => {
        setProgress(percent);
      });
      setSuccessMessage(
        `Document '${data.filename}' successfully processed into ${data.total_chunks} chunks!`
      );
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (onUploadSuccess) onUploadSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
      <div className="mb-4">
        <h3 className="text-base font-bold text-slate-900 dark:text-white">Ingest New Document</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Upload resumes, technical guides, or placement notes to index into the ChromaDB vector store.
        </p>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError(null)} />

      {successMessage && (
        <div className="flex items-center gap-2 p-3 my-2 text-sm text-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-xl">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 mt-2">
        {/* Drag and Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
            dragOver
              ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/30'
              : 'border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-600 bg-slate-50/60 dark:bg-slate-800/20'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files[0] && handleFileSelection(e.target.files[0])}
            accept=".pdf,.docx,.txt"
            className="hidden"
          />

          <div className="p-3 bg-indigo-100 dark:bg-indigo-950/60 rounded-2xl text-indigo-600 dark:text-indigo-400 mb-3 shadow-xs">
            <UploadCloud className="w-7 h-7" />
          </div>

          <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            {selectedFile ? selectedFile.name : 'Click to upload or drag & drop'}
          </p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
            Supports PDF (PyMuPDF), DOCX (tables + paragraphs), and TXT (up to 15MB)
          </p>
        </div>

        {/* Category & Action Row */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-1">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 shrink-0">
              Category:
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="text-xs font-medium px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
            >
              <option value="placement">General Placement</option>
              <option value="resume">Resume / CV</option>
              <option value="java">Java & OOP</option>
              <option value="python">Python & AI</option>
              <option value="system_design">System Design</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className={`w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold text-white transition-all shadow-sm ${
              !selectedFile || uploading
                ? 'bg-slate-400 dark:bg-slate-700 cursor-not-allowed opacity-70'
                : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 cursor-pointer shadow-indigo-600/20'
            }`}
          >
            {uploading ? `Processing (${progress}%)...` : 'Process & Index Document'}
          </button>
        </div>

        {uploading && (
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </form>
    </div>
  );
}
