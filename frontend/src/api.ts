import axios from 'axios';
import { SystemEventBus, type SystemEventPayload } from './utils/SystemEventBus';
import { supabase } from './lib/supabase';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const emitEvent = (event: SystemEventPayload['event'], origin: string = 'API', data?: any) => {
  SystemEventBus.emit({
    event,
    origin,
    timestamp: new Date().toISOString(),
    version: '1.0',
    data
  });
};

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000, // 15 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(async (config) => {
  if (!navigator.onLine) {
    window.dispatchEvent(new CustomEvent('deadline_api_error', { 
      detail: 'You are offline. Please check your network connection.' 
    }));
    return Promise.reject(new Error('No internet connection'));
  }

  // Inject Correlation ID
  config.headers['X-Correlation-ID'] = crypto.randomUUID();

  // Inject Active Business Workspace ID if present
  const activeWorkspaceId = localStorage.getItem('active_workspace_id');
  if (activeWorkspaceId) {
    config.headers['X-Workspace-Id'] = activeWorkspaceId;
  }

  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Simple retry state storage for Axios
const retryConfig = {
  maxRetries: 3,
  retryDelay: (retryCount: number) => Math.min(1000 * (2 ** retryCount), 5000)
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Automatic Retry Queue for Network Errors & 5xx Server Errors
    if (originalRequest && !originalRequest._retryCount) {
      originalRequest._retryCount = 0;
    }
    
    const isRetryableError = 
      error.code === 'ERR_NETWORK' || 
      error.message === 'Network Error' || 
      error.code === 'ECONNABORTED' ||
      (error.response && (error.response.status >= 500 || error.response.status === 429));

    if (isRetryableError && originalRequest && originalRequest._retryCount < retryConfig.maxRetries) {
      originalRequest._retryCount += 1;
      const delay = retryConfig.retryDelay(originalRequest._retryCount);
      
      console.debug(`[API] Retry ${originalRequest._retryCount}/${retryConfig.maxRetries} for ${originalRequest.url} in ${delay}ms`);
      
      // Create a promise that resolves after the delay
      await new Promise(resolve => setTimeout(resolve, delay));
      return apiClient(originalRequest);
    }

    let errorMessage = 'Something went wrong. Please try again.';
    
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error' || error.code === 'ECONNABORTED') {
      errorMessage = 'Unable to connect. Please check your internet connection.';
    } else if (error.response) {
      const status = error.response.status;
      if (status === 401 || status === 403) {
        errorMessage = 'Your session has expired or is invalid. Please log in again.';
      } else if (status === 429) {
        errorMessage = 'Too many requests. Please try again shortly.';
      } else if (status === 400 || status === 422) {
        // Validation errors
        errorMessage = error.response.data?.error || 'Please check the highlighted fields.';
      } else if (status >= 500) {
        errorMessage = 'The service is temporarily unavailable.';
      }
    }

    // Only log the real technical details internally
    console.debug('[API Error Internal]:', error);

    window.dispatchEvent(new CustomEvent('deadline_api_error', { 
      detail: errorMessage 
    }));
    
    // Pass a sanitized error object so components don't crash or display stack traces
    const sanitizedError = new Error(errorMessage);
    (sanitizedError as any).status = error.response?.status;
    return Promise.reject(sanitizedError);
  }
);

export const DeadlineOSApi = {
  // ── NOTIFICATIONS ──────────────────────────────────────────────────────
  async getNotifications(params?: { limit?: number, offset?: number, unread_only?: boolean, category?: string }) {
    const response = await apiClient.get('/notifications', { params });
    return response.data;
  },

  async markNotificationRead(id: string) {
    const response = await apiClient.put(`/notifications/${id}/read`);
    emitEvent('NOTIFICATION_READ');
    return response.data;
  },

  async markAllNotificationsRead() {
    const response = await apiClient.put('/notifications/read-all');
    emitEvent('NOTIFICATION_READ');
    return response.data;
  },

  async clearAllNotifications() {
    const response = await apiClient.delete('/notifications/clear');
    emitEvent('NOTIFICATION_READ');
    return response.data;
  },

  async executeNotificationAction(id: string, action: string, payload?: any) {
    const response = await apiClient.post(`/notifications/${id}/action`, { action, payload });
    emitEvent('NOTIFICATION_READ');
    return response.data;
  },

  async dismissNotification(id: string) {
    const response = await apiClient.post(`/notifications/${id}/dismiss`);
    emitEvent('NOTIFICATION_READ');
    return response.data;
  },

  async evaluateScheduleCheckins(grace_minutes: number = 10) {
    const response = await apiClient.post('/schedule/checkin/evaluate', { grace_minutes });
    return response.data;
  },

  
  // ── TODAY SURFACE ────────────────────────────────────────────────────────
  async getTodayActivities() {
    const response = await apiClient.get('/today');
    return response.data;
  },
  // ── TASKS ─────────────────────────────────────────────────────────────
  
  async getTasks() {
    const response = await apiClient.get('/tasks');
    return response.data;
  },

  // ── AGENTS ────────────────────────────────────────────────────────────

  async getAgentStatus() {
    const response = await apiClient.get('/agents/status');
    return response.data;
  },

  async runPriorityAgent(payload: { title: string, deadline: string, description?: string, estimated_hours?: number }) {
    const response = await apiClient.post('/agents/prioritize', payload);
    return response.data;
  },

  async runPlanningAgent(payload: { tasks: any[], availability: any }, origin: string = 'Planner') {
    const response = await apiClient.post('/agents/plan', payload);
    emitEvent('PLANNER_GENERATED', origin);
    return response.data;
  },

  async getLatestSchedule() {
    const response = await apiClient.get(`/agents/plan/latest?_t=${Date.now()}`);
    return response.data;
  },

  async runRescueAgent(payload: { tasks: any[], availability: any }) {
    const response = await apiClient.post('/agents/rescue', payload);
    return response.data;
  },

  async getRescueHistory() {
    const response = await apiClient.get('/agents/rescue/history');
    return response.data;
  },

  async executeRescuePlan(payload: { plan_id: string, action: string }) {
    const response = await apiClient.post('/agents/rescue/execute', payload);
    emitEvent('RESCUE_EXECUTED');
    return response.data;
  },

  async runDigitalTwin(payload: { scenario: any }) {
    const response = await apiClient.post('/agents/digital-twin', payload);
    return response.data;
  },

  async getDigitalTwinHistory() {
    const response = await apiClient.get('/agents/twin/history');
    return response.data;
  },

  async runVisionAgent(file: File) {
    const formData = new FormData();
    formData.append('image', file);
    
    const response = await apiClient.post('/agents/vision', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async confirmVisionAgent(data: any) {
    const response = await apiClient.post('/agents/vision/confirm', data);
    return response.data;
  },

  // ── ORCHESTRATION ────────────────────────────────────────────────────────

  async getOrchestrationFeed() {
    const response = await apiClient.get('/orchestration/feed');
    return response.data;
  },

  async runOrchestrationPipeline(file: File) {
    const formData = new FormData();
    formData.append('image', file);
    const response = await apiClient.post('/orchestration/pipeline', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async executeSystemOrchestration() {
    const response = await apiClient.post('/orchestration/execute', {});
    emitEvent('COMMAND_CENTER_REFRESH');
    return response.data;
  },

  // ── ANALYTICS ────────────────────────────────────────────────────────────

  async getAnalyticsOverview() {
    const response = await apiClient.get('/analytics/overview');
    return response.data;
  },

  async getAnalyticsBriefing() {
    const response = await apiClient.get('/analytics/briefing');
    return response.data;
  },

  async getAnalyticsProductivity() {
    const response = await apiClient.get('/analytics/productivity');
    return response.data;
  },

  async getAnalyticsContributions() {
    const response = await apiClient.get('/analytics/contributions');
    return response.data;
  },

  async getAnalyticsIntelligence() {
    const response = await apiClient.get('/analytics/intelligence');
    return response.data;
  },

  async getAnalyticsHeatmap() {
    const response = await apiClient.get('/analytics/heatmap');
    return response.data;
  },

  async getAnalyticsVoice() {
    const response = await apiClient.get('/analytics/voice');
    return response.data;
  },

  async getAnalyticsVision() {
    const response = await apiClient.get('/analytics/vision');
    return response.data;
  },

  async getAnalyticsDocuments() {
    const response = await apiClient.get('/analytics/documents');
    return response.data;
  },

  async getAnalyticsInterventions() {
    const response = await apiClient.get('/analytics/interventions');
    return response.data;
  },

  async getAnalyticsTwinAccuracy() {
    const response = await apiClient.get('/analytics/twin-accuracy');
    return response.data;
  },

  async getAnalyticsInsights() {
    const response = await apiClient.get('/analytics/insights');
    return response.data;
  },

  async downloadReport() {
    const response = await apiClient.get('/reports/download', { responseType: 'blob' });
    return response.data;
  },

  // ── CALENDAR ─────────────────────────────────────────────────────────────

  async getCalendarEvents() {
    const response = await apiClient.get('/calendar/events');
    return response.data;
  },

  async getCalendarIntelligence() {
    const response = await apiClient.get('/calendar/intelligence');
    return response.data;
  },

  async rescheduleCalendarEvent(id: string, start: string, end: string) {
    const response = await apiClient.post('/calendar/reschedule', { id, start, end });
    return response.data;
  },

  // ── INTERVENTIONS ────────────────────────────────────────────────────────

  async getInterventionThreats() {
    const response = await apiClient.get('/interventions/threats');
    return response.data;
  },

  async scanInterventions() {
    const response = await apiClient.post('/interventions/scan');
    return response.data;
  },

  async executeInterventionStrategy(payload: { strategy_name: string, actions: any[] }) {
    const response = await apiClient.post('/interventions/execute', payload);
    return response.data;
  },

  async undoIntervention(executionId: string) {
    const response = await apiClient.post(`/interventions/undo/${executionId}`);
    return response.data;
  },

  // ── GOALS & HABITS ───────────────────────────────────────────────────────

  async getGoals() {
    const response = await apiClient.get('/goals');
    return response.data;
  },

  async getHabits() {
    const response = await apiClient.get('/habits');
    return response.data;
  },

  async createGoal(payload: { title: string, description?: string, category?: string, target_date?: string }) {
    const response = await apiClient.post('/goals', payload);
    emitEvent('GOAL_CREATED');
    return response.data;
  },

  async createHabit(payload: { name: string, category?: string, frequency?: string }) {
    const response = await apiClient.post('/habits', payload);
    emitEvent('HABIT_CREATED');
    return response.data;
  },

  async editGoal(goalId: string, payload: any) {
    const response = await apiClient.put(`/goals/${goalId}`, payload);
    emitEvent('GOAL_UPDATED');
    return response.data;
  },

  async archiveGoal(goalId: string) {
    const response = await apiClient.post(`/goals/${goalId}/archive`);
    emitEvent('GOAL_ARCHIVED');
    return response.data;
  },

  async unarchiveGoal(goalId: string) {
    const response = await apiClient.post(`/goals/${goalId}/unarchive`);
    return response.data;
  },

  async pinGoal(goalId: string) {
    const response = await apiClient.post(`/goals/${goalId}/pin`);
    return response.data;
  },

  async deleteGoal(goalId: string) {
    const response = await apiClient.delete(`/goals/${goalId}`);
    emitEvent('GOAL_UPDATED');
    return response.data;
  },

  async updateMilestoneStatus(milestoneId: string, status: string) {
    const response = await apiClient.put(`/milestones/${milestoneId}/status`, { status });
    emitEvent('GOAL_UPDATED');
    return response.data;
  },

  async editHabit(habitId: string, payload: any) {
    const response = await apiClient.put(`/habits/${habitId}`, payload);
    emitEvent('HABIT_UPDATED');
    return response.data;
  },

  async archiveHabit(habitId: string) {
    const response = await apiClient.post(`/habits/${habitId}/archive`);
    return response.data;
  },

  async unarchiveHabit(habitId: string) {
    const response = await apiClient.post(`/habits/${habitId}/unarchive`);
    return response.data;
  },

  async deleteHabit(habitId: string) {
    const response = await apiClient.delete(`/habits/${habitId}`);
    return response.data;
  },

  async setHabitStatus(habitId: string, status: string) {
    const response = await apiClient.post(`/habits/${habitId}/status`, { status });
    emitEvent('HABIT_UPDATED');
    return response.data;
  },

  async checkInHabit(habitId: string) {
    const response = await apiClient.post(`/habits/${habitId}/checkin`);
    emitEvent('HABIT_CHECKIN');
    return response.data;
  },

  // ── DOCUMENTS ────────────────────────────────────────────────────────────

  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  // ── VOICE COPILOT ────────────────────────────────────────────────────────

  async processVoiceTranscript(transcript: string) {
    const response = await apiClient.post('/voice/process', { transcript });
    return response.data;
  },

  // ── DEMO/SIMULATION ──────────────────────────────────────────────────────
  
  async runDigitalTwinSimulation(userId: string) {
    const response = await apiClient.post(`/demo/simulate-twin/${userId}`, {});
    return response.data;
  },

  // ── SETTINGS & PROFILE ───────────────────────────────────────────────────

  async getProfile() {
    const response = await apiClient.get('/settings/profile');
    return response.data;
  },

  async updateProfile(data: any) {
    const response = await apiClient.put('/settings/profile', data);
    return response.data;
  },

  async getSettings(section: string) {
    const response = await apiClient.get(`/settings/${section}`);
    return response.data;
  },

  async updateSettings(section: string, data: any) {
    const response = await apiClient.put(`/settings/${section}`, data);
    return response.data;
  },

  async getSessions() {
    const response = await apiClient.get('/settings/sessions');
    return response.data;
  },

  async deleteSession(sessionId: string) {
    const response = await apiClient.delete(`/settings/session/${sessionId}`);
    return response.data;
  },

  async getConnectedAccounts() {
    const response = await apiClient.get('/settings/accounts');
    return response.data;
  },

  async updateConnectedAccounts(data: any) {
    const response = await apiClient.put('/settings/accounts', data);
    return response.data;
  },

  async exportData() {
    const response = await apiClient.post('/settings/export', {});
    return response.data;
  },

  async deleteAccount() {
    const response = await apiClient.delete('/account');
    return response.data;
  }
,

  runtime: {
    async getActive() {
      const response = await apiClient.get('/runtime/active');
      return response.data;
    },
    async start(entityId: string, entityType: string, plannedDurationSec?: number) {
      const response = await apiClient.post('/runtime/start', { entity_id: entityId, entity_type: entityType, planned_duration_sec: plannedDurationSec });
      return response.data;
    },
    async pause(entityId: string) {
      const response = await apiClient.post('/runtime/pause', { entity_id: entityId });
      return response.data;
    },
    async resume(entityId: string) {
      const response = await apiClient.post('/runtime/resume', { entity_id: entityId });
      return response.data;
    },
    async complete(entityId: string, completionSource: string = 'MANUAL') {
      const response = await apiClient.post('/runtime/complete', { entity_id: entityId, completion_source: completionSource });
      return response.data;
    }
  },

  // ── SMART SCHEDULING (PHASE 3) ───────────────────────────────────────────
  async getScheduleSlots(params?: { start?: string, end?: string, status?: string }) {
    const response = await apiClient.get('/schedule/slots', { params });
    return response.data;
  },

  async createScheduleSlot(payload: {
    entity_type?: string,
    entity_id?: string,
    title?: string,
    start_time?: string,
    end_time?: string,
    duration_minutes?: number,
    priority?: number,
    focus_block?: boolean,
    is_break?: boolean,
    schedule_id?: string
  }) {
    const response = await apiClient.post('/schedule/slots', payload);
    emitEvent('PLANNER_UPDATED');
    return response.data;
  },

  async deleteScheduleSlot(slotId: string) {
    const response = await apiClient.delete(`/schedule/slots/${slotId}`);
    emitEvent('PLANNER_UPDATED');
    return response.data;
  },

  async validateScheduleConflicts(payload: {
    start_time: string,
    end_time: string,
    entity_id?: string,
    window_start?: string,
    window_end?: string,
    exclude_slot_id?: string,
    allow_past?: boolean
  }) {
    const response = await apiClient.post('/schedule/validate-conflicts', payload);
    return response.data;
  },

  async planPrioritySchedule(payload: {
    activities: any[],
    window_start: string,
    window_end: string,
    buffer_minutes?: number,
    persist?: boolean
  }) {
    const response = await apiClient.post('/schedule/priority-plan', payload);
    emitEvent('PLANNER_GENERATED');
    return response.data;
  },

  async rescheduleSlot(payload: {
    slot_id: string,
    start_time: string,
    end_time?: string,
    duration_minutes?: number,
    force_cascade?: boolean
  }) {
    const response = await apiClient.post('/schedule/reschedule', payload);
    emitEvent('PLANNER_UPDATED');
    return response.data;
  },


  // --- Phase 5: Recovery & Flexibility ---
  skipToday: (data: { entity_id: string; entity_type?: string; schedule_id?: string; reason?: string }) =>
    apiClient.post('/recovery/skip-today', data).then(r => r.data),

  pauseActivity: (data: { entity_id: string; entity_type?: string; reason?: string }) =>
    apiClient.post('/recovery/pause-activity', data).then(r => r.data),

  resumeActivity: (data: { entity_id: string; entity_type?: string }) =>
    apiClient.post('/recovery/resume-activity', data).then(r => r.data),

  getRecoveryItems: () =>
    apiClient.get('/recovery/items').then(r => r.data),

  executeRecoveryAction: (data: { action: string; entity_id: string; entity_type?: string; schedule_id?: string; params?: any }) =>
    apiClient.post('/recovery/action', data).then(r => r.data),

  getSmartRecoveryRecommendations: () =>
    apiClient.get('/recovery/smart-recommendations').then(r => r.data),

  startVacationMode: (data: { start_date: string; end_date: string; suppress_notifications?: boolean; reason?: string }) =>
    apiClient.post('/recovery/vacation/start', data).then(r => r.data),

  endVacationMode: () =>
    apiClient.post('/recovery/vacation/end').then(r => r.data),

  getVacationStatus: () =>
    apiClient.get('/recovery/vacation/status').then(r => r.data),

  activateEmergencyMode: (data?: { reason?: string; auto_skip_non_critical?: boolean }) =>
    apiClient.post('/recovery/emergency/activate', data || {}).then(r => r.data),

  deactivateEmergencyMode: () =>
    apiClient.post('/recovery/emergency/deactivate').then(r => r.data),

  getEmergencyStatus: () =>
    apiClient.get('/recovery/emergency/status').then(r => r.data),

  // Phase 6: AI Intelligence
  getDelayRisk: (entityId?: string) =>
    apiClient.post('/ai/delay-risk', { entity_id: entityId }).then(r => r.data),

  getMissPrediction: () =>
    apiClient.post('/ai/miss-prediction', {}).then(r => r.data),

  getReminderTiming: (slot_duration_minutes: number, priority_score: number) =>
    apiClient.post('/ai/reminder-timing', { slot_duration_minutes, priority_score }).then(r => r.data),

  getWorkloadBalancer: () =>
    apiClient.post('/ai/workload-balancer', {}).then(r => r.data),

  getWorkloadStrain: () =>
    apiClient.post('/ai/workload-strain', {}).then(r => r.data),

  getEnergyPreferences: () =>
    apiClient.get('/ai/energy-preferences').then(r => r.data),

  updateEnergyPreferences: (data: {
    peak_focus_start?: string;
    peak_focus_end?: string;
    low_energy_start?: string;
    low_energy_end?: string;
    preferred_session_duration_minutes?: number;
    preferred_break_duration_minutes?: number;
  }) =>
    apiClient.put('/ai/energy-preferences', data).then(r => r.data),

  getDigitalTwinProfile: () =>
    apiClient.get('/ai/digital-twin/profile').then(r => r.data),

  rebuildDigitalTwinProfile: () =>
    apiClient.post('/ai/digital-twin/rebuild', {}).then(r => r.data),

  resetDigitalTwinProfile: () =>
    apiClient.post('/ai/digital-twin/reset', {}).then(r => r.data),

  getWeeklyCoachReport: (persist: boolean = true) =>
    apiClient.post('/ai/coach/weekly', { persist }).then(r => r.data),

  chatAccountabilityPartner: (message: string, history?: any[]) =>
    apiClient.post('/ai/accountability/chat', { message, history: history || [] }).then(r => r.data),


  // Phase 7: Analytics & Insights
  getMorningBrief: (date?: string) =>
    apiClient.get('/analytics/morning-brief', { params: { date } }).then(r => r.data),

  getEveningReflection: (date?: string) =>
    apiClient.get('/analytics/evening-reflection', { params: { date } }).then(r => r.data),

  getDailyScore: (date?: string) =>
    apiClient.get('/analytics/daily-score', { params: { date } }).then(r => r.data),

  getHabitHealth: () =>
    apiClient.get('/analytics/habit-health').then(r => r.data),

  getGoalProgress: () =>
    apiClient.get('/analytics/goal-progress').then(r => r.data),

  getDeadlineHeatmap: (days: number = 30) =>
    apiClient.get('/analytics/deadline-heatmap', { params: { days } }).then(r => r.data),

  getTimelineAnalytics: (startDate?: string, endDate?: string, limit: number = 50) =>
    apiClient.get('/analytics/timeline', { params: { start_date: startDate, end_date: endDate, limit } }).then(r => r.data),

  getSessionAnalytics: (days: number = 30) =>
    apiClient.get('/analytics/sessions', { params: { days } }).then(r => r.data),

  getTrendsAnalytics: (days: number = 30) =>
    apiClient.get('/analytics/trends', { params: { days } }).then(r => r.data),

  interpretAnalytics: (days: number = 7) =>
    apiClient.post('/analytics/ai/interpret', { days }).then(r => r.data),

  // Phase B1: Business OS Foundation
  createWorkspace: (data: { name: string; legal_name?: string; tax_identifier?: string; base_currency?: string; timezone?: string }) =>
    apiClient.post('/business/workspaces', data).then(r => r.data),

  listWorkspaces: () =>
    apiClient.get('/business/workspaces').then(r => r.data),

  getCurrentWorkspace: () =>
    apiClient.get('/business/workspaces/current').then(r => r.data),

  updateCurrentWorkspace: (data: { name?: string; legal_name?: string; tax_identifier?: string; base_currency?: string; timezone?: string }) =>
    apiClient.patch('/business/workspaces/current', data).then(r => r.data),

  listWorkspaceMembers: () =>
    apiClient.get('/business/members').then(r => r.data),

  inviteWorkspaceMember: (data: { email: string; role?: string }) =>
    apiClient.post('/business/members/invite', data).then(r => r.data),

  updateWorkspaceMemberRole: (memberId: string, role: string) =>
    apiClient.patch(`/business/members/${memberId}/role`, { role }).then(r => r.data),

  listCommercialPartners: (params?: { type?: string; search?: string; status?: string; limit?: number; offset?: number }) =>
    apiClient.get('/business/partners', { params }).then(r => r.data),

  createCommercialPartner: (data: { partner_type: string; name: string; legal_name?: string; phone?: string; email?: string; tax_identifier?: string; credit_period_days?: number }) =>
    apiClient.post('/business/partners', data).then(r => r.data),

  getCommercialPartner: (partnerId: string) =>
    apiClient.get(`/business/partners/${partnerId}`).then(r => r.data),

  updateCommercialPartner: (partnerId: string, data: any) =>
    apiClient.patch(`/business/partners/${partnerId}`, data).then(r => r.data),

  archiveCommercialPartner: (partnerId: string, reason?: string) =>
    apiClient.post(`/business/partners/${partnerId}/archive`, { reason }).then(r => r.data),

  getBusinessAuditLogs: (params?: { entity_type?: string; entity_id?: string; limit?: number; offset?: number }) =>
    apiClient.get('/business/audit', { params }).then(r => r.data),

  // Phase B2: Capture & Staging
  captureText: (text: string) =>
    apiClient.post('/business/capture/text', { text }).then(r => r.data),

  captureUpload: (formData: FormData) =>
    apiClient.post('/business/capture/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data),

  listStagedItems: (params?: { status?: string; candidate_type?: string; limit?: number; offset?: number }) =>
    apiClient.get('/business/staging', { params }).then(r => r.data),

  getStagedItem: (stagingId: string) =>
    apiClient.get(`/business/staging/${stagingId}`).then(r => r.data),

  updateStagedItem: (stagingId: string, data: any) =>
    apiClient.patch(`/business/staging/${stagingId}`, data).then(r => r.data),

  confirmStagedItem: (stagingId: string) =>
    apiClient.post(`/business/staging/${stagingId}/confirm`).then(r => r.data),

  rejectStagedItem: (stagingId: string, reason?: string) =>
    apiClient.post(`/business/staging/${stagingId}/reject`, { reason }).then(r => r.data),

  commitStagedItem: (stagingId: string, targetDomain?: string) =>
    apiClient.post(`/business/staging/${stagingId}/commit`, { target_domain: targetDomain }).then(r => r.data),

  // Phase B3: Ledger, Invoicing & Financial Truth
  listInvoices: (params?: { status?: string; invoice_type?: string; partner_id?: string; limit?: number; offset?: number }) =>
    apiClient.get('/business/invoices', { params }).then(r => r.data),

  createInvoice: (data: any) =>
    apiClient.post('/business/invoices', data).then(r => r.data),

  getInvoice: (invoiceId: string) =>
    apiClient.get(`/business/invoices/${invoiceId}`).then(r => r.data),

  issueInvoice: (invoiceId: string) =>
    apiClient.post(`/business/invoices/${invoiceId}/issue`).then(r => r.data),

  voidInvoice: (invoiceId: string, reason?: string) =>
    apiClient.post(`/business/invoices/${invoiceId}/void`, { reason }).then(r => r.data),

  listTransactions: (params?: { transaction_type?: string; status?: string; partner_id?: string; limit?: number; offset?: number }) =>
    apiClient.get('/business/transactions', { params }).then(r => r.data),

  recordTransaction: (data: any) =>
    apiClient.post('/business/transactions', data).then(r => r.data),

  getTransaction: (transactionId: string) =>
    apiClient.get(`/business/transactions/${transactionId}`).then(r => r.data),

  reverseTransaction: (transactionId: string, reason: string) =>
    apiClient.post(`/business/transactions/${transactionId}/reverse`, { reason }).then(r => r.data),

  allocatePayment: (data: { transaction_id: string; allocations: Array<{ invoice_id: string; allocated_amount: string; notes?: string }> }) =>
    apiClient.post('/business/allocations', data).then(r => r.data),

  getCashPosition: (windowDays?: number) =>
    apiClient.get('/business/financial/cash-position', { params: { window_days: windowDays } }).then(r => r.data),

  getRunway: () =>
    apiClient.get('/business/financial/runway').then(r => r.data),

  // Phase B4: Intelligence, Copilot & Polymorphic Bridge
  askBusinessCopilot: (prompt: string) =>
    apiClient.post('/business/copilot/query', { prompt }).then(r => r.data),

  getBusinessRisks: () =>
    apiClient.get('/business/financial/risks').then(r => r.data),

  getBusinessBridgeFeed: (windowDays?: number) =>
    apiClient.get('/business/bridge/feed', { params: { window_days: windowDays } }).then(r => r.data),

  // Phase B5: Rescue, Collection Reminders & Accountant Export
  getRescueAgingSummary: () =>
    apiClient.get('/business/rescue/aging').then(r => r.data),

  getPriorityReceivables: (limit?: number) =>
    apiClient.get('/business/rescue/priorities', { params: { limit } }).then(r => r.data),

  draftCollectionReminder: (invoiceId: string, tone?: string) =>
    apiClient.post('/business/reminders/draft', { invoice_id: invoiceId, tone }).then(r => r.data),

  sendCollectionReminder: (reminderId: string, customMessage?: string) =>
    apiClient.post(`/business/reminders/${reminderId}/send`, { custom_message: customMessage }).then(r => r.data),

  listCollectionReminders: (invoiceId?: string) =>
    apiClient.get('/business/reminders', { params: { invoice_id: invoiceId } }).then(r => r.data),
};

export const api = DeadlineOSApi;
