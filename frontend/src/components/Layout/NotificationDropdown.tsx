import React, { useEffect, useState, useRef } from 'react';
import { AlertTriangle, ShieldAlert, Target, Activity } from 'lucide-react';
import { DeadlineOSApi } from '../../api';

interface NotificationDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  setUnreadCount: (count: number) => void;
}

export const NotificationDropdown: React.FC<NotificationDropdownProps> = ({ isOpen, onClose, setUnreadCount }) => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await DeadlineOSApi.getNotifications();
        if (res.data) {
          setNotifications(res.data.notifications || []);
          setUnreadCount(res.data.unread_count || 0);
        }
      } catch (err) {
        console.error("Failed to load notifications", err);
      }
    };
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [setUnreadCount]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div ref={dropdownRef} className="absolute top-16 right-8 w-80 max-h-96 overflow-y-auto bg-black/80 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl z-50 p-2">
      <h3 className="text-sm font-bold text-white px-3 py-2 border-b border-white/10 mb-2">Notifications</h3>
      
      {notifications.length === 0 ? (
        <div className="p-4 text-center text-gray-400 text-sm">
          No new notifications.
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => {
            let Icon = Activity;
            let iconColor = 'text-gray-400';
            
            if (n.severity === 'critical' || n.severity === 'high') {
              Icon = AlertTriangle;
              iconColor = 'text-rose-500';
            } else if (n.severity === 'medium') {
              Icon = ShieldAlert;
              iconColor = 'text-amber-500';
            } else {
              Icon = Target;
              iconColor = 'text-emerald-500';
            }

            return (
              <div key={n.id} className="flex gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">
                <div className={`mt-0.5 ${iconColor}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-bold text-gray-200">{n.title}</p>
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2">{n.message}</p>
                  <p className="text-[10px] text-gray-500 mt-1">{new Date(n.timestamp).toLocaleString()}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
