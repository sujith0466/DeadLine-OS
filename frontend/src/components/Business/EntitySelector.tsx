import React, { useEffect, useState } from 'react';
import { Building2, Plus } from 'lucide-react';
import { api } from '../../api';

interface EntitySelectorProps {
  selectedEntityId?: string;
  onSelectEntity: (entityId?: string) => void;
  onOpenCreate: () => void;
}

export const EntitySelector: React.FC<EntitySelectorProps> = ({ selectedEntityId, onSelectEntity, onOpenCreate }) => {
  const [entities, setEntities] = useState<any[]>([]);

  useEffect(() => {
    api.listBusinessEntities()
      .then(res => setEntities(res.data?.entities || []))
      .catch(console.error);
  }, []);

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white">
        <Building2 className="w-3.5 h-3.5 text-indigo-400" />
        <select
          value={selectedEntityId || ''}
          onChange={(e) => onSelectEntity(e.target.value || undefined)}
          className="bg-transparent border-none text-xs text-white focus:outline-none cursor-pointer"
        >
          <option value="" className="bg-slate-900 text-slate-300">All Legal Entities (Workspace Consolidated)</option>
          {entities.map((ent) => (
            <option key={ent.id} value={ent.id} className="bg-slate-900 text-white">
              {ent.name} {ent.is_default ? '(Default)' : ''}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={onOpenCreate}
        title="Register New Legal Entity"
        className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
      >
        <Plus className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
