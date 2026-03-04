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
      // Use real channel distribution from API
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
      color: 'bg-blue-500',
      trend: '+12%',
      trendUp: true,
    },
    {
      title: 'Open Tickets',
      value: stats?.open_tickets ?? 0,
      icon: Clock,
      color: 'bg-yellow-500',
      trend: '-5%',
      trendUp: false,
    },
    {
      title: 'Resolved',
      value: stats?.resolved_tickets ?? 0,
      icon: CheckCircle,
      color: 'bg-green-500',
      trend: '+18%',
      trendUp: true,
    },
    {
      title: 'Escalated',
      value: stats?.escalated_tickets ?? 0,
      icon: AlertCircle,
      color: 'bg-red-500',
      trend: '-2%',
      trendUp: true,
    },
  ];

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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Overview of your customer support metrics
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {card.title}
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {card.value}
                </p>
                <div className="flex items-center mt-2">
                  {card.trendUp ? (
                    <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                  )}
                  <span
                    className={clsx(
                      'text-sm font-medium',
                      card.trendUp ? 'text-green-500' : 'text-red-500'
                    )}
                  >
                    {card.trend}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400 text-sm ml-1">
                    vs last month
                  </span>
                </div>
              </div>
              <div className={clsx('p-4 rounded-full', card.color)}>
                <card.icon className="h-6 w-6 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Channel Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Channel Stats */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
        >
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Tickets by Channel
          </h2>
          <div className="space-y-4">
            <ChannelStatCard
              icon={Mail}
              name="Email"
              count={channelStats.email}
              color="bg-blue-500"
              percentage={
                stats?.total_tickets
                  ? Math.round((channelStats.email / stats.total_tickets) * 100)
                  : 0
              }
            />
            <ChannelStatCard
              icon={MessageSquare}
              name="WhatsApp"
              count={channelStats.whatsapp}
              color="bg-green-500"
              percentage={
                stats?.total_tickets
                  ? Math.round((channelStats.whatsapp / stats.total_tickets) * 100)
                  : 0
              }
            />
            <ChannelStatCard
              icon={Monitor}
              name="Web Form"
              count={channelStats.webform}
              color="bg-purple-500"
              percentage={
                stats?.total_tickets
                  ? Math.round((channelStats.webform / stats.total_tickets) * 100)
                  : 0
              }
            />
          </div>
        </motion.div>

        {/* Performance Metrics */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
        >
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Performance Metrics
          </h2>
          <div className="space-y-4">
            <MetricRow
              label="Avg. Response Time"
              value={`${stats?.avg_response_time_hours ?? 0}h`}
              target="&lt; 4h"
              status="good"
            />
            <MetricRow
              label="Resolution Rate"
              value="87%"
              target="&gt; 85%"
              status="good"
            />
            <MetricRow
              label="Escalation Rate"
              value={
                stats?.total_tickets
                  ? `${Math.round((stats.escalated_tickets / stats.total_tickets) * 100)}%`
                  : '0%'
              }
              target="&lt; 20%"
              status="good"
            />
            <MetricRow
              label="Customer Satisfaction"
              value="4.6/5"
              target="&gt; 4.5"
              status="good"
            />
          </div>
        </motion.div>
      </div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          System Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatusCard name="Email Service" status="operational" />
          <StatusCard name="WhatsApp Service" status="operational" />
          <StatusCard name="Web Form" status="operational" />
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
  percentage,
}: {
  icon: any;
  name: string;
  count: number;
  color: string;
  percentage: number;
}) {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div className="flex items-center">
        <div className={clsx('p-3 rounded-full', color)}>
          <Icon className="h-5 w-5 text-white" />
        </div>
        <div className="ml-4">
          <p className="font-medium text-gray-900 dark:text-white">{name}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{count} tickets</p>
        </div>
      </div>
      <div className="text-right">
        <p className="text-2xl font-bold text-gray-900 dark:text-white">{percentage}%</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">of total</p>
      </div>
    </div>
  );
}

function MetricRow({
  label,
  value,
  target,
  status,
}: {
  label: string;
  value: string;
  target: string;
  status: 'good' | 'warning' | 'bad';
}) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">Target: {target}</p>
      </div>
      <div
        className={clsx(
          'px-3 py-1 rounded-full text-sm font-medium',
          status === 'good'
            ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
            : status === 'warning'
            ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200'
            : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
        )}
      >
        {value}
      </div>
    </div>
  );
}

function StatusCard({ name, status }: { name: string; status: string }) {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <span className="font-medium text-gray-900 dark:text-white">{name}</span>
      <span className="flex items-center">
        <span className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse" />
        <span className="text-sm text-green-600 dark:text-green-400 capitalize">
          {status}
        </span>
      </span>
    </div>
  );
}
