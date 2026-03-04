'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, Mail, MessageSquare, Monitor, Database, Key, Activity, CheckCircle, XCircle } from 'lucide-react';
import { healthApi } from '@/lib/api';

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const data = await healthApi.check();
      setHealth(data);
    } catch (error) {
      console.error('Health check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const services = [
    {
      name: 'Email Service',
      description: 'Gmail IMAP/SMTP integration',
      icon: Mail,
      status: 'active',
      details: 'Polling every 60 seconds',
    },
    {
      name: 'WhatsApp Service',
      description: 'Whapi.Cloud webhook integration',
      icon: MessageSquare,
      status: 'active',
      details: 'Webhook endpoint active',
    },
    {
      name: 'Web Form',
      description: 'Online support form',
      icon: Monitor,
      status: 'active',
      details: 'Form submissions enabled',
    },
    {
      name: 'Database',
      description: 'Neon PostgreSQL',
      icon: Database,
      status: health?.database === 'connected' ? 'active' : 'inactive',
      details: health?.database === 'connected' ? 'Connected' : 'Disconnected',
    },
    {
      name: 'AI Agent',
      description: 'OpenAI Agents SDK',
      icon: Key,
      status: 'active',
      details: 'GPT-4o model',
    },
    {
      name: 'API Server',
      description: 'FastAPI backend',
      icon: Activity,
      status: health?.status === 'healthy' ? 'active' : 'inactive',
      details: health?.status === 'healthy' ? 'Running' : 'Issues detected',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          System configuration and status
        </p>
      </div>

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          System Status
        </h2>
        
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : (
          <div className={clsx('p-4 rounded-lg mb-6', health?.status === 'healthy' ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900')}>
            <div className="flex items-center gap-3">
              {health?.status === 'healthy' ? (
                <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
              ) : (
                <XCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
              )}
              <div>
                <p className={clsx('font-semibold', health?.status === 'healthy' ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200')}>
                  System {health?.status === 'healthy' ? 'Healthy' : 'Issues Detected'}
                </p>
                <p className={clsx('text-sm', health?.status === 'healthy' ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300')}>
                  Last check: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'Unknown'}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((service) => (
            <ServiceCard key={service.name} service={service} />
          ))}
        </div>
      </motion.div>

      {/* Configuration */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Configuration
        </h2>
        
        <div className="space-y-4">
          <ConfigItem
            label="Polling Interval"
            value="60 seconds"
            description="How often to check for new emails"
          />
          <ConfigItem
            label="Sentiment Threshold"
            value="0.3"
            description="Score below this triggers escalation"
          />
          <ConfigItem
            label="AI Model"
            value="GPT-4o"
            description="OpenAI model for response generation"
          />
          <ConfigItem
            label="Database"
            value="Neon PostgreSQL"
            description="Cloud database service"
          />
        </div>
      </motion.div>

      {/* Environment Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Environment
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoItem label="Frontend Port" value="3000" />
          <InfoItem label="API Port" value="8002" />
          <InfoItem label="Webform API Port" value="8001" />
          <InfoItem label="WhatsApp Port" value="8000" />
        </div>
      </motion.div>
    </div>
  );
}

function ServiceCard({ service }: { service: any }) {
  const Icon = service.icon;
  const isActive = service.status === 'active';

  return (
    <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className={clsx('p-2 rounded-lg', isActive ? 'bg-primary-100 dark:bg-primary-900' : 'bg-gray-100 dark:bg-gray-700')}>
            <Icon className={clsx('h-5 w-5', isActive ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500')} />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-white">{service.name}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">{service.description}</p>
          </div>
        </div>
        <span className={clsx('px-2 py-1 text-xs rounded-full', isActive ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200')}>
          {service.status}
        </span>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400">{service.details}</p>
    </div>
  );
}

function ConfigItem({ label, value, description }: { label: string; value: string; description: string }) {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
      <p className="text-lg font-semibold text-primary-600 dark:text-primary-400">{value}</p>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
      <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-lg font-semibold text-gray-900 dark:text-white mt-1">{value}</p>
    </div>
  );
}

function clsx(...classes: any[]) {
  return classes.filter(Boolean).join(' ');
}
