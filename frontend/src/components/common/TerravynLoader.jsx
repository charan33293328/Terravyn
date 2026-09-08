import React, { useState, useEffect, useRef } from 'react';
import { Leaf } from 'lucide-react';

const TerravynLoader = ({ onComplete }) => {
  const [isFading, setIsFading] = useState(false);
  const [showFallback, setShowFallback] = useState(false);
  const [isReducedMotion, setIsReducedMotion] = useState(false);
  const fallbackTimeoutRef = useRef(null);

  useEffect(() => {
    // Prevent scrolling while loader is active
    document.body.style.overflow = 'hidden';

    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setIsReducedMotion(mediaQuery.matches);

    // Fallback timeout in case video fails to load or play
    fallbackTimeoutRef.current = setTimeout(() => {
      setShowFallback(true);
      // If we're showing the fallback, complete after 3 seconds
      setTimeout(() => {
        finishLoading();
      }, 3000);
    }, 5000); // Wait 5 seconds before deciding video failed to load

    return () => {
      document.body.style.overflow = '';
      if (fallbackTimeoutRef.current) clearTimeout(fallbackTimeoutRef.current);
    };
  }, []);

  const finishLoading = () => {
    setIsFading(true);
    // Unmount after fade duration
    setTimeout(() => {
      document.body.style.overflow = '';
      onComplete();
    }, 600);
  };

  const handleVideoCanPlay = () => {
    // Video is ready, clear the fallback timeout
    if (fallbackTimeoutRef.current) clearTimeout(fallbackTimeoutRef.current);
  };

  const handleVideoError = () => {
    if (fallbackTimeoutRef.current) clearTimeout(fallbackTimeoutRef.current);
    setShowFallback(true);
    setTimeout(() => {
      finishLoading();
    }, 3000);
  };

  // Immediate fallback for reduced motion
  useEffect(() => {
    if (isReducedMotion) {
      if (fallbackTimeoutRef.current) clearTimeout(fallbackTimeoutRef.current);
      setShowFallback(true);
      const timer = setTimeout(() => {
        finishLoading();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isReducedMotion]);

  return (
    <div 
      className={`fixed inset-0 z-[99999] bg-[#0B1120] flex justify-center items-center overflow-hidden transition-opacity duration-600 ease-in-out ${isFading ? 'opacity-0' : 'opacity-100'}`}
    >
      {!showFallback && !isReducedMotion ? (
        <video
          autoPlay
          muted
          playsInline
          preload="auto"
          onEnded={finishLoading}
          onCanPlay={handleVideoCanPlay}
          onError={handleVideoError}
          className="max-w-full max-h-full object-contain"
          style={{ width: '100%', height: '100%' }}
        >
          <source src="/videos/Terravyn%20Loading%20Animation.mp4" type="video/mp4" />
        </video>
      ) : (
        <div className="flex flex-col items-center justify-center space-y-6">
          <div className="w-20 h-20 bg-brand rounded-2xl flex items-center justify-center shadow-lg shadow-brand/20 animate-pulse">
            <Leaf className="w-10 h-10 text-white" />
          </div>
          <div className="flex flex-col items-center space-y-2">
            <h2 className="text-2xl font-bold text-white tracking-widest">TERRAVYN</h2>
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 bg-brand rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-1.5 h-1.5 bg-brand rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-1.5 h-1.5 bg-brand rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <p className="text-slate-400 text-sm mt-2">Loading TERRAVYN...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default TerravynLoader;
