import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    window.dispatchEvent(new CustomEvent('deadline_api_error', { 
      detail: error.response?.data?.error || error.message || 'Service Unavailable' 
    }));
    return Promise.reject(error);
  }
);

export const DeadlineOSApi = {
  // ── NOTIFICATIONS ──────────────────────────────────────────────────────
  async getNotifications() {
    const response = await apiClient.get('/notifications');
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

  async runPlanningAgent(payload: { tasks: any[], availability: any }) {
    const response = await apiClient.post('/agents/plan', payload);
    return response.data;
  },

  async runRescueAgent(payload: { tasks: any[], availability: any }) {
    const response = await apiClient.post('/agents/rescue', payload);
    return response.data;
  },

  async runDigitalTwin(payload: { scenario: any }) {
    const response = await apiClient.post('/agents/digital-twin', payload);
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

  async getInterventions() {
    const response = await apiClient.get('/interventions');
    return response.data;
  },

  async runInterventionEngine() {
    const response = await apiClient.post('/interventions/run');
    return response.data;
  },

  async resolveIntervention(id: string) {
    const response = await apiClient.post('/interventions/resolve', { id });
    return response.data;
  },

  async executeIntervention(id: string) {
    const response = await apiClient.post(`/interventions/${id}/execute`);
    return response.data;
  },

  async simulateIntervention(id: string) {
    const response = await apiClient.post(`/interventions/${id}/simulate`);
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
  }
};
