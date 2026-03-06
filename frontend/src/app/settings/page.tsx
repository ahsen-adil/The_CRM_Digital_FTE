'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Settings, 
  Mail, 
  MessageSquare, 
  Monitor, 
  Database, 
  Key, 
  Activity, 
  CheckCircle, 
  XCircle,
  Sparkles,
  Shield,
  Clock,
  Zap,
  Server,
  Cpu,
} from 'lucide-react';
import { healthApi } from '@/lib/api';
import { clsx } from 'clsx';

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
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
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/30',
    },
    {
      name: 'WhatsApp Service',
      description: 'Whapi.Cloud webhook integration',
      icon: MessageSquare,
      status: 'active',
      details: 'Webhook endpoint active',
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/30',
    },
    {
      name: 'Web Form',
      description: 'Online support form',
      icon: Monitor,
      status: 'active',
      details: 'Form submissions enabled',
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-500/30',
    },
    {
      name: 'Database',
      description: 'Neon PostgreSQL',
      icon: Database,
      status: health?.database === 'connected' ? 'active' : 'inactive',
      details: health?.database === 'connected' ? 'Connected' : 'Disconnected',
      color: 'from-cyan-500 to-cyan-600',
      bgColor: 'bg-cyan-500/10',
      borderColor: 'border-cyan-500/30',
    },
    {
      name: 'AI Agent',
      description: 'OpenAI Agents SDK',
      icon: Key,
      status: 'active',
      details: 'GPT-4o model',
      color: 'from-pink-500 to-pink-600',
      bgColor: 'bg-pink-500/10',
      borderColor: 'border-pink-500/30',
    },
    {
      name: 'API Server',
      description: 'FastAPI backend',
      icon: Activity,
      status: health?.status === 'healthy' ? 'active' : 'inactive',
      details: health?.status === 'healthy' ? 'Running' : 'Issues detected',
      color: 'from-orange-500 to-orange-600',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-500/30',
    },
  ];

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
              <Settings className="h-6 w-6 text-white" />
            </motion.div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            System configuration and status
          </p>
        </div>
        
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="hidden sm:flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/30 rounded-full"
        >
          <Sparkles className="h-4 w-4 text-primary-500" />
          <span className="text-sm text-primary-600 dark:text-primary-400 font-medium">System Control</span>
        </motion.div>
      </motion.div>

      {/* System Status - Enhanced */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6 overflow-hidden"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-br from-green-500 to-green-600 rounded-xl">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            System Status
          </h2>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-10 h-10 border-4 border-primary-500/30 border-t-primary-500 rounded-full"
            />
          </div>
        ) : (
          <>
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className={clsx(
                'p-6 rounded-2xl mb-6 border-2',
                health?.status === 'healthy' 
                  ? 'bg-gradient-to-r from-green-500/10 to-emerald-500/10 border-green-500/30' 
                  : 'bg-gradient-to-r from-red-500/10 to-orange-500/10 border-red-500/30'
              )}
            >
              <div className="flex items-center gap-4">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200 }}
                  className={clsx(
                    'p-3 rounded-xl',
                    health?.status === 'healthy' 
                      ? 'bg-gradient-to-br from-green-500 to-green-600' 
                      : 'bg-gradient-to-br from-red-500 to-red-600'
                  )}
                >
                  {health?.status === 'healthy' ? (
                    <CheckCircle className="h-8 w-8 text-white" />
                  ) : (
                    <XCircle className="h-8 w-8 text-white" />
                  )}
                </motion.div>
                <div className="flex-1">
                  <p className={clsx(
                    'text-lg font-bold',
                    health?.status === 'healthy' 
                      ? 'text-green-700 dark:text-green-300' 
                      : 'text-red-700 dark:text-red-300'
                  )}>
                    System {health?.status === 'healthy' ? 'Healthy' : 'Issues Detected'}
                  </p>
                  <p className={clsx(
                    'text-sm',
                    health?.status === 'healthy' 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  )}>
                    Last check: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'Unknown'}
                  </p>
                </div>
                {health?.status === 'healthy' && (
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="hidden sm:block"
                  >
                    <Shield className="h-12 w-12 text-green-500/30" />
                  </motion.div>
                )}
              </div>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {services.map((service, index) => (
                <ServiceCard key={service.name} service={service} index={index} />
              ))}
            </div>
          </>
        )}
      </motion.div>

      {/* Configuration - Enhanced */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl">
            <Settings className="h-5 w-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Configuration
          </h2>
        </div>

        <div className="space-y-3">
          <ConfigItem
            label="Polling Interval"
            value="60 seconds"
            description="How often to check for new emails"
            icon={Clock}
            delay={0.3}
          />
          <ConfigItem
            label="Sentiment Threshold"
            value="0.3"
            description="Score below this triggers escalation"
            icon={Activity}
            delay={0.35}
          />
          <ConfigItem
            label="AI Model"
            value="GPT-4o"
            description="OpenAI model for response generation"
            icon={Cpu}
            delay={0.4}
          />
          <ConfigItem
            label="Database"
            value="Neon PostgreSQL"
            description="Cloud database service"
            icon={Database}
            delay={0.45}
          />
        </div>
      </motion.div>

      {/* Environment Info - Enhanced */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl">
            <Server className="h-5 w-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Environment
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <EnvItem label="Frontend Port" value="3000" icon={Monitor} delay={0.4} />
          <EnvItem label="API Port" value="8002" icon={Activity} delay={0.45} />
          <EnvItem label="Webform API Port" value="8001" icon={Mail} delay={0.5} />
          <EnvItem label="WhatsApp Port" value="8000" icon={MessageSquare} delay={0.55} />
        </div>
      </motion.div>
    </div>
  );
}

function ServiceCard({ service, index }: { service: any; index: number }) {
  const Icon = service.icon;
  const isActive = service.status === 'active';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 + index * 0.05 }}
      whileHover={{ y: -4, scale: 1.02 }}
      className={`p-5 rounded-2xl border transition-all duration-300 ${service.bgColor} ${service.borderColor} group cursor-pointer`}
    >
      <div className="flex items-start justify-between mb-3">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3 + index * 0.05, type: 'spring', stiffness: 200 }}
          className={`p-3 rounded-xl bg-gradient-to-br ${service.color} shadow-lg group-hover:shadow-xl transition-shadow`}
        >
          <Icon className="h-5 w-5 text-white" />
        </motion.div>
        <span
          className={clsx(
            'px-3 py-1 text-xs rounded-full font-semibold',
            isActive 
              ? 'bg-green-500/20 text-green-600 dark:text-green-400 border border-green-500/30' 
              : 'bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30'
          )}
        >
          {service.status}
        </span>
      </div>
      <h3 className="font-bold text-gray-900 dark:text-white mb-1">{service.name}</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{service.description}</p>
      <p className="text-xs text-gray-400 dark:text-gray-500">{service.details}</p>
    </motion.div>
  );
}

function ConfigItem({ label, value, description, icon: Icon, delay }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      whileHover={{ x: 4, scale: 1.01 }}
      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-gray-200/50 dark:border-gray-700/50 transition-all duration-200 cursor-pointer group"
    >
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary-500/10 rounded-lg group-hover:bg-primary-500/20 transition-colors">
          <Icon className="h-5 w-5 text-primary-500" />
        </div>
        <div>
          <p className="font-semibold text-gray-900 dark:text-white">{label}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
        </div>
      </div>
      <motion.p 
        className="text-lg font-bold text-primary-600 dark:text-primary-400"
        whileHover={{ scale: 1.1 }}
      >
        {value}
      </motion.p>
    </motion.div>
  );
}

function EnvItem({ label, value, icon: Icon, delay }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
      whileHover={{ scale: 1.05, y: -2 }}
      className="p-5 border border-gray-200 dark:border-gray-700 rounded-xl transition-all duration-200 group hover:border-primary-500/30 hover:shadow-lg"
    >
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg group-hover:bg-primary-500/10 transition-colors">
          <Icon className="h-5 w-5 text-gray-500 group-hover:text-primary-500" />
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
    </motion.div>
  );
}
