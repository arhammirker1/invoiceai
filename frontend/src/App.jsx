import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  Download, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  User,
  LogOut,
  Settings,
  CreditCard,
  BarChart3,
  X,
  Mail,
  Google,
  Sparkles,
  ArrowRight,
  File,
  Zap
} from 'lucide-react';
import { GoogleLogin } from "@react-oauth/google";

// Color palette
const colors = {
  cream: '#fdf6ec',
  matcha: '#a4c3a2',
  matchaDark: '#8faf8d',
  text: '#2d3436',
  textLight: '#636e72'
};

// Mock data and auth context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const login = async (method, data) => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setUser({
        id: 1,
        email: data.email || 'user@example.com',
        name: 'John Doe',
        plan: 'trial',
        credits: 50,
        trialEnds: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)
      });
      setLoading(false);
    }, 1000);
  };

  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Auth Modal Component

const AuthModal = ({ isOpen, onClose }) => {
  const [mode, setMode] = useState('login'); // 'login' or 'magic-link'
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();






  const handleMagicLink = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    // Simulate sending magic link
    setTimeout(() => {
      setIsSubmitting(false);
      login('magic-link', { email });
      onClose();
    }, 1500);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Welcome Back</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X size={24} />
            </button>
          </div>

          {mode === 'login' ? (
            <div className="space-y-4">
              <GoogleLogin
  onSuccess={async (credentialResponse) => {
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: "google",
          token: credentialResponse.credential,
        }),
      });

      if (!res.ok) throw new Error("Login failed");
      const data = await res.json();

      // Save the user + token in frontend
      login("google", data);
      onClose();
    } catch (err) {
      console.error("Google login error:", err);
    }
  }}
  onError={() => {
    console.log("Google Login Failed");
  }}
/>


              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-gray-200"></div>
                <span className="text-sm text-gray-500">or</span>
                <div className="flex-1 h-px bg-gray-200"></div>
              </div>

              <button
                onClick={() => setMode('magic-link')}
                className="w-full flex items-center justify-center gap-3 rounded-xl py-3 px-4 text-white transition-colors"
                style={{ backgroundColor: colors.matcha }}
              >
                <Mail size={20} />
                Continue with Email
              </button>
            </div>
          ) : (
            <form onSubmit={handleMagicLink} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-matcha focus:border-transparent outline-none"
                  placeholder="Enter your email"
                  required
                />
              </div>
              
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-xl py-3 px-4 text-white font-medium transition-colors disabled:opacity-50"
                style={{ backgroundColor: colors.matcha }}
              >
                {isSubmitting ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Sending Magic Link...
                  </div>
                ) : (
                  'Send Magic Link'
                )}
              </button>

              <button
                type="button"
                onClick={() => setMode('login')}
                className="w-full text-gray-600 hover:text-gray-900 transition-colors"
              >
                ← Back to login options
              </button>
            </form>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// Landing Page Component
const LandingPage = ({ onLogin }) => {
  return (
    <div className="min-h-screen" style={{ backgroundColor: colors.cream }}>
      {/* Navigation */}
      <nav className="flex justify-between items-center p-6 md:p-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-2"
        >
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: colors.matcha }}
          >
            <Sparkles size={20} className="text-white" />
          </div>
          <span className="text-xl font-bold" style={{ color: colors.text }}>
            InvoiceAI
          </span>
        </motion.div>

        <motion.button
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={onLogin}
          className="px-6 py-2 rounded-lg text-white font-medium hover:scale-105 transition-transform"
          style={{ backgroundColor: colors.matcha }}
        >
          Sign In
        </motion.button>
      </nav>

      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-6 md:px-8 py-12 md:py-20">
        <div className="text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border mb-8"
            style={{ 
              backgroundColor: 'rgba(164, 195, 162, 0.1)',
              borderColor: colors.matcha 
            }}
          >
            <Zap size={16} style={{ color: colors.matcha }} />
            <span className="text-sm font-medium" style={{ color: colors.matcha }}>
              AI-Powered Invoice Processing
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-4xl md:text-6xl font-bold mb-6"
            style={{ color: colors.text }}
          >
            Transform Invoices to{' '}
            <span
              className="bg-gradient-to-r bg-clip-text text-transparent"
              style={{
                backgroundImage: `linear-gradient(135deg, ${colors.matcha}, ${colors.matchaDark})`
              }}
            >
              Excel Magic
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-xl md:text-2xl mb-8 max-w-3xl mx-auto"
            style={{ color: colors.textLight }}
          >
            Upload any invoice format and get perfectly structured Excel files in seconds. 
            Powered by advanced AI that understands your documents.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
          >
            <button
              onClick={onLogin}
              className="px-8 py-4 rounded-xl text-white font-semibold text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2"
              style={{ backgroundColor: colors.matcha }}
            >
              Start Free Trial
              <ArrowRight size={20} />
            </button>
            
            <button className="px-8 py-4 rounded-xl font-semibold text-lg border-2 hover:scale-105 transition-transform"
              style={{ 
                borderColor: colors.matcha,
                color: colors.matcha
              }}
            >
              Watch Demo
            </button>
          </motion.div>

          {/* Animated Invoice → Excel Graphic */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="relative max-w-4xl mx-auto"
          >
            <div className="flex items-center justify-center gap-8 md:gap-16">
              {/* Invoice */}
              <motion.div
                animate={{ 
                  y: [0, -10, 0],
                  rotateY: [0, 5, 0]
                }}
                transition={{ 
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="w-32 h-40 md:w-48 md:h-60 rounded-lg shadow-2xl flex flex-col items-center justify-center"
                style={{ backgroundColor: 'white' }}
              >
                <FileText size={40} style={{ color: colors.matcha }} className="mb-4" />
                <div className="space-y-2 px-4">
                  <div className="h-2 bg-gray-200 rounded w-full"></div>
                  <div className="h-2 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-2 bg-gray-200 rounded w-1/2"></div>
                </div>
              </motion.div>

              {/* Arrow */}
              <motion.div
                animate={{ x: [0, 10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
                style={{ color: colors.matcha }}
              >
                <ArrowRight size={32} />
              </motion.div>

              {/* Excel */}
              <motion.div
                animate={{ 
                  y: [0, -10, 0],
                  rotateY: [0, -5, 0]
                }}
                transition={{ 
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: 0.5
                }}
                className="w-32 h-40 md:w-48 md:h-60 rounded-lg shadow-2xl flex flex-col"
                style={{ backgroundColor: colors.matcha }}
              >
                <div className="bg-white rounded-t-lg p-4 flex-1">
                  <div className="grid grid-cols-3 gap-1 h-full">
                    {Array.from({ length: 15 }).map((_, i) => (
                      <div
                        key={i}
                        className="bg-gray-100 rounded"
                        style={{
                          backgroundColor: i < 3 ? colors.matcha : '#f1f2f6'
                        }}
                      ></div>
                    ))}
                  </div>
                </div>
                <div className="p-2 text-center">
                  <span className="text-white text-xs font-medium">Excel Ready</span>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white py-20">
        <div className="max-w-6xl mx-auto px-6 md:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ color: colors.text }}>
              Why Choose InvoiceAI?
            </h2>
            <p className="text-xl" style={{ color: colors.textLight }}>
              Advanced AI technology meets beautiful design
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Zap,
                title: "Lightning Fast",
                desc: "Process 100+ invoices in minutes with our advanced AI pipeline"
              },
              {
                icon: CheckCircle,
                title: "99% Accuracy",
                desc: "Industry-leading OCR and data extraction with manual verification"
              },
              {
                icon: File,
                title: "Any Format",
                desc: "PDF, JPG, PNG - upload any invoice format and get perfect Excel output"
              }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 * i }}
                className="text-center p-6 rounded-2xl hover:shadow-lg transition-shadow"
                style={{ backgroundColor: colors.cream }}
              >
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                  style={{ backgroundColor: colors.matcha }}
                >
                  <feature.icon size={32} className="text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-2" style={{ color: colors.text }}>
                  {feature.title}
                </h3>
                <p style={{ color: colors.textLight }}>{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Upload Page Component
const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(prev => [...prev, ...droppedFiles.slice(0, 100 - prev.length)]);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(prev => [...prev, ...selectedFiles.slice(0, 100 - prev.length)]);
  };

  const startUpload = () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          // Redirect to dashboard
          return 100;
        }
        return prev + Math.random() * 15;
      });
    }, 200);
  };

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: colors.cream }}>
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-3xl font-bold mb-2" style={{ color: colors.text }}>
            Upload Your Invoices
          </h1>
          <p style={{ color: colors.textLight }}>
            Drop up to 100 files or click to select. Supports PDF, JPG, PNG formats.
          </p>
        </motion.div>

        {/* Upload Area */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className={`border-3 border-dashed rounded-2xl p-12 text-center transition-all ${
            isDragging ? 'border-matcha bg-matcha bg-opacity-10' : 'border-gray-300'
          }`}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onDragEnter={() => setIsDragging(true)}
          onDragLeave={() => setIsDragging(false)}
        >
          <div className="space-y-4">
            <motion.div
              animate={{ 
                y: isDragging ? [0, -10, 0] : [0, -5, 0] 
              }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              <Upload size={48} style={{ color: colors.matcha }} className="mx-auto" />
            </motion.div>
            
            <div>
              <p className="text-lg font-semibold mb-2" style={{ color: colors.text }}>
                Drop your invoices here
              </p>
              <p style={{ color: colors.textLight }}>
                or click to browse files
              </p>
            </div>
            
            <input
              type="file"
              multiple
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileSelect}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className="inline-block px-6 py-3 rounded-lg text-white font-medium cursor-pointer hover:scale-105 transition-transform"
              style={{ backgroundColor: colors.matcha }}
            >
              Browse Files
            </label>
          </div>
        </motion.div>

        {/* File List */}
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8"
          >
            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold" style={{ color: colors.text }}>
                  Selected Files ({files.length}/100)
                </h3>
                <button
                  onClick={() => setFiles([])}
                  className="text-gray-400 hover:text-gray-600"
                >
                  Clear All
                </button>
              </div>
              
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {files.map((file, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <FileText size={20} style={{ color: colors.matcha }} />
                    <span className="flex-1 truncate">{file.name}</span>
                    <span className="text-sm text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                    <button
                      onClick={() => setFiles(files.filter((_, idx) => idx !== i))}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>

              {/* Upload Progress */}
              {isUploading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-6"
                >
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium" style={{ color: colors.text }}>
                      Processing...
                    </span>
                    <span className="text-sm" style={{ color: colors.textLight }}>
                      {Math.round(uploadProgress)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <motion.div
                      className="h-2 rounded-full"
                      style={{ 
                        backgroundColor: colors.matcha,
                        width: `${uploadProgress}%`
                      }}
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </motion.div>
              )}

              {!isUploading && (
                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  onClick={startUpload}
                  className="w-full mt-6 py-4 rounded-xl text-white font-semibold text-lg hover:scale-105 transition-transform"
                  style={{ backgroundColor: colors.matcha }}
                >
                  Process {files.length} Invoice{files.length !== 1 ? 's' : ''}
                </motion.button>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user } = useAuth();
  const [invoices] = useState([
    {
      id: 1,
      filename: 'invoice-001.pdf',
      status: 'completed',
      uploadedAt: '2025-08-29T10:30:00Z',
      vendor: 'ABC Company',
      total: '$1,250.00'
    },
    {
      id: 2,
      filename: 'receipt-002.jpg',
      status: 'processing',
      uploadedAt: '2025-08-29T11:15:00Z',
      vendor: 'XYZ Corp',
      total: null
    },
    {
      id: 3,
      filename: 'bill-003.png',
      status: 'failed',
      uploadedAt: '2025-08-29T09:45:00Z',
      vendor: null,
      total: null
    }
  ]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="text-green-500" size={20} />;
      case 'processing': return <Clock className="text-yellow-500" size={20} />;
      case 'failed': return <AlertCircle className="text-red-500" size={20} />;
      default: return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'processing': return 'text-yellow-600';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: colors.cream }}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-between items-center mb-8"
        >
          <div>
            <h1 className="text-3xl font-bold" style={{ color: colors.text }}>
              Dashboard
            </h1>
            <p style={{ color: colors.textLight }}>
              Welcome back, {user?.name}
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <div 
              className="px-4 py-2 rounded-lg text-white font-medium"
              style={{ backgroundColor: colors.matcha }}
            >
              {user?.credits} credits
            </div>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            { label: 'Total Processed', value: '1,247', icon: FileText },
            { label: 'This Month', value: '89', icon: BarChart3 },
            { label: 'Success Rate', value: '99.2%', icon: CheckCircle }
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="bg-white rounded-2xl p-6 shadow-lg"
            >
              <div className="flex items-center gap-4">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: colors.cream }}
                >
                  <stat.icon size={24} style={{ color: colors.matcha }} />
                </div>
                <div>
                  <p className="text-2xl font-bold" style={{ color: colors.text }}>
                    {stat.value}
                  </p>
                  <p className="text-sm" style={{ color: colors.textLight }}>
                    {stat.label}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Recent Invoices */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl shadow-lg overflow-hidden"
        >
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-xl font-semibold" style={{ color: colors.text }}>
              Recent Invoices
            </h2>
          </div>
          
          <div className="divide-y divide-gray-100">
            {invoices.map((invoice, i) => (
              <motion.div
                key={invoice.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="p-6 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {getStatusIcon(invoice.status)}
                    <div>
                      <p className="font-medium" style={{ color: colors.text }}>
                        {invoice.filename}
                      </p>
                      <p className="text-sm" style={{ color: colors.textLight }}>
                        {invoice.vendor || 'Processing vendor info...'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    {invoice.total && (
                      <span className="font-semibold" style={{ color: colors.text }}>
                        {invoice.total}
                      </span>
                    )}
                    <span className={`text-sm capitalize ${getStatusColor(invoice.status)}`}>
                      {invoice.status}
                    </span>
                    {invoice.status === 'completed' && (
                      <button
                        className="p-2 rounded-lg hover:scale-110 transition-transform"
                        style={{ backgroundColor: colors.cream }}
                      >
                        <Download size={16} style={{ color: colors.matcha }} />
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

// Main App Component
const InvoiceAI = () => {
  const [currentPage, setCurrentPage] = useState('landing');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { user, logout } = useAuth();

  useEffect(() => {
    if (user && currentPage === 'landing') {
      setCurrentPage('dashboard');
    }
  }, [user, currentPage]);

  const handleNavigation = (page) => {
    setCurrentPage(page);
  };

  const handleLogin = () => {
    setShowAuthModal(true);
  };

  // Navigation Component
  const Navigation = () => {
    if (!user) return null;

    return (
      <nav className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <div 
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: colors.matcha }}
                >
                  <Sparkles size={20} className="text-white" />
                </div>
                <span className="text-xl font-bold" style={{ color: colors.text }}>
                  InvoiceAI
                </span>
              </div>
              
              <div className="flex gap-6">
                <button
                  onClick={() => handleNavigation('dashboard')}
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    currentPage === 'dashboard' ? 'bg-matcha text-white' : 'text-gray-600 hover:text-gray-900'
                  }`}
                  style={{ 
                    backgroundColor: currentPage === 'dashboard' ? colors.matcha : 'transparent'
                  }}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => handleNavigation('upload')}
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    currentPage === 'upload' ? 'bg-matcha text-white' : 'text-gray-600 hover:text-gray-900'
                  }`}
                  style={{ 
                    backgroundColor: currentPage === 'upload' ? colors.matcha : 'transparent'
                  }}
                >
                  Upload
                </button>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-sm" style={{ color: colors.textLight }}>
                {user?.credits} credits remaining
              </div>
              <div className="relative">
                <button className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100">
                  <User size={20} style={{ color: colors.text }} />
                </button>
              </div>
              <button
                onClick={logout}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </div>
      </nav>
    );
  };

  return (
    <div className="min-h-screen">
      <Navigation />
      
      <AnimatePresence mode="wait">
        {currentPage === 'landing' && !user && (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <LandingPage onLogin={handleLogin} />
          </motion.div>
        )}
        
        {currentPage === 'upload' && user && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <UploadPage />
          </motion.div>
        )}
        
        {currentPage === 'dashboard' && user && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Dashboard />
          </motion.div>
        )}
      </AnimatePresence>

      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)} 
      />
    </div>
  );
};

// Root App with Auth Provider
const App = () => {
  return (
    <AuthProvider>
      <InvoiceAI />
    </AuthProvider>
  );
};

export default App;
