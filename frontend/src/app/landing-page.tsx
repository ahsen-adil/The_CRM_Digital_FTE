'use client';

import { motion, useScroll, useTransform, useInView, useMotionValue, useSpring } from 'framer-motion';
import {
  ArrowRight,
  Mail,
  MessageSquare,
  Monitor,
  BarChart3,
  Users,
  Ticket,
  Zap,
  Shield,
  Clock,
  Sparkles,
  Rocket,
  Star,
  Target,
  Globe,
  Play,
  Award,
  Cloud,
  Smile,
} from 'lucide-react';
import Link from 'next/link';
import { useRef, useState, useEffect } from 'react';

export default function LandingPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: containerRef });
  
  const heroY = useTransform(scrollYProgress, [0, 0.4], [0, 150]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.4], [1, 0]);
  
  return (
    <div ref={containerRef} className="min-h-screen overflow-hidden bg-gray-950">
      <CustomCursor />
      <AnimatedBackground />
      
      <div className="relative z-10">
        <Navigation />
        <motion.section style={{ y: heroY, opacity: heroOpacity }} className="relative min-h-screen flex items-center justify-center">
          <HeroSection />
        </motion.section>
        <StatsSection />
        <FeaturesSection />
        <ChannelsSection />
        <BenefitsSection />
        <TestimonialsSection />
        <CTASection />
        <Footer />
      </div>
    </div>
  );
}

// Premium Custom Cursor
function CustomCursor() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  
  const cursorX = useSpring(0, { stiffness: 600, damping: 30 });
  const cursorY = useSpring(0, { stiffness: 600, damping: 30 });
  const trailX = useSpring(0, { stiffness: 300, damping: 20 });
  const trailY = useSpring(0, { stiffness: 300, damping: 20 });

  useEffect(() => {
    const mouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
      cursorX.set(e.clientX - 10);
      cursorY.set(e.clientY - 10);
      trailX.set(e.clientX - 20);
      trailY.set(e.clientY - 20);
    };
    window.addEventListener('mousemove', mouseMove);
    return () => window.removeEventListener('mousemove', mouseMove);
  }, [cursorX, cursorY, trailX, trailY]);

  useEffect(() => {
    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const isInteractive = target.tagName === 'A' || target.tagName === 'BUTTON' || !!target.closest('a') || !!target.closest('button');
      setIsHovering(isInteractive);
    };
    document.addEventListener('mouseover', handleMouseOver);
    return () => document.removeEventListener('mouseover', handleMouseOver);
  }, []);

  return (
    <>
      <motion.div
        className="fixed top-0 left-0 w-5 h-5 bg-gradient-to-br from-primary-400 via-purple-400 to-pink-400 rounded-full pointer-events-none z-[9999] shadow-lg shadow-primary-500/50"
        style={{ x: cursorX, y: cursorY, scale: isHovering ? 1.8 : 1 }}
      />
      <motion.div
        className="fixed top-0 left-0 w-12 h-12 border-2 border-primary-400/40 rounded-full pointer-events-none z-[9998]"
        style={{ x: trailX, y: trailY, scale: isHovering ? 1.3 : 1 }}
      />
      <motion.div
        className="fixed top-0 left-0 w-2 h-2 bg-white/60 rounded-full pointer-events-none z-[9997]"
        style={{ x: mousePosition.x - 4, y: mousePosition.y - 4, scale: isHovering ? 0 : 1 }}
      />
    </>
  );
}

// Premium Animated Background - Partial with dramatic effects
function AnimatedBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Deep base gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-gray-950 via-slate-950 to-gray-950" />
      
      {/* TOP gradient mesh - animated */}
      <div className="absolute top-0 left-0 right-0 h-[60vh] overflow-hidden">
        <motion.div
          animate={{
            scale: [1, 1.3, 1],
            x: [0, 80, 0],
            y: [0, 40, 0],
            rotate: [0, 10, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -top-[30%] -right-[20%] w-[800px] h-[800px] bg-gradient-to-br from-primary-600/30 via-purple-600/20 to-pink-600/30 rounded-full filter blur-[120px] opacity-60"
        />
        <motion.div
          animate={{
            scale: [1.3, 1, 1.3],
            x: [0, -60, 0],
            y: [0, 80, 0],
            rotate: [0, -15, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -top-[20%] -left-[10%] w-[600px] h-[600px] bg-gradient-to-br from-blue-600/30 via-cyan-600/20 to-teal-600/30 rounded-full filter blur-[100px] opacity-50"
        />
        <motion.div
          animate={{
            scale: [1, 1.4, 1],
            x: [0, 50, 0],
            y: [0, -60, 0],
          }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-[20%] left-[30%] w-[500px] h-[500px] bg-gradient-to-br from-pink-600/25 via-rose-600/20 to-orange-600/25 rounded-full filter blur-[90px] opacity-40"
        />
      </div>

      {/* BOTTOM accent glow */}
      <div className="absolute bottom-0 left-0 right-0 h-[40vh] overflow-hidden">
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
          transition={{ duration: 15, repeat: Infinity }}
          className="absolute -bottom-[30%] left-[20%] w-[400px] h-[400px] bg-gradient-to-tr from-primary-600/20 to-purple-600/20 rounded-full filter blur-[80px]"
        />
        <motion.div
          animate={{ scale: [1.2, 1, 1.2], opacity: [0.4, 0.6, 0.4] }}
          transition={{ duration: 20, repeat: Infinity }}
          className="absolute -bottom-[20%] right-[10%] w-[500px] h-[500px] bg-gradient-to-tl from-blue-600/15 to-cyan-600/15 rounded-full filter blur-[100px]"
        />
      </div>

      {/* Floating 3D geometric shapes - TOP HALF ONLY */}
      <div className="absolute top-0 left-0 right-0 h-[70vh] overflow-hidden">
        <FloatingShape type="hexagon" className="absolute top-[15%] right-[15%]" size={80} delay={0} duration={8} />
        <FloatingShape type="circle" className="absolute top-[30%] left-[10%]" size={60} delay={1} duration={10} />
        <FloatingShape type="square" className="absolute top-[50%] right-[25%]" size={50} delay={2} duration={9} />
        <FloatingShape type="hexagon" className="absolute top-[25%] left-[35%]" size={45} delay={3} duration={11} />
        <FloatingShape type="circle" className="absolute top-[60%] right-[10%]" size={55} delay={4} duration={12} />
        <FloatingShape type="square" className="absolute top-[45%] left-[20%]" size={40} delay={5} duration={10} />
      </div>

      {/* Rising particles */}
      <div className="absolute inset-0">
        {[...Array(25)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1.5 h-1.5 bg-gradient-to-br from-primary-400 to-purple-400 rounded-full shadow-lg shadow-primary-500/60"
            style={{ left: `${(i * 4) % 100}%`, top: `${80 + (i * 3) % 20}%` }}
            animate={{ y: [0, -200, -400], opacity: [0, 0.8, 0], scale: [0.5, 1.2, 0.5] }}
            transition={{ duration: 12 + i * 0.4, repeat: Infinity, ease: 'easeInOut', delay: i * 0.4 }}
          />
        ))}
      </div>

      {/* Grid pattern overlay - subtle */}
      <div className="absolute inset-0 opacity-[0.02]" style={{
        backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
        backgroundSize: '80px 80px',
      }} />

      {/* Radial vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(0,0,0,0.6)_100%)]" />
    </div>
  );
}

// Floating 3D Shape Component
function FloatingShape({ type, className, size, delay, duration }: any) {
  return (
    <motion.div
      className={className}
      style={{ width: size, height: size }}
      animate={{
        y: [0, -40, 0],
        rotate: [0, 180, 360],
        rotateX: [0, 180, 360],
        rotateY: [0, 180, 360],
        scale: [1, 1.3, 1],
      }}
      transition={{ duration, delay, repeat: Infinity, ease: 'easeInOut' }}
    >
      {type === 'hexagon' && (
        <div className="w-full h-full bg-gradient-to-br from-primary-500/30 to-purple-500/30 border border-primary-500/50 backdrop-blur-sm shadow-xl shadow-primary-500/20"
          style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }} />
      )}
      {type === 'circle' && (
        <div className="w-full h-full bg-gradient-to-br from-blue-500/30 to-cyan-500/30 border border-blue-500/50 backdrop-blur-sm rounded-full shadow-xl shadow-blue-500/20" />
      )}
      {type === 'square' && (
        <div className="w-full h-full bg-gradient-to-br from-pink-500/30 to-rose-500/30 border border-pink-500/50 backdrop-blur-sm rounded-xl shadow-xl shadow-pink-500/20 transform rotate-12" />
      )}
    </motion.div>
  );
}

// Navigation
function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.nav initial={{ y: -100, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
      className={cn('fixed top-0 left-0 right-0 z-50 transition-all duration-500',
        scrolled ? 'bg-gray-950/90 backdrop-blur-xl border-b border-gray-800/50 shadow-2xl shadow-primary-500/10' : 'bg-transparent')}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          <motion.div className="flex items-center gap-3" whileHover={{ scale: 1.08 }}>
            <motion.div animate={{ rotate: 360 }} transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary-500 via-purple-500 to-pink-500 rounded-2xl shadow-2xl shadow-primary-500/50">
              <Cloud className="h-6 w-6 text-white" />
            </motion.div>
            <div>
              <span className="text-xl font-bold text-white">CloudManage</span>
              <p className="text-xs text-gray-400">Customer Success FTE</p>
            </div>
          </motion.div>
          <div className="hidden md:flex items-center gap-8">
            {['Features', 'Channels', 'Benefits', 'Testimonials'].map((item) => (
              <a key={item} href={`#${item.toLowerCase()}`} className="text-gray-400 hover:text-white transition-colors text-sm font-medium relative group">
                {item}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-primary-500 to-purple-500 group-hover:w-full transition-all duration-300" />
              </a>
            ))}
          </div>
          <Link href="/dashboard"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-500 hover:to-purple-500 text-white font-semibold rounded-2xl transition-all shadow-xl shadow-primary-500/40 hover:shadow-primary-500/60 hover:scale-105">
            Go to Dashboard
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </motion.nav>
  );
}

// Hero Section with dramatic 3D
function HeroSection() {
  const ref = useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const rotateX = useSpring(useTransform(mouseY, [-0.5, 0.5], [15, -15]), { damping: 25, stiffness: 150 });
  const rotateY = useSpring(useTransform(mouseX, [-0.5, 0.5], [-15, 15]), { damping: 25, stiffness: 150 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!ref.current) return;
      const rect = ref.current.getBoundingClientRect();
      mouseX.set((e.clientX - rect.left) / rect.width - 0.5);
      mouseY.set((e.clientY - rect.top) / rect.height - 0.5);
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [mouseX, mouseY]);

  return (
    <div ref={ref} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
      <div className="text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-500/15 border border-primary-500/40 rounded-full mb-10 backdrop-blur-xl shadow-lg shadow-primary-500/20">
          <Sparkles className="h-4 w-4 text-primary-300" />
          <span className="text-sm text-primary-200 font-medium">AI-Powered Customer Success Platform</span>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.1 }}>
          <h1 className="text-5xl sm:text-6xl lg:text-8xl font-black text-white mb-6 tracking-tight">
            Customer Success
            <br />
            <span className="bg-gradient-to-r from-primary-400 via-purple-400 to-pink-400 bg-clip-text text-transparent drop-shadow-2xl">
              Digital FTE
            </span>
          </h1>
        </motion.div>

        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }}
          className="text-xl lg:text-2xl text-gray-300 max-w-4xl mx-auto mb-10 leading-relaxed">
          AI-powered customer support across Email, WhatsApp, and Web Forms.
          <br />
          <span className="text-gray-400">Resolve tickets faster, keep customers happier.</span>
        </motion.p>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-5 justify-center mb-12">
          <Link href="/dashboard"
            className="group inline-flex items-center justify-center gap-2 px-10 py-5 bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 hover:from-primary-500 hover:via-purple-500 hover:to-pink-500 text-white font-bold rounded-2xl transition-all shadow-2xl shadow-primary-500/50 hover:shadow-primary-500/70 hover:scale-105 text-lg relative overflow-hidden">
            <span className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/25 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
            <Rocket className="h-6 w-6" />
            Go to Dashboard
            <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <a href="#features"
            className="inline-flex items-center justify-center gap-2 px-10 py-5 bg-gray-800/60 hover:bg-gray-800 text-white font-bold rounded-2xl transition-all border border-gray-600 text-lg backdrop-blur-xl hover:scale-105 shadow-xl">
            <Play className="h-5 w-5" />
            Learn More
          </a>
        </motion.div>

        {/* Dramatic 3D floating elements */}
        {/* <div className="relative h-40 max-w-6xl mx-auto perspective-1000"> */}
          {/* Central 3D card with mouse tracking */}
          {/* <motion.div
            initial={{ opacity: 0, rotateX: 30, y: 80 }}
            animate={{ opacity: 1, rotateX: 0, y: 0 }}
            transition={{ duration: 1.2, delay: 0.5, type: 'spring' }}
            style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
            className="absolute top-0 left-1/2 -translate-x-1/2 w-[400px] p-6 bg-gradient-to-br from-gray-800/95 via-gray-900/95 to-gray-800/95 backdrop-blur-2xl rounded-3xl border border-gray-600/50 shadow-2xl shadow-primary-500/30">
             */}
            {/* Depth layers */}
            {/* <div className="absolute inset-0 bg-gradient-to-br from-primary-500/15 to-purple-500/15 rounded-3xl" style={{ transform: 'translateZ(-30px)' }} />
            <div className="absolute inset-0 bg-gradient-to-br from-primary-500/8 to-transparent rounded-3xl" style={{ transform: 'translateZ(-50px)' }} />
             */}
            {/* Content with depth */}
            {/* <div style={{ transform: 'translateZ(40px)' }}>
              <div className="flex gap-2.5 mb-5">
                <div className="w-3.5 h-3.5 rounded-full bg-red-500 shadow-lg shadow-red-500/60" />
                <div className="w-3.5 h-3.5 rounded-full bg-yellow-500 shadow-lg shadow-yellow-500/60" />
                <div className="w-3.5 h-3.5 rounded-full bg-green-500 shadow-lg shadow-green-500/60" />
              </div>
              <div className="space-y-2.5">
                <div className="h-2.5 bg-gradient-to-r from-gray-600 to-gray-500 rounded-full w-4/5 shadow-lg" />
                <div className="h-2.5 bg-gradient-to-r from-gray-600 to-gray-500 rounded-full w-2/3 shadow-lg" />
                <div className="h-2.5 bg-gradient-to-r from-primary-500/60 to-purple-500/60 rounded-full w-3/4 shadow-lg shadow-primary-500/30" />
                <div className="h-2.5 bg-gradient-to-r from-gray-600 to-gray-500 rounded-full w-3/5 shadow-lg" />
              </div>
              <div className="mt-5 flex gap-3">
                <div className="flex-1 h-12 bg-gradient-to-r from-primary-500/30 to-purple-500/30 rounded-xl border border-primary-500/30 shadow-lg" />
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-purple-500 rounded-xl shadow-2xl shadow-primary-500/50" />
              </div>
            </div>
          </motion.div>
        </div> */}
      </div>
    </div>
  );
}

// Stats Section with 3D cards
function StatsSection() {
  const stats = [
    { value: '24/7', label: 'Automated Support', icon: Clock },
    { value: '< 4h', label: 'Avg Response Time', icon: Zap },
    { value: '87%', label: 'Resolution Rate', icon: Target },
    { value: '4.6/5', label: 'Customer Satisfaction', icon: Smile },
  ];

  return (
    <section className="py-24 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <StatCard key={stat.label} stat={stat} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}

function StatCard({ stat, index }: { stat: any; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 60, rotateX: -15 }} whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
      viewport={{ once: true }} transition={{ duration: 0.7, delay: index * 0.1, type: 'spring' }}
      whileHover={{ y: -12, scale: 1.08, rotateX: 8, rotateY: -5 }}
      className="group p-6 rounded-3xl bg-gradient-to-br from-gray-800/70 to-gray-800/50 backdrop-blur-xl border border-gray-600/50 hover:border-primary-500/50 transition-all cursor-pointer shadow-2xl"
      style={{ transformStyle: 'preserve-3d' }}>
      
      <div className="absolute inset-0 bg-gradient-to-br from-primary-500/8 to-purple-500/8 rounded-3xl" style={{ transform: 'translateZ(-30px)' }} />
      
      <motion.div initial={{ scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true }}
        transition={{ type: 'spring', stiffness: 200, delay: index * 0.1 + 0.2 }}
        className="inline-flex p-4 bg-gradient-to-br from-primary-500/30 to-purple-500/30 rounded-2xl mb-4 shadow-xl border border-primary-500/30"
        style={{ transform: 'translateZ(25px)' }}>
        <stat.icon className="h-7 w-7 text-primary-300" />
      </motion.div>
      <div className="text-4xl font-black bg-gradient-to-r from-primary-300 via-purple-300 to-pink-300 bg-clip-text text-transparent mb-3 drop-shadow-lg"
        style={{ transform: 'translateZ(35px)' }}>{stat.value}</div>
      <div className="text-gray-400 text-sm font-medium" style={{ transform: 'translateZ(20px)' }}>{stat.label}</div>
    </motion.div>
  );
}

// Features Section with dramatic 3D cards
function FeaturesSection() {
  const features = [
    { icon: Mail, title: 'Email Integration', description: 'Automatically process emails with AI-powered responses.', color: 'from-blue-500 to-cyan-500' },
    { icon: MessageSquare, title: 'WhatsApp Support', description: 'Connect with customers on WhatsApp automatically.', color: 'from-green-500 to-emerald-500' },
    { icon: Monitor, title: 'Web Forms', description: 'Customizable forms that integrate into your system.', color: 'from-purple-500 to-pink-500' },
    { icon: Ticket, title: 'Smart Ticketing', description: 'Intelligent ticket routing and prioritization.', color: 'from-orange-500 to-red-500' },
    { icon: Users, title: 'Customer Management', description: 'Complete profiles with interaction history.', color: 'from-pink-500 to-rose-500' },
    { icon: BarChart3, title: 'Analytics & Reports', description: 'Real-time dashboards and detailed reports.', color: 'from-cyan-500 to-blue-500' },
  ];

  return (
    <section id="features" className="py-32 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-20">
          <h2 className="text-5xl lg:text-6xl font-black text-white mb-5 drop-shadow-2xl">Everything You Need</h2>
          <p className="text-xl text-gray-300">Powerful features to streamline your support</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} feature={feature} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}

function FeatureCard({ feature, index }: { feature: any; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 70, rotateY: -20, rotateX: 10 }}
      whileInView={{ opacity: 1, y: 0, rotateY: 0, rotateX: 0 }}
      viewport={{ once: true }} transition={{ duration: 0.7, delay: index * 0.1, type: 'spring' }}
      whileHover={{ y: -15, scale: 1.06, rotateY: 10, rotateX: -8 }}
      className="group p-7 rounded-3xl bg-gradient-to-br from-gray-800/70 to-gray-800/50 backdrop-blur-xl border border-gray-600/50 hover:border-gray-500/50 transition-all cursor-pointer shadow-2xl"
      style={{ transformStyle: 'preserve-3d' }}>
      
      <div className="absolute inset-0 bg-gradient-to-br from-primary-500/6 to-purple-500/6 rounded-3xl" style={{ transform: 'translateZ(-35px)' }} />
      <div className={cn('absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-15 transition-opacity duration-500 rounded-3xl', feature.color)} style={{ transform: 'translateZ(-25px)' }} />
      
      <motion.div initial={{ scale: 0, rotate: -180 }} whileInView={{ scale: 1, rotate: 0 }}
        viewport={{ once: true }} transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
        className={cn('inline-flex p-5 rounded-2xl bg-gradient-to-br mb-5 shadow-2xl border', feature.color)}
        style={{ transform: 'translateZ(35px)', borderImage: 'linear-gradient(135deg, rgba(255,255,255,0.4), transparent) 1' }}>
        <feature.icon className="h-7 w-7 text-white drop-shadow-lg" />
      </motion.div>
      <h3 className="text-2xl font-black text-white mb-3 drop-shadow-lg" style={{ transform: 'translateZ(30px)' }}>{feature.title}</h3>
      <p className="text-gray-400 leading-relaxed" style={{ transform: 'translateZ(20px)' }}>{feature.description}</p>
    </motion.div>
  );
}

// Channels Section
function ChannelsSection() {
  const channels = [
    { icon: Mail, name: 'Email', description: 'Traditional email support with AI automation', color: 'text-blue-400', bg: 'bg-blue-500/15', border: 'border-blue-500/40' },
    { icon: MessageSquare, name: 'WhatsApp', description: 'Instant messaging with global reach', color: 'text-green-400', bg: 'bg-green-500/15', border: 'border-green-500/40' },
    { icon: Monitor, name: 'Web Form', description: 'Custom forms on your website', color: 'text-purple-400', bg: 'bg-purple-500/15', border: 'border-purple-500/40' },
  ];

  return (
    <section className="py-32 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-20">
          <h2 className="text-5xl lg:text-6xl font-black text-white mb-5 drop-shadow-2xl">Multi-Channel Support</h2>
          <p className="text-xl text-gray-300">Meet your customers where they are</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {channels.map((channel, index) => (
            <ChannelCard key={channel.name} channel={channel} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}

function ChannelCard({ channel, index }: { channel: any; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 60, scale: 0.85 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true }} transition={{ duration: 0.7, delay: index * 0.15, type: 'spring' }}
      whileHover={{ y: -12, scale: 1.07 }}
      className={cn('p-9 rounded-3xl backdrop-blur-xl border transition-all cursor-pointer shadow-2xl', channel.bg, channel.border)}>
      <div className="flex items-center justify-between mb-5">
        <motion.div whileHover={{ scale: 1.15, rotate: 15 }} className={cn('p-4 rounded-2xl', channel.bg)}>
          <channel.icon className={cn('h-9 w-9', channel.color)} />
        </motion.div>
        <span className="px-4 py-2 bg-green-500/25 text-green-300 text-sm rounded-full font-bold border border-green-500/40 flex items-center gap-2 shadow-lg">
          <span className="w-2.5 h-2.5 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-500/50" />
          active
        </span>
      </div>
      <h3 className="text-2xl font-black text-white mb-2 drop-shadow-lg">{channel.name}</h3>
      <p className="text-gray-400">{channel.description}</p>
    </motion.div>
  );
}

// Benefits Section
function BenefitsSection() {
  const benefits = [
    { icon: Zap, title: 'Lightning Fast', description: 'AI responses in seconds, not hours.' },
    { icon: Shield, title: 'Enterprise Security', description: 'Bank-level encryption and compliance.' },
    { icon: Clock, title: '24/7 Availability', description: 'Never miss a customer inquiry.' },
    { icon: Award, title: 'Proven Results', description: '87% resolution rate, 4.6/5 satisfaction.' },
  ];

  return (
    <section id="benefits" className="py-32 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-20">
          <h2 className="text-5xl lg:text-6xl font-black text-white mb-5 drop-shadow-2xl">Why Choose CloudManage?</h2>
          <p className="text-xl text-gray-300">Built for modern support teams</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {benefits.map((benefit, index) => (
            <BenefitCard key={benefit.title} benefit={benefit} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}

function BenefitCard({ benefit, index }: { benefit: any; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div ref={ref} initial={{ opacity: 0, x: index % 2 === 0 ? -70 : 70, rotateY: index % 2 === 0 ? -15 : 15 }}
      whileInView={{ opacity: 1, x: 0, rotateY: 0 }}
      viewport={{ once: true }} transition={{ duration: 0.7, delay: index * 0.1, type: 'spring' }}
      whileHover={{ x: index % 2 === 0 ? 15 : -15, scale: 1.04, rotateY: index % 2 === 0 ? 10 : -10 }}
      className="group flex items-start gap-5 p-7 rounded-2xl bg-gradient-to-br from-gray-800/70 to-gray-800/50 backdrop-blur-xl border border-gray-600/50 hover:border-primary-500/50 transition-all cursor-pointer shadow-2xl">
      <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 shadow-2xl flex-shrink-0 border border-white/20">
        <benefit.icon className="h-7 w-7 text-white drop-shadow-lg" />
      </div>
      <div>
        <h3 className="text-2xl font-black text-white mb-2 drop-shadow-lg">{benefit.title}</h3>
        <p className="text-gray-400 leading-relaxed">{benefit.description}</p>
      </div>
    </motion.div>
  );
}

// Testimonials Section
function TestimonialsSection() {
  const testimonials = [
    { name: 'Sarah Johnson', role: 'Support Manager', content: 'CloudManage transformed our support. Response times dropped by 80%.', avatar: '👩‍💼' },
    { name: 'Mike Chen', role: 'CTO', content: 'The AI handles 87% of tickets without human intervention.', avatar: '👨‍💻' },
    { name: 'Emily Davis', role: 'Customer Success', content: 'Our team can now focus on complex issues. Game changer!', avatar: '👩‍🎨' },
  ];

  return (
    <section id="testimonials" className="py-32 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-20">
          <h2 className="text-5xl lg:text-6xl font-black text-white mb-5 drop-shadow-2xl">Loved by Support Teams</h2>
          <p className="text-xl text-gray-300">See what our customers say</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard key={testimonial.name} testimonial={testimonial} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}

function TestimonialCard({ testimonial, index }: { testimonial: any; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 60 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }} transition={{ duration: 0.7, delay: index * 0.15, type: 'spring' }}
      whileHover={{ y: -10, scale: 1.05 }}
      className="p-7 rounded-3xl bg-gradient-to-br from-gray-800/70 to-gray-800/50 backdrop-blur-xl border border-gray-600/50 hover:border-primary-500/50 transition-all cursor-pointer shadow-2xl">
      <div className="flex gap-1.5 mb-5">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className="h-5 w-5 text-yellow-400 fill-yellow-400 drop-shadow-lg" />
        ))}
      </div>
      <p className="text-gray-300 mb-5 leading-relaxed">"{testimonial.content}"</p>
      <div className="flex items-center gap-3">
        <span className="text-4xl drop-shadow-lg">{testimonial.avatar}</span>
        <div>
          <p className="font-bold text-white drop-shadow-lg">{testimonial.name}</p>
          <p className="text-sm text-gray-400">{testimonial.role}</p>
        </div>
      </div>
    </motion.div>
  );
}

// CTA Section with dramatic 3D
function CTASection() {
  return (
    <section className="py-32 relative overflow-hidden">
      <div className="absolute inset-0">
        <motion.div animate={{ scale: [1, 1.4, 1], rotate: [0, 180, 360] }}
          transition={{ duration: 30, repeat: Infinity }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-gradient-to-br from-primary-600/30 via-purple-600/25 to-pink-600/30 rounded-full filter blur-3xl opacity-60" />
      </div>
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div initial={{ opacity: 0, scale: 0.85, rotateX: 20 }}
          whileInView={{ opacity: 1, scale: 1, rotateX: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.8, type: 'spring' }}
          className="relative bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 rounded-3xl p-12 text-center shadow-2xl overflow-hidden border border-white/20">
          
          <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/15 to-white/0 animate-shimmer" />
          <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent rounded-3xl" style={{ transform: 'translateZ(-20px)' }} />
          
          <div style={{ transform: 'translateZ(30px)' }}>
            <h2 className="text-4xl lg:text-5xl font-black text-white mb-5 drop-shadow-2xl">Ready to Transform Your Support?</h2>
            <p className="text-xl text-white/90 mb-8">Join the future of customer success automation</p>
            <Link href="/dashboard"
              className="inline-flex items-center gap-2 px-10 py-5 bg-white text-primary-600 font-black rounded-2xl transition-all shadow-2xl hover:scale-105 text-xl">
              Go to Dashboard
              <ArrowRight className="h-6 w-6" />
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// Footer
function Footer() {
  return (
    <footer className="border-t border-gray-800/50 py-10 bg-gray-950/95 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-5">
          <motion.div className="flex items-center gap-3" whileHover={{ scale: 1.08 }}>
            <div className="flex items-center justify-center w-11 h-11 bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl shadow-2xl shadow-primary-500/40">
              <Cloud className="h-6 w-6 text-white drop-shadow-lg" />
            </div>
            <div>
              <span className="text-lg font-bold text-white drop-shadow-lg">CloudManage</span>
              <p className="text-xs text-gray-400">Customer Success Digital FTE</p>
            </div>
          </motion.div>
          <div className="flex items-center gap-5 text-sm text-gray-400">
            <span>© 2026 CloudManage.</span>
            <Star className="h-4 w-4 text-primary-500" />
            <span>Powered by AI</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

function cn(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(' ');
}
