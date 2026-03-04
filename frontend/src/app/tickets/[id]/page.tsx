'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, Ticket, User, Calendar, Clock, 
  MessageSquare, CheckCircle, AlertCircle, 
  Mail, Phone, Tag, Activity
} from 'lucide-react';
import Link from 'next/link';
import { ticketsApi, customersApi } from '@/lib/api';
import { clsx } from 'clsx';

export default function TicketDetailPage() {
  const params = useParams();
  const ticketId = params.id as string;
  
  const [ticket, setTicket] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [customer, setCustomer] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadTicketDetails();
  }, [ticketId]);

  const loadTicketDetails = async () => {
    try {
      setLoading(true);
      const ticketData = await ticketsApi.getById(ticketId);
      setTicket(ticketData.ticket);
      setMessages(ticketData.messages || []);
      
      // Load customer details
      if (ticketData.ticket.customer_id) {
        const customerData = await customersApi.getById(ticketData.ticket.customer_id);
        setCustomer(customerData.customer);
      }
    } catch (error) {
      console.error('Failed to load ticket:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateTicketStatus = async (newStatus: string) => {
    try {
      setUpdating(true);
      await ticketsApi.update(ticketId, { status: newStatus });
      await loadTicketDetails();
    } catch (error) {
      console.error('Failed to update status:', error);
    } finally {
      setUpdating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200';
      case 'in_progress': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200';
      case 'resolved': return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200';
      case 'escalated': return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200';
      case 'closed': return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'normal': return 'bg-blue-500';
      case 'low': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email': return <Mail className="h-4 w-4" />;
      case 'whatsapp': return <MessageSquare className="h-4 w-4" />;
      case 'web_form': return <Ticket className="h-4 w-4" />;
      default: return <Ticket className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Ticket Not Found</h2>
        <Link href="/tickets" className="text-primary-600 hover:underline">
          ← Back to Tickets
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/tickets"
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {ticket.ticket_number}
            </h1>
            <span className={clsx('px-3 py-1 text-sm rounded-full font-medium', getStatusColor(ticket.status))}>
              {ticket.status}
            </span>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mt-1">{ticket.subject}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Conversation */}
        <div className="lg:col-span-2 space-y-6">
          {/* Ticket Description */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Description</h2>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{ticket.description}</p>
            
            <div className="mt-4 flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center gap-1">
                {getChannelIcon(ticket.channel)}
                <span className="capitalize">{ticket.channel.replace('_', ' ')}</span>
              </div>
              <div className="flex items-center gap-1">
                <div className={clsx('w-2 h-2 rounded-full', getPriorityColor(ticket.priority))} />
                <span className="capitalize">{ticket.priority}</span>
              </div>
              {ticket.sentiment_score && (
                <div className="flex items-center gap-1">
                  <Activity className="h-4 w-4" />
                  <span>Sentiment: {(ticket.sentiment_score * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
          </motion.div>

          {/* Conversation History */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Conversation History
            </h2>
            
            {messages.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                No messages yet
              </p>
            ) : (
              <div className="space-y-4">
                {messages.map((msg, idx) => (
                  <motion.div
                    key={msg.id || idx}
                    initial={{ opacity: 0, x: msg.direction === 'inbound' ? -20 : 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className={clsx(
                      'p-4 rounded-lg',
                      msg.direction === 'inbound' 
                        ? 'bg-gray-100 dark:bg-gray-700 ml-8'
                        : 'bg-primary-100 dark:bg-primary-900 mr-8'
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {msg.direction === 'inbound' ? 'Customer' : 'Support'}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(msg.sent_at).toLocaleString()}
                        </span>
                      </div>
                      <span className={clsx('px-2 py-1 text-xs rounded-full', msg.direction === 'inbound' ? 'bg-gray-200 dark:bg-gray-600' : 'bg-primary-200 dark:bg-primary-800')}>
                        {msg.direction === 'inbound' ? 'Received' : 'Sent'}
                      </span>
                    </div>
                    <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{msg.content}</p>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        </div>

        {/* Sidebar - Customer Info & Actions */}
        <div className="space-y-6">
          {/* Customer Info */}
          {customer && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <User className="h-5 w-5" />
                Customer
              </h2>
              
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Name</p>
                  <p className="font-medium text-gray-900 dark:text-white">{customer.name || 'N/A'}</p>
                </div>
                
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
                  <p className="font-medium text-gray-900 dark:text-white">{customer.email}</p>
                </div>
                
                {customer.phone_number && (
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Phone</p>
                    <div className="flex items-center gap-1">
                      <Phone className="h-4 w-4" />
                      <p className="font-medium text-gray-900 dark:text-white">{customer.phone_number}</p>
                    </div>
                  </div>
                )}
                
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Total Tickets</p>
                  <p className="font-medium text-gray-900 dark:text-white">{customer.total_tickets}</p>
                </div>
                
                {customer.average_sentiment && (
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Avg Sentiment</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full"
                          style={{ width: `${(customer.average_sentiment + 1) * 50}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{(customer.average_sentiment * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Ticket Info */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              Ticket Details
            </h2>
            
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Created</p>
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <p className="font-medium text-gray-900 dark:text-white">
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Last Updated</p>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  <p className="font-medium text-gray-900 dark:text-white">
                    {new Date(ticket.updated_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Status Actions */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              Actions
            </h2>
            
            <div className="space-y-2">
              <button
                onClick={() => updateTicketStatus('in_progress')}
                disabled={updating || ticket.status === 'in_progress'}
                className="w-full px-4 py-2 bg-yellow-500 hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                Mark In Progress
              </button>
              
              <button
                onClick={() => updateTicketStatus('resolved')}
                disabled={updating || ticket.status === 'resolved'}
                className="w-full px-4 py-2 bg-green-500 hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                Mark Resolved
              </button>
              
              <button
                onClick={() => updateTicketStatus('closed')}
                disabled={updating || ticket.status === 'closed'}
                className="w-full px-4 py-2 bg-gray-500 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                Close Ticket
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
