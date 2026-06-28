/**
 * useDemoLogin
 * ============
 * Shared hook that implements the Demo Login flow used by:
 *   - Login page  (Quick Access / Demo Account button)
 *   - Landing page (Watch Demo button)
 *
 * Both callers execute the exact same:
 *   1. POST /demo/start  → get access_token + refresh_token
 *   2. supabase.auth.setSession()
 *   3. navigate('/dashboard')
 *
 * Error handling and loading state are returned so each UI can
 * render its own affordances without duplicating logic.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { supabase } from '../lib/supabase';

interface UseDemoLoginReturn {
  handleDemoLogin: () => Promise<void>;
  loading: boolean;
  error: string | null;
  clearError: () => void;
}

export function useDemoLogin(): UseDemoLoginReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/demo/start`
      );
      const { access_token, refresh_token } = response.data;

      if (!access_token || !refresh_token) {
        throw new Error('Invalid demo session returned from server');
      }

      const { error: sessionError } = await supabase.auth.setSession({
        access_token,
        refresh_token,
      });

      if (sessionError) {
        throw sessionError;
      }

      navigate('/dashboard');
    } catch (err: any) {
      if (
        err.code === 'ERR_NETWORK' ||
        err.code === 'ECONNREFUSED' ||
        !err.response
      ) {
        setError(
          'Demo service is temporarily unavailable. Please try again in a few minutes.'
        );
      } else {
        setError(
          'Failed to authenticate demo user: ' +
            (err.response?.data?.error || err.message)
        );
      }
      setLoading(false);
    }
  };

  const clearError = () => setError(null);

  return { handleDemoLogin, loading, error, clearError };
}
