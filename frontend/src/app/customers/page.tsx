'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Search, Mail, Phone, Ticket, Star, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import { customersApi, Customer as CustomerType } from '@/lib/api';
import Link from 'next/link';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<CustomerType[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0, pages: 1 });

  useEffect(() => {
    const timer = setTimeout(() => {
      loadCustomers();
    }, 500);
    return () => clearTimeout(timer);
  }, [search, pagination.page]);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      const params: any = {
        page: pagination.page,
        limit: pagination.limit,
      };
      if (search) params.search = search;

      const data = await customersApi.getAll(params);
      setCustomers(data.customers);
      setPagination(prev => ({ ...prev, ...data.pagination }));
    } catch (error) {
      console.error('Failed to load customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score > 0.7) return 'text-green-500';
    if (score > 0.3) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getSentimentGradient = (score?: number) => {
    if (!score) return 'from-gray-500 to-gray-600';
    if (score > 0.7) return 'from-green-500 to-green-600';
    if (score > 0.3) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <div className="flex items-center gap-3">
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl shadow-lg shadow-primary-500/30"
            >
              <Users className="h-6 w-6 text-white" />
            </motion.div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Customers</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            View and manage customer accounts
          </p>
        </div>
        
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="hidden sm:flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/30 rounded-full"
        >
          <Sparkles className="h-4 w-4 text-primary-500" />
          <span className="text-sm text-primary-600 dark:text-primary-400 font-medium">
            {pagination.total} Total
          </span>
        </motion.div>
      </motion.div>

      {/* Search - Enhanced */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6"
      >
        <div className="relative max-w-md">
          <motion.div 
            className="absolute left-4 top-1/2 transform -translate-y-1/2"
            animate={{ x: [0, 5, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
          >
            <Search className="h-5 w-5 text-gray-400" />
          </motion.div>
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white transition-all duration-200"
          />
          {search && (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
            >
              <span className="text-gray-400 text-sm">✕</span>
            </motion.button>
          )}
        </div>
      </motion.div>

      {/* Customers Grid - Enhanced */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        <AnimatePresence mode="wait">
          {loading ? (
            <div className="col-span-full flex justify-center py-16">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-12 h-12 border-4 border-primary-500/30 border-t-primary-500 rounded-full"
              />
            </div>
          ) : customers.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="col-span-full flex flex-col items-center justify-center py-16"
            >
              <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
                <Users className="h-12 w-12 text-gray-400" />
              </div>
              <p className="text-gray-500 dark:text-gray-400 text-lg">No customers found</p>
            </motion.div>
          ) : (
            customers.map((customer, index) => (
              <Link key={customer.id} href={`/customers/${customer.id}`} className="block group">
                <motion.div
                  key={customer.id}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -30 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ y: -8, scale: 1.02 }}
                  className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden transition-all duration-300 group-hover:shadow-xl group-hover:shadow-primary-500/10"
                >
                  {/* Gradient overlay on hover */}
                  <div className="absolute inset-0 bg-gradient-to-br from-primary-500/0 via-primary-500/0 to-primary-500/5 group-hover:via-primary-500/5 transition-all duration-300" />
                  
                  {/* Card content */}
                  <div className="relative">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3 flex-1">
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ type: 'spring', stiffness: 200, delay: index * 0.05 + 0.2 }}
                          className="p-3 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl shadow-lg shadow-primary-500/30"
                        >
                          <Users className="h-5 w-5 text-white" />
                        </motion.div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-bold text-gray-900 dark:text-white truncate group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                            {customer.name || 'Unnamed Customer'}
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                            {customer.email}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Info Grid */}
                    <div className="space-y-3">
                      {customer.phone_number && (
                        <motion.div
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 + 0.3 }}
                          className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                        >
                          <div className="p-1.5 bg-blue-500/10 rounded-lg">
                            <Phone className="h-4 w-4 text-blue-500" />
                          </div>
                          <span className="truncate">{customer.phone_number}</span>
                        </motion.div>
                      )}

                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 + 0.35 }}
                        className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                      >
                        <div className="p-1.5 bg-purple-500/10 rounded-lg">
                          <Ticket className="h-4 w-4 text-purple-500" />
                        </div>
                        <span>{customer.total_tickets} tickets</span>
                      </motion.div>

                      {customer.average_sentiment !== null && customer.average_sentiment !== undefined && (
                        <motion.div
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 + 0.4 }}
                          className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                        >
                          <div className={`p-1.5 rounded-lg bg-gradient-to-br ${getSentimentGradient(customer.average_sentiment)}`}>
                            <Star className="h-4 w-4 text-white" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className={`text-sm font-bold ${getSentimentColor(customer.average_sentiment)}`}>
                                {(customer.average_sentiment * 10).toFixed(1)}/10
                              </span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">sentiment</span>
                            </div>
                            {/* Sentiment bar */}
                            <div className="mt-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${(customer.average_sentiment + 1) * 50}%` }}
                                transition={{ delay: index * 0.05 + 0.5, duration: 0.5 }}
                                className={`h-full bg-gradient-to-r ${getSentimentGradient(customer.average_sentiment)}`}
                              />
                            </div>
                          </div>
                        </motion.div>
                      )}

                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 + 0.45 }}
                        className="pt-3 border-t border-gray-200 dark:border-gray-700"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            Preferred:
                          </span>
                          <span className="text-xs font-semibold px-2 py-1 bg-primary-500/10 text-primary-600 dark:text-primary-400 rounded-lg capitalize">
                            {customer.preferred_channel.replace('_', ' ')}
                          </span>
                        </div>
                      </motion.div>
                    </div>

                    {/* Arrow indicator */}
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 + 0.5 }}
                      className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <div className="p-2 bg-primary-500 rounded-lg shadow-lg">
                        <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </motion.div>
                  </div>
                </motion.div>
              </Link>
            ))
          )}
        </AnimatePresence>
      </motion.div>

      {/* Pagination - Enhanced */}
      {!loading && customers.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-center gap-2"
        >
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
            disabled={pagination.page === 1}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white dark:hover:bg-gray-700 transition-all duration-200"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Previous</span>
          </motion.button>
          
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            className="px-4 py-2 bg-primary-500/10 border border-primary-500/30 rounded-xl text-primary-600 dark:text-primary-400 font-semibold"
          >
            Page {pagination.page} of {pagination.pages}
          </motion.div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
            disabled={pagination.page >= pagination.pages}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white dark:hover:bg-gray-700 transition-all duration-200"
          >
            <span>Next</span>
            <ChevronRight className="h-4 w-4" />
          </motion.button>
        </motion.div>
      )}
    </div>
  );
}
