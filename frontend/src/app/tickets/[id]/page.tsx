'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Ticket,
  User,
  Calendar,
  Clock,
  MessageSquare,
  CheckCircle,
  AlertCircle,
  Mail,
  Phone,
  Tag,
  Activity,
  Sparkles,
  ChevronRight,
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
      case 'open': return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30';
      case 'in_progress': return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30';
      case 'resolved': return 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/30';
      case 'escalated': return 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30';
      case 'closed': return 'bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/30';
      default: return 'bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/30';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500 shadow-lg shadow-red-500/50';
      case 'high': return 'bg-orange-500 shadow-lg shadow-orange-500/50';
      case 'normal': return 'bg-blue-500 shadow-lg shadow-blue-500/50';
      case 'low': return 'bg-gray-500 shadow-lg shadow-gray-500/50';
      default: return 'bg-gray-500';
    }
  };

  const getPriorityGradient = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'from-red-500 to-red-600';
      case 'high': return 'from-orange-500 to-orange-600';
      case 'normal': return 'from-blue-500 to-blue-600';
      case 'low': return 'from-gray-500 to-gray-600';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email': return { icon: Mail, color: 'text-blue-500', bg: 'bg-blue-500/10' };
      case 'whatsapp': return { icon: MessageSquare, color: 'text-green-500', bg: 'bg-green-500/10' };
      case 'web_form': return { icon: Ticket, color: 'text-purple-500', bg: 'bg-purple-500/10' };
      default: return { icon: Ticket, color: 'text-gray-500', bg: 'bg-gray-500/10' };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-4 border-primary-500/30 border-t-primary-500 rounded-full"
        />
      </div>
    );
  }

  if (!ticket) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center py-12"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200 }}
          className="inline-flex p-4 bg-red-500/10 rounded-full mb-4"
        >
          <AlertCircle className="h-16 w-16 text-red-500" />
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Ticket Not Found</h2>
        <Link href="/tickets" className="text-primary-600 hover:text-primary-500 hover:underline inline-flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Tickets
        </Link>
      </motion.div>
    );
  }

  const channelInfo = getChannelIcon(ticket.channel);

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4"
      >
        <Link
          href="/tickets"
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-700"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <motion.h1
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white"
            >
              {ticket.ticket_number}
            </motion.h1>
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className={clsx('px-4 py-1.5 text-sm rounded-xl font-semibold border', getStatusColor(ticket.status))}
            >
              {ticket.status.replace('_', ' ')}
            </motion.span>
          </div>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-gray-600 dark:text-gray-400 mt-1"
          >
            {ticket.subject}
          </motion.p>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content - Conversation */}
        <div className="lg:col-span-2 space-y-6">
          {/* Ticket Description */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl">
                <MessageSquare className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Description</h2>
            </div>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{ticket.description}</p>

            <div className="mt-6 flex flex-wrap gap-3">
              <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <div className={`p-1.5 rounded-lg ${channelInfo.bg}`}>
                  <channelInfo.icon className={`h-4 w-4 ${channelInfo.color}`} />
                </div>
                <span className="text-sm font-medium capitalize">{ticket.channel.replace('_', ' ')}</span>
              </div>
              
              <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <div className={`w-3 h-3 rounded-full ${getPriorityColor(ticket.priority)}`} />
                <span className="text-sm font-medium capitalize">{ticket.priority}</span>
              </div>
              
              {ticket.sentiment_score && (
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <Activity className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium">Sentiment: {(ticket.sentiment_score * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
          </motion.div>

          {/* Conversation History */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl">
                <MessageSquare className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                Conversation History
              </h2>
            </div>

            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-12"
              >
                <div className="inline-flex p-4 bg-gray-100 dark:bg-gray-700 rounded-full mb-4">
                  <MessageSquare className="h-8 w-8 text-gray-400" />
                </div>
                <p className="text-gray-500 dark:text-gray-400">No messages yet</p>
              </motion.div>
            ) : (
              <div className="space-y-4">
                <AnimatePresence>
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={msg.id || idx}
                      initial={{ opacity: 0, x: msg.direction === 'inbound' ? -30 : 30 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      whileHover={{ scale: 1.01 }}
                      className={clsx(
                        'p-5 rounded-2xl border',
                        msg.direction === 'inbound'
                          ? 'bg-gray-50 dark:bg-gray-700/50 border-gray-200/50 dark:border-gray-700/50 ml-8'
                          : 'bg-gradient-to-br from-primary-500/10 to-primary-600/10 border-primary-500/30 mr-8'
                      )}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={clsx(
                            'p-2 rounded-xl',
                            msg.direction === 'inbound'
                              ? 'bg-gray-200 dark:bg-gray-600'
                              : 'bg-primary-500'
                          )}>
                            {msg.direction === 'inbound' ? (
                              <User className="h-4 w-4 text-gray-600 dark:text-gray-300" />
                            ) : (
                              <User className="h-4 w-4 text-white" />
                            )}
                          </div>
                          <div>
                            <span className="text-sm font-bold text-gray-900 dark:text-white">
                              {msg.direction === 'inbound' ? 'Customer' : 'Support Team'}
                            </span>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {new Date(msg.sent_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <span className={clsx(
                          'px-3 py-1 text-xs rounded-full font-semibold',
                          msg.direction === 'inbound'
                            ? 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300'
                            : 'bg-primary-500 text-white'
                        )}>
                          {msg.direction === 'inbound' ? 'Received' : 'Sent'}
                        </span>
                      </div>
                      <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </motion.div>
                  ))}
                </AnimatePresence>
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
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl">
                  <User className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Customer</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Name</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{customer.name || 'N/A'}</p>
                </div>

                <div>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Email</p>
                  <p className="font-medium text-gray-900 dark:text-white">{customer.email}</p>
                </div>

                {customer.phone_number && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Phone</p>
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4 text-gray-400" />
                      <p className="font-medium text-gray-900 dark:text-white">{customer.phone_number}</p>
                    </div>
                  </div>
                )}

                <div>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Total Tickets</p>
                  <div className="flex items-center gap-2">
                    <Ticket className="h-4 w-4 text-primary-500" />
                    <p className="font-bold text-gray-900 dark:text-white">{customer.total_tickets}</p>
                  </div>
                </div>

                {customer.average_sentiment && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Avg Sentiment</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(customer.average_sentiment + 1) * 50}%` }}
                          transition={{ duration: 0.5 }}
                          className={clsx(
                            'h-full rounded-full bg-gradient-to-r',
                            customer.average_sentiment > 0.7 ? 'from-green-500 to-green-600' :
                            customer.average_sentiment > 0.3 ? 'from-yellow-500 to-yellow-600' :
                            'from-red-500 to-red-600'
                          )}
                        />
                      </div>
                      <span className="text-sm font-bold">{(customer.average_sentiment * 100).toFixed(0)}%</span>
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
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl">
                <Ticket className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Ticket Details</h2>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Created</p>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <p className="font-medium text-gray-900 dark:text-white">
                    {new Date(ticket.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Last Updated</p>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <p className="font-medium text-gray-900 dark:text-white">
                    {new Date(ticket.updated_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
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
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-green-500 to-green-600 rounded-xl">
                <CheckCircle className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Actions</h2>
            </div>

            <div className="space-y-3">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => updateTicketStatus('in_progress')}
                disabled={updating || ticket.status === 'in_progress'}
                className="w-full px-4 py-3 bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-400 hover:to-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-semibold transition-all duration-300 shadow-lg shadow-yellow-500/30"
              >
                Mark In Progress
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => updateTicketStatus('resolved')}
                disabled={updating || ticket.status === 'resolved'}
                className="w-full px-4 py-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-400 hover:to-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-semibold transition-all duration-300 shadow-lg shadow-green-500/30"
              >
                Mark Resolved
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => updateTicketStatus('closed')}
                disabled={updating || ticket.status === 'closed'}
                className="w-full px-4 py-3 bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-400 hover:to-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-semibold transition-all duration-300 shadow-lg shadow-gray-500/30"
              >
                Close Ticket
              </motion.button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
