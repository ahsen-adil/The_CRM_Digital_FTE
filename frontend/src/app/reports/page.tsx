'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { BarChart3, TrendingUp, Ticket, Users, CheckCircle, AlertCircle } from 'lucide-react';
import { reportsApi } from '@/lib/api';

const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#6b7280'];

export default function ReportsPage() {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const [overviewData, trendsData, sentimentData] = await Promise.all([
        reportsApi.getOverview(),
        reportsApi.getTrends(7),
        reportsApi.getSentiment(),
      ]);
      setOverview(overviewData);
      setTrends(trendsData);
      setSentiment(sentimentData);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Reports & Analytics</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Insights and metrics for customer support
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Tickets"
          value={overview?.total_tickets || 0}
          icon={Ticket}
          color="bg-blue-500"
        />
        <KPICard
          title="Open Tickets"
          value={overview?.open_tickets || 0}
          icon={AlertCircle}
          color="bg-yellow-500"
        />
        <KPICard
          title="Resolved"
          value={overview?.resolved_tickets || 0}
          icon={CheckCircle}
          color="bg-green-500"
        />
        <KPICard
          title="Customers"
          value={overview?.total_customers || 0}
          icon={Users}
          color="bg-purple-500"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tickets by Channel */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Tickets by Channel
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={Object.entries(overview?.by_channel || {}).map(([name, value]) => ({ name, value }))}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {Object.keys(overview?.by_channel || {}).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Tickets by Status */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Tickets by Status
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(overview?.by_status || {}).map(([name, value]) => ({ name, value }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Ticket Trends */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 lg:col-span-2"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Ticket Trends (Last 7 Days)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends?.trends || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#8b5cf6" name="Total" />
              <Line type="monotone" dataKey="resolved" stroke="#10b981" name="Resolved" />
              <Line type="monotone" dataKey="escalated" stroke="#ef4444" name="Escalated" />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Sentiment Analysis */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 lg:col-span-2"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Sentiment Analysis
          </h3>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <SentimentCard label="Positive" value={sentiment?.positive || 0} color="green" />
            <SentimentCard label="Neutral" value={sentiment?.neutral || 0} color="yellow" />
            <SentimentCard label="Negative" value={sentiment?.negative || 0} color="red" />
          </div>
          {sentiment?.average_score && (
            <div className="text-center">
              <p className="text-gray-600 dark:text-gray-400">Average Sentiment Score</p>
              <p className="text-4xl font-bold text-primary-600 mt-2">
                {(sentiment.average_score * 10).toFixed(1)}/10
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

function KPICard({ title, value, icon: Icon, color }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{value}</p>
        </div>
        <div className={clsx('p-4 rounded-full', color)}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </motion.div>
  );
}

function SentimentCard({ label, value, color }: any) {
  const colorClasses = {
    green: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200',
    yellow: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200',
    red: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200',
  };

  return (
    <div className={clsx('p-4 rounded-lg text-center', colorClasses[color as keyof typeof colorClasses])}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm mt-1">{label}</p>
    </div>
  );
}

function clsx(...classes: any[]) {
  return classes.filter(Boolean).join(' ');
}
