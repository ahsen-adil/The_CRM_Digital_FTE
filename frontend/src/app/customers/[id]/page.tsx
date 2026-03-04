'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft, User, Mail, Phone, Ticket,
  MessageSquare, Calendar, Activity, TrendingUp,
  Clock, CheckCircle, AlertCircle, Tag
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
      case 'open': return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200';
      case 'resolved': return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200';
      case 'closed': return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-200';
      default: return 'bg-gray-100 text-gray-700';
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

  if (!customer) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Customer Not Found</h2>
        <Link href="/customers" className="text-primary-600 hover:underline">
          ← Back to Customers
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/customers"
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
            <User className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {customer.name || 'Unnamed Customer'}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">{customer.email}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Tickets */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tickets List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              Tickets ({tickets.length})
            </h2>
            
            {tickets.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                No tickets yet
              </p>
            ) : (
              <div className="space-y-3">
                {tickets.map((ticket, idx) => (
                  <Link
                    key={ticket.id}
                    href={`/tickets/${ticket.id}`}
                    className="block"
                  >
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      whileHover={{ scale: 1.02 }}
                      className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 dark:hover:border-primary-500 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-primary-600 dark:text-primary-400">
                              {ticket.ticket_number}
                            </span>
                            <span className={clsx('px-2 py-0.5 text-xs rounded-full', getStatusColor(ticket.status))}>
                              {ticket.status}
                            </span>
                          </div>
                          <p className="text-gray-700 dark:text-gray-300 text-sm mb-2">
                            {ticket.subject}
                          </p>
                          <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                            <div className="flex items-center gap-1">
                              {getChannelIcon(ticket.channel)}
                              <span className="capitalize">{ticket.channel.replace('_', ' ')}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  </Link>
                ))}
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
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <User className="h-5 w-5" />
              Contact Information
            </h2>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Email</p>
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <p className="font-medium text-gray-900 dark:text-white">{customer.email}</p>
                </div>
              </div>
              
              {customer.phone_number && (
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Phone</p>
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-gray-400" />
                    <p className="font-medium text-gray-900 dark:text-white">{customer.phone_number}</p>
                  </div>
                </div>
              )}
              
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Preferred Channel</p>
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-gray-400" />
                  <p className="font-medium text-gray-900 dark:text-white capitalize">
                    {customer.preferred_channel.replace('_', ' ')}
                  </p>
                </div>
              </div>
              
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Customer Since</p>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <p className="font-medium text-gray-900 dark:text-white">
                    {new Date(customer.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Statistics */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Statistics
            </h2>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Tickets</p>
                <div className="flex items-center gap-2">
                  <Ticket className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{customer.total_tickets}</p>
                </div>
              </div>
              
              {customer.average_sentiment !== null && customer.average_sentiment !== undefined && (
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Average Sentiment</p>
                  <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                    <div className="flex-1">
                      <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                        <div 
                          className={clsx(
                            'h-3 rounded-full transition-all',
                            customer.average_sentiment > 0.7 ? 'bg-green-500' :
                            customer.average_sentiment > 0.3 ? 'bg-yellow-500' :
                            'bg-red-500'
                          )}
                          style={{ width: `${(customer.average_sentiment + 1) * 50}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-lg font-bold text-gray-900 dark:text-white">
                      {(customer.average_sentiment * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {customer.average_sentiment > 0.7 ? 'Positive' :
                     customer.average_sentiment > 0.3 ? 'Neutral' :
                     'Negative'}
                  </p>
                </div>
              )}
            </div>
          </motion.div>

          {/* Activity Summary */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Recent Activity
            </h2>
            
            <div className="space-y-3">
              {tickets.slice(0, 3).map((ticket, idx) => (
                <div key={ticket.id} className="flex items-start gap-3">
                  <div className={clsx(
                    'p-2 rounded-lg',
                    ticket.status === 'resolved' ? 'bg-green-100 dark:bg-green-900' :
                    ticket.status === 'open' ? 'bg-blue-100 dark:bg-blue-900' :
                    'bg-gray-100 dark:bg-gray-700'
                  )}>
                    {ticket.status === 'resolved' ? <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" /> :
                     ticket.status === 'open' ? <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400" /> :
                     <Clock className="h-4 w-4 text-gray-600 dark:text-gray-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {ticket.ticket_number}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {ticket.subject}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
              
              {tickets.length === 0 && (
                <p className="text-gray-500 dark:text-gray-400 text-sm text-center py-4">
                  No recent activity
                </p>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
