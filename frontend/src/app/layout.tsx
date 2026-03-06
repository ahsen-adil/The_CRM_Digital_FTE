'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Ticket,
  Users,
  BarChart3,
  FileText,
  Settings,
  Menu,
  X,
  Moon,
  Sun,
  Mail,
  MessageSquare,
  Monitor,
  Sparkles,
} from 'lucide-react';
import { clsx } from 'clsx';
import './globals.css';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Tickets', href: '/tickets', icon: Ticket },
  { name: 'Customers', href: '/customers', icon: Users },
  { name: 'Reports', href: '/reports', icon: BarChart3 },
  { name: 'Web Form', href: '/webform', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const channels = [
  { name: 'Email', href: '/channels/email', icon: Mail, status: 'active' },
  { name: 'WhatsApp', href: '/channels/whatsapp', icon: MessageSquare, status: 'active' },
  { name: 'Web Form', href: '/webform', icon: Monitor, status: 'active' },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    // Set dark mode class on mount
    document.documentElement.classList.add('dark');
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (darkMode) {
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.add('dark');
    }
  };

  const isLandingPage = pathname === '/';

  if (isLandingPage) {
    return (
      <html lang="en" suppressHydrationWarning>
        <body className="antialiased">{children}</body>
      </html>
    );
  }

  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <div className={clsx('min-h-screen', darkMode ? 'dark' : '')}>
          <div className="flex h-screen overflow-hidden bg-gradient-to-br from-gray-50 via-gray-100 to-gray-50 dark:from-gray-900 dark:via-gray-950 dark:to-gray-900">
            {/* Mobile sidebar backdrop */}
            <AnimatePresence>
              {sidebarOpen && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 z-40 bg-gray-900/60 backdrop-blur-sm lg:hidden"
                  onClick={() => setSidebarOpen(false)}
                />
              )}
            </AnimatePresence>

            {/* Sidebar */}
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className={clsx(
                'fixed inset-y-0 left-0 z-50 w-72 transform transition-transform duration-300 lg:translate-x-0 lg:static lg:inset-0',
                sidebarOpen ? 'translate-x-0' : '-translate-x-full'
              )}
            >
              <div className="flex flex-col h-full">
                {/* Logo - Enhanced with gradient and glow */}
                <div className="relative flex items-center justify-between h-20 px-6 bg-gradient-to-r from-primary-600 via-primary-500 to-primary-600 overflow-hidden">
                  {/* Animated background effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
                  
                  <motion.div 
                    className="flex items-center gap-3 relative z-10"
                    whileHover={{ scale: 1.02 }}
                  >
                    <motion.div
                      animate={{ rotate: [0, 360] }}
                      transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                      className="flex items-center justify-center w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl shadow-lg"
                    >
                      <span className="text-2xl">☁️</span>
                    </motion.div>
                    <div>
                      <h1 className="text-xl font-bold text-white tracking-tight">CloudManage</h1>
                      <p className="text-xs text-primary-100">Customer Success FTE</p>
                    </div>
                  </motion.div>
                  
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="lg:hidden relative z-10 p-2 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {/* Navigation - Enhanced with glassmorphism */}
                <nav className="flex-1 px-3 py-6 space-y-2 overflow-y-auto">
                  <div className="mb-6">
                    <motion.div 
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center gap-2 px-4 py-2 mb-2"
                    >
                      <Sparkles className="h-4 w-4 text-primary-500" />
                      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Main Menu
                      </h3>
                    </motion.div>
                    
                    {navigation.map((item, index) => {
                      const isActive = pathname === item.href;
                      return (
                        <Link key={item.name} href={item.href}>
                          <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            whileHover={{ x: 6, scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className={clsx(
                              'relative flex items-center px-4 py-3 mt-2 rounded-xl transition-all duration-200 group',
                              isActive
                                ? 'bg-gradient-to-r from-primary-500/20 to-primary-500/10 dark:from-primary-500/30 dark:to-primary-500/10 text-primary-700 dark:text-primary-200 shadow-primary border border-primary-200/50 dark:border-primary-500/30'
                                : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100/80 dark:hover:bg-gray-800/50 hover:shadow-md border border-transparent'
                            )}
                          >
                            {isActive && (
                              <motion.div
                                layoutId="activeNav"
                                className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary-500 rounded-r-full"
                                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                              />
                            )}
                            <item.icon className={clsx("h-5 w-5 mr-3 transition-colors", isActive ? 'text-primary-600 dark:text-primary-300' : 'text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-200')} />
                            <span className="font-medium">{item.name}</span>
                            {isActive && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="ml-auto"
                              >
                                <Sparkles className="h-4 w-4 text-primary-500" />
                              </motion.div>
                            )}
                          </motion.div>
                        </Link>
                      );
                    })}
                  </div>

                  <div>
                    <motion.div 
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 }}
                      className="flex items-center gap-2 px-4 py-2 mb-2"
                    >
                      <Sparkles className="h-4 w-4 text-secondary-500" />
                      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Channels
                      </h3>
                    </motion.div>
                    
                    {channels.map((item, index) => (
                      <Link key={item.name} href={item.href}>
                        <motion.div
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.3 + index * 0.05 }}
                          whileHover={{ x: 6, scale: 1.02 }}
                          className="flex items-center justify-between px-4 py-3 mt-2 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-100/80 dark:hover:bg-gray-800/50 transition-all duration-200 border border-transparent hover:border-gray-200/50 dark:hover:border-gray-700/50 group"
                        >
                          <div className="flex items-center">
                            <div className={clsx("p-2 rounded-lg mr-3 transition-colors", 
                              item.name === 'Email' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' :
                              item.name === 'WhatsApp' ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' :
                              'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
                            )}>
                              <item.icon className="h-4 w-4" />
                            </div>
                            <span className="font-medium">{item.name}</span>
                          </div>
                          <span
                            className={clsx(
                              'px-2 py-1 text-xs rounded-full font-medium',
                              item.status === 'active'
                                ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300'
                                : 'bg-gray-100 text-gray-700'
                            )}
                          >
                            {item.status}
                          </span>
                        </motion.div>
                      </Link>
                    ))}
                  </div>
                </nav>

                {/* Dark mode toggle - Enhanced */}
                <div className="p-4 border-t border-gray-200/50 dark:border-gray-700/50">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={toggleDarkMode}
                    className={clsx(
                      "flex items-center justify-center w-full px-4 py-3 rounded-xl transition-all duration-300 font-medium",
                      darkMode 
                        ? "bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-700 dark:text-amber-300 border border-amber-200/50 dark:border-amber-500/30 hover:from-amber-500/30 hover:to-orange-500/30" 
                        : "bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-indigo-700 dark:text-indigo-300 border border-indigo-200/50 dark:border-indigo-500/30 hover:from-indigo-500/30 hover:to-purple-500/30"
                    )}
                  >
                    <motion.div
                      animate={{ rotate: darkMode ? 180 : 0 }}
                      transition={{ duration: 0.5 }}
                    >
                      {darkMode ? (
                        <>
                          <Sun className="h-5 w-5 mr-2" />
                          Light Mode
                        </>
                      ) : (
                        <>
                          <Moon className="h-5 w-5 mr-2" />
                          Dark Mode
                        </>
                      )}
                    </motion.div>
                  </motion.button>
                </div>
              </div>
            </motion.aside>

            {/* Main content */}
            <div className="flex-1 flex flex-col min-w-0">
              {/* Top bar - Enhanced with glassmorphism */}
              <motion.header 
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50 shadow-sm"
              >
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setSidebarOpen(true)}
                  className="lg:hidden p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all"
                >
                  <Menu className="h-6 w-6" />
                </motion.button>

                <div className="flex-1" />

                <div className="flex items-center space-x-4">
                  <motion.div 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-sm text-gray-600 dark:text-gray-400 bg-gray-100/50 dark:bg-gray-800/50 px-4 py-2 rounded-xl border border-gray-200/50 dark:border-gray-700/50"
                  >
                    {new Date().toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </motion.div>
                </div>
              </motion.header>

              {/* Page content */}
              <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                  className="max-w-7xl mx-auto"
                >
                  {children}
                </motion.div>
              </main>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
