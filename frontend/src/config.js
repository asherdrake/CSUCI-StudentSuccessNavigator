// Read API URL from configuration, fallback to local dev server
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/chat';

export const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'bot',
  content:
    'Hello! I am the CSUCI Student Success Navigator. How can I help you find registration, advising, degree requirements, or financial aid information today?',
  citations: [],
  escalation: null
};
