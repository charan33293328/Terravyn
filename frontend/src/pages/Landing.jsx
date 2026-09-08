import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Leaf, Droplets, Activity, Shield, ArrowRight, ChevronDown, Package, Wifi, User, QrCode, LayoutDashboard, Plus, Minus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import OnboardingVideo from '../components/OnboardingVideo';
import LanguageSelector from '../components/LanguageSelector';
import { fetchHomepage, fetchFAQs, fetchPublicSettings } from '../api/publicCms';

const getMediaUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
  return `${baseUrl}${path}`;
};

const FAQItem = ({ question, answer }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="border border-slate-200 rounded-xl mb-4 overflow-hidden bg-white">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-5 text-left bg-white hover:bg-slate-50 transition-colors"
      >
        <span className="font-bold text-slate-800 pr-4">{question}</span>
        {isOpen ? <Minus className="text-brand shrink-0" size={20} /> : <Plus className="text-slate-400 shrink-0" size={20} />}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-5 pt-0 text-slate-600 leading-relaxed border-t border-slate-100">
              {answer}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const Landing = () => {
  const { t, i18n } = useTranslation();
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => 
    typeof window !== 'undefined' ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false
  );

  const [cmsData, setCmsData] = useState(null);
  const [faqs, setFaqs] = useState([]);
  const [settings, setSettings] = useState(null);
  const [loadingCms, setLoadingCms] = useState(true);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const listener = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', listener);
    return () => mediaQuery.removeEventListener('change', listener);
  }, []);

  useEffect(() => {
    document.body.classList.add('hide-scrollbar');
    return () => document.body.classList.remove('hide-scrollbar');
  }, []);

  useEffect(() => {
    async function loadContent() {
      setLoadingCms(true);
      const [homeData, faqData, settingsData] = await Promise.all([
        fetchHomepage(i18n.language),
        fetchFAQs(i18n.language),
        fetchPublicSettings()
      ]);
      if (homeData && homeData.data) {
        setCmsData(homeData.data);
      }
      if (faqData) {
        setFaqs(faqData);
      }
      if (settingsData) {
        setSettings(settingsData);
      }
      setLoadingCms(false);
    }
    loadContent();
  }, [i18n.language]);

  // Fallbacks
  const heroTitle = cmsData?.heroTitle || t('hero.title');
  const heroSubtitle = cmsData?.heroSubtitle || t('hero.subtitle');
  const heroDesc = t('hero.desc'); // Kept from translation if not in CMS
  const ctaText = cmsData?.ctaText || t('hero.getStarted');
  const ctaUrl = cmsData?.ctaUrl || '/signup';
  const heroVideoUrl = getMediaUrl(cmsData?.heroVideo) || '/hero-bg.mp4';
  
  const howItWorksTitle = cmsData?.howItWorksTitle || t('howItWorks.title');
  const howItWorksDesc = cmsData?.howItWorksDesc || t('howItWorks.subtitle');
  const howItWorksVideo = getMediaUrl(cmsData?.howItWorksVideo);
  
  const platformName = settings?.platform_name || 'TERRAVYN';
  const companyName = settings?.company_name || 'TERRAVYN Pvt Ltd';

  // Map icon strings to components
  const iconMap = {
    'Droplets': Droplets,
    'Activity': Activity,
    'Shield': Shield,
    'Package': Package,
    'Wifi': Wifi,
    'User': User,
    'QrCode': QrCode,
    'LayoutDashboard': LayoutDashboard
  };

  const activeFeatures = (cmsData?.features || []).filter(f => f.active);

  return (
    <div className="min-h-screen bg-white font-sans text-slate-900">
      {/* Navbar */}
      <nav className="fixed w-full bg-white/80 backdrop-blur-md z-50 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-brand rounded-xl flex items-center justify-center shadow-lg shadow-brand/20">
                <Leaf className="w-6 h-6 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight text-slate-800">{platformName}</span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#home" className="text-sm font-medium text-slate-600 hover:text-brand transition-colors">{t('nav.home')}</a>
              <a href="#features" className="text-sm font-medium text-slate-600 hover:text-brand transition-colors">{t('nav.features')}</a>
              <a href="#how-it-works" className="text-sm font-medium text-slate-600 hover:text-brand transition-colors">{t('nav.howItWorks')}</a>
              <Link to="/pricing" className="text-sm font-medium text-slate-600 hover:text-brand transition-colors">{t('nav.pricing')}</Link>
              {faqs.length > 0 && <a href="#faqs" className="text-sm font-medium text-slate-600 hover:text-brand transition-colors">FAQs</a>}
            </div>
            <div className="flex items-center gap-4">
              <LanguageSelector />
              <Link to="/login" className="text-sm font-medium text-slate-700 hover:text-brand transition-colors">{t('nav.login')}</Link>
              <Link to="/signup" className="px-5 py-2.5 bg-brand text-white text-sm font-medium rounded-lg shadow-md shadow-brand/20 hover:bg-brand-dark transition-all hover:-translate-y-0.5">
                {t('nav.getStarted')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="home" className="relative w-full h-[80vh] lg:h-screen flex items-center justify-center overflow-hidden bg-slate-900">
        <div className="absolute inset-0 bg-[url('/hero-poster.jpg')] bg-cover bg-center bg-no-repeat" aria-hidden="true"></div>

        {!prefersReducedMotion && (
          <motion.video 
            key={heroVideoUrl}
            autoPlay 
            loop 
            muted 
            playsInline 
            controls={false}
            preload="metadata"
            poster="/hero-poster.jpg"
            aria-hidden="true"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
            className="absolute inset-0 w-full h-full object-cover"
          >
            <source src={heroVideoUrl} type="video/mp4" />
          </motion.video>
        )}

        <div className="absolute inset-0 bg-[rgba(0,0,0,0.45)] pointer-events-none z-0"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center flex flex-col items-center justify-center h-full w-full pt-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            className="space-y-6"
          >
            <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight text-white drop-shadow-lg">
              {heroTitle}
            </h1>
            <h2 className="text-xl md:text-3xl font-medium tracking-wide text-brand-light text-green-300 drop-shadow-md max-w-4xl mx-auto whitespace-pre-line">
              {heroSubtitle}
            </h2>
          </motion.div>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="mt-8 max-w-2xl mx-auto text-lg md:text-2xl font-light text-slate-300 leading-relaxed drop-shadow-sm"
          >
            {heroDesc}
          </motion.p>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="mt-12 flex flex-col sm:flex-row justify-center items-center gap-6"
          >
            <Link to={ctaUrl} className="px-8 py-4 bg-brand/90 hover:bg-brand text-white text-lg font-medium rounded-full backdrop-blur-md shadow-[0_8px_32px_rgba(10,125,64,0.4)] border border-brand-light/20 transition-all hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(10,125,64,0.6)] flex items-center justify-center gap-2 group">
              {ctaText} 
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a href="#features" className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white text-lg font-medium rounded-full backdrop-blur-xl border border-white/10 transition-all hover:-translate-y-1 shadow-[0_8px_32px_rgba(0,0,0,0.2)] hover:border-white/20 flex items-center justify-center">
              {t('hero.exploreDashboard')}
            </a>
          </motion.div>
        </div>

        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.5 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center justify-center cursor-pointer opacity-70 hover:opacity-100 transition-opacity"
          onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
        >
          <span className="text-xs tracking-widest text-white/70 uppercase mb-2">Scroll</span>
          <motion.div animate={{ y: [0, 8, 0] }} transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}>
            <ChevronDown className="w-6 h-6 text-white/70" />
          </motion.div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">{t('features.title')}</h2>
            <p className="mt-4 text-slate-500">{t('features.subtitle')}</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {activeFeatures.length > 0 ? (
              activeFeatures.map((feat, idx) => {
                const IconComponent = iconMap[feat.icon] || Droplets;
                return (
                  <div key={idx} className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-xl transition-shadow">
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                      <IconComponent className="w-6 h-6 text-brand" />
                    </div>
                    <h3 className="text-xl font-bold mb-3">{feat.title}</h3>
                    <p className="text-slate-600 leading-relaxed">{feat.description}</p>
                  </div>
                );
              })
            ) : (
              // Fallback features if CMS is empty
              <>
                <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-xl transition-shadow">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                    <Droplets className="w-6 h-6 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-bold mb-3">{t('features.f1_title')}</h3>
                  <p className="text-slate-600 leading-relaxed">{t('features.f1_desc')}</p>
                </div>
                <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-xl transition-shadow">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                    <Activity className="w-6 h-6 text-brand" />
                  </div>
                  <h3 className="text-xl font-bold mb-3">{t('features.f2_title')}</h3>
                  <p className="text-slate-600 leading-relaxed">{t('features.f2_desc')}</p>
                </div>
                <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-xl transition-shadow">
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-6">
                    <Shield className="w-6 h-6 text-orange-600" />
                  </div>
                  <h3 className="text-xl font-bold mb-3">{t('features.f3_title')}</h3>
                  <p className="text-slate-600 leading-relaxed">{t('features.f3_desc')}</p>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-24 bg-slate-50 relative overflow-hidden border-t border-slate-100">
        <div className="absolute top-0 right-0 w-1/2 h-full bg-brand/5 skew-x-12 translate-x-32 hidden lg:block"></div>
        <motion.div 
          initial={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.15 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10"
        >
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-extrabold text-slate-900 tracking-tight">{howItWorksTitle}</h2>
            <p className="mt-4 text-lg lg:text-xl text-slate-500 whitespace-pre-line">{howItWorksDesc}</p>
          </div>
          
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-start">
            <div className="space-y-6 lg:space-y-8">
              {[
                { step: 1, title: t('howItWorks.step1_title'), desc: t('howItWorks.step1_desc'), icon: Package },
                { step: 2, title: t('howItWorks.step2_title'), desc: t('howItWorks.step2_desc'), icon: Wifi },
                { step: 3, title: t('howItWorks.step3_title'), desc: t('howItWorks.step3_desc'), icon: User },
                { step: 4, title: t('howItWorks.step4_title'), desc: t('howItWorks.step4_desc'), icon: QrCode },
                { step: 5, title: t('howItWorks.step5_title'), desc: t('howItWorks.step5_desc'), icon: LayoutDashboard },
                { step: 6, title: t('howItWorks.step6_title'), desc: t('howItWorks.step6_desc'), icon: Droplets }
              ].map((item, idx) => (
                <div key={item.step} className="flex gap-4 lg:gap-6 items-start group">
                  <div className={`flex-shrink-0 w-12 h-12 lg:w-14 lg:h-14 rounded-full flex items-center justify-center text-lg lg:text-xl font-bold shadow-md transition-all duration-300 group-hover:scale-110 ${idx % 2 === 0 ? 'bg-brand text-white' : 'bg-green-100 text-brand border-2 border-brand/20'}`}>
                    {item.step}
                  </div>
                  <div className="bg-white p-5 lg:p-6 rounded-2xl shadow-sm border border-slate-100 flex-1 hover:shadow-lg transition-all duration-300 group-hover:-translate-y-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="p-2 bg-slate-50 rounded-lg text-slate-600 hidden sm:block">
                        <item.icon className="w-5 h-5" />
                      </div>
                      <h4 className="text-lg lg:text-xl font-bold text-slate-800">{item.title}</h4>
                    </div>
                    <p className="text-slate-600 leading-relaxed sm:pl-12 lg:pl-14 text-sm lg:text-base">
                      {item.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="lg:sticky lg:top-32 mt-8 lg:mt-0">
              <OnboardingVideo prefersReducedMotion={prefersReducedMotion} customVideoUrl={howItWorksVideo} />
            </div>
          </div>
        </motion.div>
      </section>

      {/* FAQs Section */}
      {faqs.length > 0 && (
        <section id="faqs" className="py-24 bg-white">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-slate-900">Frequently Asked Questions</h2>
            </div>
            <div>
              {faqs.map(faq => (
                <FAQItem key={faq.id} question={faq.question} answer={faq.answer} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Testimonials Section */}
      <section className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">Trusted by Farmers</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="p-8 bg-white rounded-2xl shadow-sm border border-slate-100">
              <p className="text-lg text-slate-700 italic mb-6">"TERRAVYN completely changed how we manage our orchards. The real-time alerts saved our crop during the heatwave last summer."</p>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-brand/10 rounded-full flex items-center justify-center text-brand font-bold text-xl">J</div>
                <div>
                  <h4 className="font-bold text-slate-900">Julian Sterling</h4>
                  <p className="text-sm text-slate-500">Farm Manager, Sterling Orchards</p>
                </div>
              </div>
            </div>
            <div className="p-8 bg-white rounded-2xl shadow-sm border border-slate-100">
              <p className="text-lg text-slate-700 italic mb-6">"The integration with our existing ESP32 sensors was flawless. The dashboard is intuitive and incredibly responsive."</p>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-xl">S</div>
                <div>
                  <h4 className="font-bold text-slate-900">Sarah Jenkins</h4>
                  <p className="text-sm text-slate-500">AgriTech Systems</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Call To Action Section */}
      <section className="py-20 bg-brand text-white text-center">
        <div className="max-w-3xl mx-auto px-4">
          <h2 className="text-4xl font-bold mb-6">Ready to upgrade your farm?</h2>
          <p className="text-lg text-green-100 mb-10">Join the smart agriculture revolution today. Deploy your first sensor node in minutes.</p>
          <Link to="/signup" className="px-8 py-4 bg-white text-brand font-bold rounded-xl shadow-xl hover:bg-slate-50 transition-all hover:scale-105 inline-block">
            Create Your Account
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 py-12 text-center text-slate-400">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-center items-center gap-2 mb-6">
            <Leaf className="w-5 h-5 text-brand" />
            <span className="font-bold text-lg text-white">{platformName}</span>
          </div>
          <p>&copy; {new Date().getFullYear()} {companyName}. {t('footer.rights')}</p>
          {settings?.support_email && (
            <p className="mt-2 text-sm text-slate-500">Support: {settings.support_email}</p>
          )}
        </div>
      </footer>
    </div>
  );
};

export default Landing;
