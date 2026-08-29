import React, { useEffect, useState } from 'react';
import { AlertTriangle, ShieldAlert } from 'lucide-react';
import { api } from '../../api';

export const CashRiskBanner: React.FC = () => {
  const [riskData, setRiskData] = useState<any>(null);

  useEffect(() => {
    api.getBusinessRisks()
      .then(res => setRiskData(res.data?.risks))
      .catch(() => {});
  }, []);

  if (!riskData || riskData.risks_count === 0) return null;

  const topRisk = riskData.risks[0];
  const isCritical = riskData.overall_status === 'CRITICAL';

  return (
    <div className={`p-4 rounded-2xl mb-6 border flex items-center justify-between gap-4 ${
      isCritical
        ? 'bg-rose-950/30 border-rose-500/30 text-rose-300'
        : 'bg-amber-950/30 border-amber-500/30 text-amber-300'
    }`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-xl ${isCritical ? 'bg-rose-500/20' : 'bg-amber-500/20'}`}>
          {isCritical ? <ShieldAlert className="w-5 h-5 text-rose-400" /> : <AlertTriangle className="w-5 h-5 text-amber-400" />}
        </div>
        <div>
          <div className="text-sm font-semibold text-white flex items-center gap-2">
            {topRisk.title}
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border bg-black/20">
              {topRisk.code}
            </span>
          </div>
          <p className="text-xs text-slate-300 mt-0.5">{topRisk.message}</p>
        </div>
      </div>
    </div>
  );
};
