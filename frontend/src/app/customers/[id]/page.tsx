'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  User,
  Mail,
  Phone,
  Ticket,
  MessageSquare,
  Calendar,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Tag,
  Sparkles,
  Star,
} from 'lucide-react';
import Link from 'next/link';
import { customersApi, ticketsApi } from '@/lib/api';
import { clsx } from 'clsx';

export default function CustomerDetailPage() {
  const params = useParams();
  const customerId = params.id as string;

  const [customer, setCustomer] = useState<any>(null);
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCustomerDetails();
  }, [customerId]);

  const loadCustomerDetails = async () => {
    try {
      setLoading(true);
      const customerData = await customersApi.getById(customerId);
      setCustomer(customerData.customer);
      setTickets(customerData.tickets || []);
    } catch (error) {
      console.error('Failed to load customer:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30';
      case 'resolved': return 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/30';
      case 'closed': return 'bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/30';
      default: return 'bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/30';
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

  const getSentimentGradient = (score?: number) => {
    if (!score) return 'from-gray-500 to-gray-600';
    if (score > 0.7) return 'from-green-500 to-green-600';
    if (score > 0.3) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
  };

  const getSentimentColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score > 0.7) return 'text-green-500';
    if (score > 0.3) return 'text-yellow-500';
    return 'text-red-500';
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

  if (!customer) {
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
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Customer Not Found</h2>
        <Link href="/customers" className="text-primary-600 hover:text-primary-500 hover:underline inline-flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Customers
        </Link>
      </motion.div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4"
      >
        <Link
          href="/customers"
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-700"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex items-center gap-4 flex-1">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
            className="h-16 w-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/30"
          >
            <User className="h-8 w-8 text-white" />
          </motion.div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {customer.name || 'Unnamed Customer'}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">{customer.email}</p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content - Tickets */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tickets List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl">
                  <Ticket className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                  Tickets ({tickets.length})
                </h2>
              </div>
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-primary-500/10 border border-primary-500/30 rounded-full"
              >
                <Sparkles className="h-3.5 w-3.5 text-primary-500" />
                <span className="text-xs text-primary-600 dark:text-primary-400 font-medium">
                  {tickets.filter(t => t.status === 'open').length} Open
                </span>
              </motion.div>
            </div>

            {tickets.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-12"
              >
                <div className="inline-flex p-4 bg-gray-100 dark:bg-gray-700 rounded-full mb-4">
                  <Ticket className="h-8 w-8 text-gray-400" />
                </div>
                <p className="text-gray-500 dark:text-gray-400">No tickets yet</p>
              </motion.div>
            ) : (
              <div className="space-y-3">
                <AnimatePresence>
                  {tickets.map((ticket, idx) => {
                    const channelInfo = getChannelIcon(ticket.channel);
                    return (
                      <Link key={ticket.id} href={`/tickets/${ticket.id}`} className="block">
                        <motion.div
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          whileHover={{ scale: 1.02, x: 4 }}
                          className="p-5 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-primary-500/50 dark:hover:border-primary-500/50 transition-all duration-200 cursor-pointer group bg-gradient-to-r from-transparent via-transparent to-primary-500/0 hover:to-primary-500/5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <span className="font-bold text-primary-600 dark:text-primary-400">
                                  {ticket.ticket_number}
                                </span>
                                <span className={clsx('px-3 py-1 text-xs rounded-lg font-semibold border', getStatusColor(ticket.status))}>
                                  {ticket.status.replace('_', ' ')}
                                </span>
                              </div>
                              <p className="text-gray-700 dark:text-gray-300 text-sm mb-3 line-clamp-1">
                                {ticket.subject}
                              </p>
                              <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                                <div className="flex items-center gap-2">
                                  <div className={`p-1.5 rounded-lg ${channelInfo.bg}`}>
                                    <channelInfo.icon className={`h-3.5 w-3.5 ${channelInfo.color}`} />
                                  </div>
                                  <span className="capitalize">{ticket.channel.replace('_', ' ')}</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <Calendar className="h-3.5 w-3.5" />
                                  <span>
                                    {new Date(ticket.created_at).toLocaleDateString('en-US', {
                                      month: 'short',
                                      day: 'numeric',
                                      year: 'numeric'
                                    })}
                                  </span>
                                </div>
                              </div>
                            </div>
                            <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors opacity-0 group-hover:opacity-100" />
                          </div>
                        </motion.div>
                      </Link>
                    );
                  })}
                </AnimatePresence>
              </div>
            )}
          </motion.div>
        </div>

        {/* Sidebar - Customer Info */}
        <div className="space-y-6">
          {/* Contact Info */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl">
                <User className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                Contact Information
              </h2>
            </div>

            <div className="space-y-5">
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50"
              >
                <div className="p-2 bg-blue-500/10 rounded-lg">
                  <Mail className="h-5 w-5 text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Email</p>
                  <p className="font-medium text-gray-900 dark:text-white truncate">{customer.email}</p>
                </div>
              </motion.div>

              {customer.phone_number && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50"
                >
                  <div className="p-2 bg-green-500/10 rounded-lg">
                    <Phone className="h-5 w-5 text-green-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Phone</p>
                    <p className="font-medium text-gray-900 dark:text-white truncate">{customer.phone_number}</p>
                  </div>
                </motion.div>
              )}

              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50"
              >
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <Tag className="h-5 w-5 text-purple-500" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Preferred Channel</p>
                  <p className="font-medium text-gray-900 dark:text-white capitalize">
                    {customer.preferred_channel.replace('_', ' ')}
                  </p>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50"
              >
                <div className="p-2 bg-orange-500/10 rounded-lg">
                  <Calendar className="h-5 w-5 text-orange-500" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Customer Since</p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {new Date(customer.created_at).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </p>
                </div>
              </motion.div>
            </div>
          </motion.div>

          {/* Statistics */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-green-500 to-green-600 rounded-xl">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                Statistics
              </h2>
            </div>

            <div className="space-y-5">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-4 rounded-xl bg-gradient-to-br from-primary-500/10 to-purple-500/10 border border-primary-500/30"
              >
                <div className="flex items-center gap-3">
                  <Ticket className="h-6 w-6 text-primary-500" />
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Tickets</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">{customer.total_tickets}</p>
                  </div>
                </div>
              </motion.div>

              {customer.average_sentiment !== null && customer.average_sentiment !== undefined && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1 }}
                  className="p-4 rounded-xl bg-gradient-to-br from-pink-500/10 to-red-500/10 border border-pink-500/30"
                >
                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <Activity className="h-6 w-6 text-pink-500" />
                      <div>
                        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Average Sentiment</p>
                        <div className="flex items-center gap-2">
                          <Star className={clsx('h-4 w-4', getSentimentColor(customer.average_sentiment))} />
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {(customer.average_sentiment * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(customer.average_sentiment + 1) * 50}%` }}
                        transition={{ duration: 0.5 }}
                        className={clsx(
                          'h-full rounded-full bg-gradient-to-r',
                          getSentimentGradient(customer.average_sentiment)
                        )}
                      />
                    </div>
                    <p className={clsx('text-sm font-medium mt-2', getSentimentColor(customer.average_sentiment))}>
                      {customer.average_sentiment > 0.7 ? 'Positive' :
                       customer.average_sentiment > 0.3 ? 'Neutral' :
                       'Negative'}
                    </p>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Activity Summary */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl">
                <Clock className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                Recent Activity
              </h2>
            </div>

            <div className="space-y-4">
              {tickets.slice(0, 3).map((ticket, idx) => (
                <motion.div
                  key={ticket.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + idx * 0.05 }}
                  className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className={clsx(
                    'p-2 rounded-lg flex-shrink-0',
                    ticket.status === 'resolved' ? 'bg-green-100 dark:bg-green-900/30' :
                    ticket.status === 'open' ? 'bg-blue-100 dark:bg-blue-900/30' :
                    'bg-gray-100 dark:bg-gray-700'
                  )}>
                    {ticket.status === 'resolved' ? (
                      <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                    ) : ticket.status === 'open' ? (
                      <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    ) : (
                      <Clock className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <Link href={`/tickets/${ticket.id}`}>
                      <p className="text-sm font-bold text-primary-600 dark:text-primary-400 hover:underline truncate">
                        {ticket.ticket_number}
                      </p>
                    </Link>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                      {ticket.subject}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </motion.div>
              ))}

              {tickets.length === 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-6"
                >
                  <p className="text-gray-500 dark:text-gray-400 text-sm">No recent activity</p>
                </motion.div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}
