'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
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
} from 'lucide-react';
import { clsx } from 'clsx';
import './globals.css';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
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

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (darkMode) {
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.add('dark');
    }
  };

  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <div className={clsx('min-h-screen', darkMode ? 'dark' : '')}>
          <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
              <div
                className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
                onClick={() => setSidebarOpen(false)}
              />
            )}

            {/* Sidebar */}
            <aside
              className={clsx(
                'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 lg:translate-x-0',
                sidebarOpen ? 'translate-x-0' : '-translate-x-full'
              )}
            >
              <div className="flex flex-col h-full">
                {/* Logo */}
                <div className="flex items-center justify-between h-16 px-6 bg-gradient-to-r from-primary-600 to-primary-700">
                  <h1 className="text-xl font-bold text-white">☁️ CloudManage</h1>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="lg:hidden text-white hover:text-gray-200"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
                  <div className="mb-6">
                    <h3 className="px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Main Menu
                    </h3>
                    {navigation.map((item) => {
                      const isActive = pathname === item.href;
                      return (
                        <Link key={item.name} href={item.href}>
                          <motion.div
                            whileHover={{ x: 4 }}
                            className={clsx(
                              'flex items-center px-4 py-3 mt-2 rounded-lg transition-colors',
                              isActive
                                ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-200'
                                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                            )}
                          >
                            <item.icon className="h-5 w-5 mr-3" />
                            <span className="font-medium">{item.name}</span>
                          </motion.div>
                        </Link>
                      );
                    })}
                  </div>

                  <div>
                    <h3 className="px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Channels
                    </h3>
                    {channels.map((item) => (
                      <Link key={item.name} href={item.href}>
                        <motion.div
                          whileHover={{ x: 4 }}
                          className="flex items-center justify-between px-4 py-3 mt-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        >
                          <div className="flex items-center">
                            <item.icon className="h-5 w-5 mr-3" />
                            <span className="font-medium">{item.name}</span>
                          </div>
                          <span
                            className={clsx(
                              'px-2 py-1 text-xs rounded-full',
                              item.status === 'active'
                                ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
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

                {/* Dark mode toggle */}
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                  <button
                    onClick={toggleDarkMode}
                    className="flex items-center justify-center w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
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
                  </button>
                </div>
              </div>
            </aside>

            {/* Main content */}
            <div className="flex-1 flex flex-col lg:pl-64">
              {/* Top bar */}
                <header className="flex items-center justify-between h-16 px-6 bg-white dark:bg-gray-800 shadow">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="lg:hidden text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  <Menu className="h-6 w-6" />
                </button>

                <div className="flex-1" />

                <div className="flex items-center space-x-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {new Date().toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </div>
                </div>
              </header>

              {/* Page content */}
              <main className="flex-1 overflow-y-auto p-6">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
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
