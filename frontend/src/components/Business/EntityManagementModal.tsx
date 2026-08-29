import React, { useState } from 'react';
import { X, Check } from 'lucide-react';
import { api } from '../../api';

interface EntityManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const EntityManagementModal: React.FC<EntityManagementModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [legalName, setLegalName] = useState('');
  const [entityCode, setEntityCode] = useState('');
  const [taxIdentifier, setTaxIdentifier] = useState('');
  const [isDefault, setIsDefault] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError(null);
    try {
      await api.createBusinessEntity({
        name: name.trim(),
        legal_name: legalName.trim() || undefined,
        entity_code: entityCode.trim() || undefined,
        tax_identifier: taxIdentifier.trim() || undefined,
        is_default: isDefault,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to create entity');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
          <h3 className="font-semibold text-white">Register Legal Entity / Branch</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="text-xs font-semibold text-slate-400">Entity Display Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Mumbai Operating Division"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-400">Registered Legal Name</label>
            <input
              type="text"
              value={legalName}
              onChange={(e) => setLegalName(e.target.value)}
              placeholder="e.g. Acme Technologies India Private Limited"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-400">Entity Code</label>
              <input
                type="text"
                value={entityCode}
                onChange={(e) => setEntityCode(e.target.value)}
                placeholder="MUM-01"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400">GSTIN / PAN / EIN</label>
              <input
                type="text"
                value={taxIdentifier}
                onChange={(e) => setTaxIdentifier(e.target.value)}
                placeholder="27ABCDE1234F1Z5"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="isDefault"
              checked={isDefault}
              onChange={(e) => setIsDefault(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-0"
            />
            <label htmlFor="isDefault" className="text-xs text-slate-300">
              Set as default legal entity for this workspace
            </label>
          </div>

          <button
            type="submit"
            disabled={loading || !name.trim()}
            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-colors"
          >
            <Check className="w-4 h-4" />
            <span>Register Business Entity</span>
          </button>
        </form>
      </div>
    </div>
  );
};
