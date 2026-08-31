import React, { useState, useEffect } from 'react';
import { api } from '../../api';
import { Upload, Send, X, FileText, AlertCircle, CheckCircle } from 'lucide-react';

interface CaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const CaptureModal: React.FC<CaptureModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [activeTab, setActiveTab] = useState<'text' | 'upload'>('text');
  const [textPrompt, setTextPrompt] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textPrompt.trim()) return;

    setIsLoading(true);
    setFeedback(null);
    try {
      const res = await api.captureText(textPrompt.trim());
      if (res.status === 'success') {
        setFeedback({ type: 'success', message: 'Candidate extracted and staged for review!' });
        setTextPrompt('');
        setTimeout(() => {
          onSuccess?.();
          onClose();
        }, 1200);
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Capture failed.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsLoading(true);
    setFeedback(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('artifact_type', file.type.startsWith('audio/') ? 'AUDIO' : 'DOCUMENT');

      const res = await api.captureUpload(formData);
      if (res.status === 'success') {
        setFeedback({ type: 'success', message: 'Document processed and staged for review!' });
        setFile(null);
        setTimeout(() => {
          onSuccess?.();
          onClose();
        }, 1200);
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Upload failed.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="capture-modal-title"
        className="w-full max-w-lg rounded-2xl bg-zinc-900 border border-white/10 shadow-2xl p-6 relative"
      >
        <button
          onClick={onClose}
          aria-label="Close capture modal"
          className="absolute top-4 right-4 p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
        >
          <X className="w-4 h-4" />
        </button>

        <h2 id="capture-modal-title" className="text-lg font-bold text-white mb-4">Capture Business Item</h2>

        <div className="flex gap-2 mb-4 p-1 bg-white/5 rounded-xl border border-white/5">
          <button
            onClick={() => setActiveTab('text')}
            className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'text' ? 'bg-emerald-500 text-black shadow' : 'text-zinc-400 hover:text-white'
            }`}
          >
            Quick Note / Text
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'upload' ? 'bg-emerald-500 text-black shadow' : 'text-zinc-400 hover:text-white'
            }`}
          >
            Document / Receipt
          </button>
        </div>

        {feedback && (
          <div className={`mb-4 p-3 rounded-xl text-xs flex items-center gap-2 ${
            feedback.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}>
            {feedback.type === 'success' ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
            <span>{feedback.message}</span>
          </div>
        )}

        {activeTab === 'text' && (
          <form onSubmit={handleTextSubmit} className="space-y-4">
            <textarea
              rows={3}
              placeholder="e.g. Bought stock from Reliance Retail for ₹12,500 on Friday"
              value={textPrompt}
              onChange={e => setTextPrompt(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading || !textPrompt.trim()}
                className="flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-black font-semibold text-xs shadow-lg shadow-emerald-500/10"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{isLoading ? 'Extracting...' : 'Stage for Review'}</span>
              </button>
            </div>
          </form>
        )}

        {activeTab === 'upload' && (
          <form onSubmit={handleFileUpload} className="space-y-4">
            <div className="border-2 border-dashed border-white/10 hover:border-emerald-500/50 rounded-2xl p-6 text-center transition-colors">
              <input
                type="file"
                id="biz-file-upload"
                accept=".pdf,.png,.jpg,.jpeg,.txt"
                onChange={e => setFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              <label htmlFor="biz-file-upload" className="cursor-pointer flex flex-col items-center gap-2">
                <Upload className="w-8 h-8 text-emerald-400 mb-1" />
                <span className="text-xs font-semibold text-zinc-200">
                  {file ? file.name : 'Click to upload or drag & drop'}
                </span>
                <span className="text-[10px] text-zinc-500">PDF, PNG, JPG up to 15MB</span>
              </label>
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading || !file}
                className="flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-black font-semibold text-xs shadow-lg shadow-emerald-500/10"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>{isLoading ? 'Uploading & Processing...' : 'Process Document'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
