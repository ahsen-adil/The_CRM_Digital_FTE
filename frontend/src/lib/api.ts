import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Ticket {
  id: string;
  ticket_number: string;
  customer_id: string;
  customer_name?: string;
  customer_email?: string;
  channel: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  category?: string;
  sentiment_score?: number;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  email: string;
  name?: string;
  phone_number?: string;
  total_tickets: number;
  average_sentiment?: number;
  preferred_channel: string;
  created_at: string;
}

export interface TicketStats {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  escalated_tickets: number;
  avg_response_time_hours: number;
  by_channel?: {
    email: number;
    whatsapp: number;
    web_form: number;
  };
  by_status?: Record<string, number>;
}

export const ticketsApi = {
  getAll: async (params?: { status?: string; channel?: string; priority?: string; page?: number; limit?: number }) => {
    const response = await api.get('/api/v1/tickets', { params });
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/api/v1/tickets/${id}`);
    return response.data;
  },

  update: async (id: string, data: { status?: string; priority?: string; assigned_to?: string }) => {
    const response = await api.patch(`/api/v1/tickets/${id}`, data);
    return response.data;
  },

  getStats: async () => {
    const allTickets: any[] = [];
    let page = 1;
    const limit = 100;
    let hasMore = true;

    while (hasMore) {
      const response = await api.get('/api/v1/tickets', {
        params: { page, limit }
      });
      const tickets = response.data.tickets || [];
      allTickets.push(...tickets);

      hasMore = tickets.length === limit && page < (response.data.pagination?.pages || 0);
      page++;

      if (page > 50) break;
    }

    return {
      total_tickets: allTickets.length,
      open_tickets: allTickets.filter((t: any) => t.status === 'open').length,
      resolved_tickets: allTickets.filter((t: any) => t.status === 'resolved').length,
      escalated_tickets: allTickets.filter((t: any) => t.status === 'escalated').length,
      avg_response_time_hours: 2.5,
      by_channel: {
        email: allTickets.filter((t: any) => t.channel === 'email').length,
        whatsapp: allTickets.filter((t: any) => t.channel === 'whatsapp').length,
        web_form: allTickets.filter((t: any) => t.channel === 'web_form').length,
      },
      by_status: allTickets.reduce((acc: any, t: any) => {
        acc[t.status] = (acc[t.status] || 0) + 1;
        return acc;
      }, {}),
    };
  },
};

export const customersApi = {
  getAll: async (params?: { search?: string; page?: number; limit?: number }) => {
    const response = await api.get('/api/v1/customers', { params });
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/api/v1/customers/${id}`);
    return response.data;
  },
};

export const reportsApi = {
  getOverview: async () => {
    const response = await api.get('/api/v1/reports/overview');
    return response.data;
  },

  getTrends: async (days: number = 7) => {
    const response = await api.get('/api/v1/reports/trends', { params: { days } });
    return response.data;
  },

  getSentiment: async () => {
    const response = await api.get('/api/v1/reports/sentiment');
    return response.data;
  },
};

export const webformApi = {
  submit: async (data: {
    name: string;
    email: string;
    subject: string;
    message: string;
    priority?: string;
  }) => {
    const webformUrl = process.env.NEXT_PUBLIC_WEBFORM_URL || 'http://localhost:8001';
    const response = await axios.post(`${webformUrl}/api/v1/webform/submit`, data, {
      headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
  },
};

export const healthApi = {
  check: async () => {
    const response = await api.get('/api/v1/health');
    return response.data;
  },
};

export default api;
