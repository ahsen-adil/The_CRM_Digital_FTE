'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Ticket,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Mail,
  MessageSquare,
  Monitor,
  Sparkles,
  Zap,
  Activity,
} from 'lucide-react';
import { ticketsApi, TicketStats } from '@/lib/api';
import { clsx } from 'clsx';

interface ChannelStats {
  email: number;
  whatsapp: number;
  webform: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [channelStats, setChannelStats] = useState<ChannelStats>({
    email: 0,
    whatsapp: 0,
    webform: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await ticketsApi.getStats();
      setStats(data);
      setChannelStats({
        email: data.by_channel?.email || 0,
        whatsapp: data.by_channel?.whatsapp || 0,
        webform: data.by_channel?.web_form || 0,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const kpiCards = [
    {
      title: 'Total Tickets',
      value: stats?.total_tickets ?? 0,
      icon: Ticket,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/30',
      textColor: 'text-blue-600 dark:text-blue-400',
      trend: '+12%',
      trendUp: true,
    },
    {
      title: 'Open Tickets',
      value: stats?.open_tickets ?? 0,
      icon: Clock,
      color: 'from-yellow-500 to-yellow-600',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/30',
      textColor: 'text-yellow-600 dark:text-yellow-400',
      trend: '-5%',
      trendUp: false,
    },
    {
      title: 'Resolved',
      value: stats?.resolved_tickets ?? 0,
      icon: CheckCircle,
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/30',
      textColor: 'text-green-600 dark:text-green-400',
      trend: '+18%',
      trendUp: true,
    },
    {
      title: 'Escalated',
      value: stats?.escalated_tickets ?? 0,
      icon: AlertCircle,
      color: 'from-red-500 to-red-600',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/30',
      textColor: 'text-red-600 dark:text-red-400',
      trend: '-2%',
      trendUp: true,
    },
  ];

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
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl shadow-lg shadow-primary-500/30"
            >
              <LayoutDashboardIcon className="h-6 w-6 text-white" />
            </motion.div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Dashboard
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Overview of your customer support metrics
          </p>
        </div>
        
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="hidden sm:flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/30 rounded-full"
        >
          <Sparkles className="h-4 w-4 text-primary-500" />
          <span className="text-sm text-primary-600 dark:text-primary-400 font-medium">Live Updates</span>
        </motion.div>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, type: 'spring', stiffness: 100 }}
            whileHover={{ y: -8, scale: 1.02 }}
            className="relative group"
          >
            {/* Card background with gradient border effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-gray-200/50 dark:to-gray-800/50 rounded-2xl" />
            <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden">
              {/* Gradient overlay on hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${card.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
              
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {card.title}
                    </p>
                  </div>
                  <motion.p
                    initial={{ scale: 0.5 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: index * 0.1 + 0.2, type: 'spring', stiffness: 200 }}
                    className="text-4xl font-bold text-gray-900 dark:text-white"
                  >
                    {card.value}
                  </motion.p>
                  
                  <div className="flex items-center mt-3 gap-2">
                    <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${card.trendUp ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                      {card.trendUp ? (
                        <TrendingUp className="h-3.5 w-3.5 text-green-500" />
                      ) : (
                        <TrendingDown className="h-3.5 w-3.5 text-red-500" />
                      )}
                      <span className={`text-sm font-semibold ${card.trendUp ? 'text-green-500' : 'text-red-500'}`}>
                        {card.trend}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400 dark:text-gray-500">
                      vs last month
                    </span>
                  </div>
                </div>
                
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ delay: index * 0.1 + 0.3, type: 'spring', stiffness: 200 }}
                  className={`p-4 rounded-xl bg-gradient-to-br ${card.color} shadow-lg`}
                >
                  <card.icon className="h-6 w-6 text-white" />
                </motion.div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Channel Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Channel Stats */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ y: -2 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden relative"
        >
          {/* Decorative element */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary-500/10 to-transparent rounded-bl-full" />
          
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Tickets by Channel
            </h2>
          </div>
          
          <div className="space-y-4">
            <ChannelStatCard
              icon={Mail}
              name="Email"
              count={channelStats.email}
              color="from-blue-500 to-blue-600"
              bgColor="bg-blue-500/10"
              percentage={
                stats?.total_tickets
                  ? Math.round((channelStats.email / stats.total_tickets) * 100)
                  : 0
              }
              delay={0.5}
            />
            <ChannelStatCard
              icon={MessageSquare}
              name="WhatsApp"
              count={channelStats.whatsapp}
              color="from-green-500 to-green-600"
              bgColor="bg-green-500/10"
              percentage={
                stats?.total_tickets
                  ? Math.round((channelStats.whatsapp / stats.total_tickets) * 100)
                  : 0
              }
              delay={0.6}
            />
            <ChannelStatCard
              icon={Monitor}
              name="Web Form"
              count={channelStats.webform}
              color="from-purple-500 to-purple-600"
              bgColor="bg-purple-500/10"
              percentage={
                stats?.total_tickets
                  ? Math.round((channelStats.webform / stats.total_tickets) * 100)
                  : 0
              }
              delay={0.7}
            />
          </div>
        </motion.div>

        {/* Performance Metrics */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ y: -2 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden relative"
        >
          {/* Decorative element */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-green-500/10 to-transparent rounded-bl-full" />
          
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-green-500 to-green-600 rounded-xl">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Performance Metrics
            </h2>
          </div>
          
          <div className="space-y-4">
            <MetricRow
              label="Avg. Response Time"
              value={`${stats?.avg_response_time_hours ?? 0}h`}
              target="< 4h"
              status="good"
              delay={0.5}
            />
            <MetricRow
              label="Resolution Rate"
              value="87%"
              target="> 85%"
              status="good"
              delay={0.6}
            />
            <MetricRow
              label="Escalation Rate"
              value={
                stats?.total_tickets
                  ? `${Math.round((stats.escalated_tickets / stats.total_tickets) * 100)}%`
                  : '0%'
              }
              target="< 20%"
              status="good"
              delay={0.7}
            />
            <MetricRow
              label="Customer Satisfaction"
              value="4.6/5"
              target="> 4.5"
              status="good"
              delay={0.8}
            />
          </div>
        </motion.div>
      </div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl">
            <CheckCircle className="h-5 w-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            System Status
          </h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatusCard name="Email Service" status="operational" delay={0.9} />
          <StatusCard name="WhatsApp Service" status="operational" delay={1} />
          <StatusCard name="Web Form" status="operational" delay={1.1} />
        </div>
      </motion.div>
    </div>
  );
}

function ChannelStatCard({
  icon: Icon,
  name,
  count,
  color,
  bgColor,
  percentage,
  delay,
}: {
  icon: any;
  name: string;
  count: number;
  color: string;
  bgColor: string;
  percentage: number;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      whileHover={{ x: 4, scale: 1.02 }}
      className={`flex items-center justify-between p-4 ${bgColor} rounded-xl border border-gray-200/50 dark:border-gray-700/50 transition-all duration-200 group cursor-pointer`}
    >
      <div className="flex items-center gap-3">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: delay + 0.2, type: 'spring', stiffness: 200 }}
          className={`p-3 rounded-full bg-gradient-to-br ${color} shadow-lg`}
        >
          <Icon className="h-5 w-5 text-white" />
        </motion.div>
        <div>
          <p className="font-semibold text-gray-900 dark:text-white">{name}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{count} tickets</p>
        </div>
      </div>
      <div className="text-right">
        <motion.p
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: delay + 0.3, type: 'spring', stiffness: 200 }}
          className="text-2xl font-bold text-gray-900 dark:text-white"
        >
          {percentage}%
        </motion.p>
        <p className="text-xs text-gray-500 dark:text-gray-400">of total</p>
      </div>
    </motion.div>
  );
}

function MetricRow({
  label,
  value,
  target,
  status,
  delay,
}: {
  label: string;
  value: string;
  target: string;
  status: 'good' | 'warning' | 'bad';
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      whileHover={{ x: 4, scale: 1.01 }}
      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-gray-200/50 dark:border-gray-700/50 transition-all duration-200 cursor-pointer group"
    >
      <div>
        <p className="font-semibold text-gray-900 dark:text-white">{label}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">Target: {target}</p>
      </div>
      <div
        className={clsx(
          'px-4 py-2 rounded-xl text-sm font-semibold transition-all group-hover:scale-105',
          status === 'good'
            ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300 border border-green-200/50 dark:border-green-700/50'
            : status === 'warning'
            ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300 border border-yellow-200/50 dark:border-yellow-700/50'
            : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300 border border-red-200/50 dark:border-red-700/50'
        )}
      >
        {value}
      </div>
    </motion.div>
  );
}

function StatusCard({ name, status, delay }: { name: string; status: string; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
      whileHover={{ scale: 1.02, y: -2 }}
      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-gray-200/50 dark:border-gray-700/50 transition-all duration-200 cursor-pointer group"
    >
      <span className="font-semibold text-gray-900 dark:text-white">{name}</span>
      <span className="flex items-center gap-2">
        <motion.span
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="h-2.5 w-2.5 bg-green-500 rounded-full shadow-lg shadow-green-500/50"
        />
        <span className="text-sm font-medium text-green-600 dark:text-green-400 capitalize">
          {status}
        </span>
      </span>
    </motion.div>
  );
}

function LayoutDashboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  );
}
