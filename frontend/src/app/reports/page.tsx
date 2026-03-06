'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { BarChart3, TrendingUp, Ticket, Users, CheckCircle, AlertCircle, Sparkles, Activity, PieChart as PieChartIcon } from 'lucide-react';
import { reportsApi } from '@/lib/api';
import { clsx } from 'clsx';

const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#6b7280', '#3b82f6', '#ec4899'];

// Custom tooltip for charts
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700">
        <p className="font-semibold text-gray-900 dark:text-white mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-gray-600 dark:text-gray-400">{entry.name}:</span>
            <span className="font-bold text-gray-900 dark:text-white">{entry.value}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

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
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-4 border-primary-500/30 border-t-primary-500 rounded-full"
        />
      </div>
    );
  }

  const channelData = Object.entries(overview?.by_channel || {}).map(([name, value]) => ({ 
    name: name.replace('_', ' '), 
    value: value as number 
  }));

  const statusData = Object.entries(overview?.by_status || {}).map(([name, value]) => ({ 
    name: name.replace('_', ' '), 
    value: value as number 
  }));

  return (
    <div className="space-y-8">
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
              <BarChart3 className="h-6 w-6 text-white" />
            </motion.div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Reports & Analytics
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Insights and metrics for customer support
          </p>
        </div>
        
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="hidden sm:flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/30 rounded-full"
        >
          <Sparkles className="h-4 w-4 text-primary-500" />
          <span className="text-sm text-primary-600 dark:text-primary-400 font-medium">Real-time Data</span>
        </motion.div>
      </motion.div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Tickets"
          value={overview?.total_tickets || 0}
          icon={Ticket}
          color="from-blue-500 to-blue-600"
          bgColor="bg-blue-500/10"
          delay={0}
        />
        <KPICard
          title="Open Tickets"
          value={overview?.open_tickets || 0}
          icon={AlertCircle}
          color="from-yellow-500 to-yellow-600"
          bgColor="bg-yellow-500/10"
          delay={0.1}
        />
        <KPICard
          title="Resolved"
          value={overview?.resolved_tickets || 0}
          icon={CheckCircle}
          color="from-green-500 to-green-600"
          bgColor="bg-green-500/10"
          delay={0.2}
        />
        <KPICard
          title="Customers"
          value={overview?.total_customers || 0}
          icon={Users}
          color="from-purple-500 to-purple-600"
          bgColor="bg-purple-500/10"
          delay={0.3}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tickets by Channel - Pie Chart */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl">
              <PieChartIcon className="h-5 w-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Tickets by Channel
            </h3>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={channelData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  strokeWidth={3}
                  stroke="rgba(255,255,255,0.1)"
                >
                  {channelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Tickets by Status - Bar Chart */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Tickets by Status
            </h3>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData}>
                <defs>
                  <linearGradient id="colorBar" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" />
                <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" fill="url(#colorBar)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Ticket Trends - Area Chart */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden lg:col-span-2"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-green-500 to-green-600 rounded-xl">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Ticket Trends (Last 7 Days)
            </h3>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends?.trends || []}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorResolved" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorEscalated" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" />
                <XAxis dataKey="date" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorTotal)" name="Total" />
                <Area type="monotone" dataKey="resolved" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorResolved)" name="Resolved" />
                <Area type="monotone" dataKey="escalated" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorEscalated)" name="Escalated" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Sentiment Analysis */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden lg:col-span-2"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-pink-500 to-pink-600 rounded-xl">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Sentiment Analysis
            </h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <SentimentCard 
              label="Positive" 
              value={sentiment?.positive || 0} 
              color="from-green-500 to-green-600"
              bgColor="bg-green-500/10"
              borderColor="border-green-500/30"
              delay={0.7}
            />
            <SentimentCard 
              label="Neutral" 
              value={sentiment?.neutral || 0} 
              color="from-yellow-500 to-yellow-600"
              bgColor="bg-yellow-500/10"
              borderColor="border-yellow-500/30"
              delay={0.75}
            />
            <SentimentCard 
              label="Negative" 
              value={sentiment?.negative || 0} 
              color="from-red-500 to-red-600"
              bgColor="bg-red-500/10"
              borderColor="border-red-500/30"
              delay={0.8}
            />
          </div>
          
          {sentiment?.average_score && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.85 }}
              className="text-center p-6 bg-gradient-to-br from-primary-500/10 to-purple-500/10 rounded-2xl border border-primary-500/30"
            >
              <p className="text-gray-600 dark:text-gray-400 mb-2">Average Sentiment Score</p>
              <motion.div
                initial={{ scale: 0.5 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, delay: 0.9 }}
                className="inline-flex items-center gap-3"
              >
                <p className="text-5xl font-bold bg-gradient-to-r from-primary-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  {(sentiment.average_score * 10).toFixed(1)}/10
                </p>
              </motion.div>
              
              {/* Sentiment meter */}
              <div className="mt-6 max-w-md mx-auto">
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(sentiment.average_score + 1) * 50}%` }}
                    transition={{ delay: 1, duration: 0.8, ease: 'easeOut' }}
                    className={`h-full bg-gradient-to-r ${
                      sentiment.average_score > 0.7 ? 'from-green-500 to-green-600' :
                      sentiment.average_score > 0.3 ? 'from-yellow-500 to-yellow-600' :
                      'from-red-500 to-red-600'
                    }`}
                  />
                </div>
                <div className="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
                  <span>Negative</span>
                  <span>Neutral</span>
                  <span>Positive</span>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

function KPICard({ title, value, icon: Icon, color, bgColor, delay }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, type: 'spring', stiffness: 100 }}
      whileHover={{ y: -5, scale: 1.02 }}
      className="relative group"
    >
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
            <motion.p
              initial={{ scale: 0.5 }}
              animate={{ scale: 1 }}
              transition={{ delay: delay + 0.2, type: 'spring', stiffness: 200 }}
              className="text-4xl font-bold text-gray-900 dark:text-white mt-2"
            >
              {value}
            </motion.p>
          </div>
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: delay + 0.3, type: 'spring', stiffness: 200 }}
            className={`p-4 rounded-xl bg-gradient-to-br ${color} shadow-lg`}
          >
            <Icon className="h-6 w-6 text-white" />
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}

function SentimentCard({ label, value, color, bgColor, borderColor, delay }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -5, scale: 1.03 }}
      className={`p-6 rounded-2xl ${bgColor} backdrop-blur-sm border ${borderColor} transition-all duration-300`}
    >
      <div className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: delay + 0.2, type: 'spring', stiffness: 200 }}
          className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${color} mb-3 shadow-lg`}
        >
          <Activity className="h-6 w-6 text-white" />
        </motion.div>
        <p className="text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{label}</p>
      </div>
    </motion.div>
  );
}
