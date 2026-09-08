import React, { useRef, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Leaf } from 'lucide-react';

const getMediaConfig = (lang) => {
  const languageMap = {
    en: { video: '/videos/onboarding-en.mp4', thumb: '/thumbnails/onboarding-en.jpg' },
    te: { video: '/videos/onboarding-te.mp4', thumb: '/thumbnails/onboarding-te.jpg' },
    hi: { video: '/videos/onboarding-hi.mp4', thumb: '/thumbnails/onboarding-hi.jpg' },
    ta: { video: '/videos/onboarding-ta.mp4', thumb: '/thumbnails/onboarding-ta.jpg' },
    kn: { video: '/videos/onboarding-kn.mp4', thumb: '/thumbnails/onboarding-kn.jpg' },
    mr: { video: '/videos/onboarding-mr.mp4', thumb: '/thumbnails/onboarding-mr.jpg' }
  };
  return languageMap[lang] || languageMap.en;
};

const OnboardingVideoInner = ({ customVideoUrl, customThumbUrl }) => {
  const videoRef = useRef(null);
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  
  const config = getMediaConfig(lang);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(customVideoUrl || config.video);
  const [currentThumb, setCurrentThumb] = useState(customThumbUrl || config.thumb);
  const [thumbStatus, setThumbStatus] = useState('loading'); // 'loading', 'success', 'fallback_loading', 'fallback_used', 'failed'

  useEffect(() => {
    // Reset state on language change
    const newConfig = getMediaConfig(lang);
    setIsPlaying(false);
    setCurrentVideo(customVideoUrl || newConfig.video);
    setCurrentThumb(customThumbUrl || newConfig.thumb);
    setThumbStatus('loading');
    
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
      videoRef.current.load();
    }
    
    console.log(`Selected Language: ${lang}`);
    console.log(`Selected Video: ${newConfig.video}`);
    console.log(`Selected Thumbnail: ${newConfig.thumb}`);
  }, [lang]);

  const handlePlayClick = () => {
    if (videoRef.current) {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handlePlay = () => setIsPlaying(true);
  const handlePause = () => setIsPlaying(false);

  // Auto-pause when scrolled out of view
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting && videoRef.current && !videoRef.current.paused) {
            videoRef.current.pause();
            setIsPlaying(false);
          }
        });
      },
      { threshold: 0.1 }
    );

    if (videoRef.current) {
      observer.observe(videoRef.current);
    }

    return () => {
      if (videoRef.current) {
        observer.unobserve(videoRef.current);
      }
    };
  }, []);

  const handleThumbLoad = () => {
    if (thumbStatus === 'loading') {
      setThumbStatus('success');
      console.log('Thumbnail Loaded Successfully: true');
      console.log('Fallback Used: false');
    } else if (thumbStatus === 'fallback_loading') {
      setThumbStatus('fallback_used');
      console.log('Thumbnail Loaded Successfully: true');
      console.log('Fallback Used: true');
    }
  };

  const handleThumbError = () => {
    if (currentThumb !== '/thumbnails/onboarding-en.jpg') {
      console.log('Thumbnail Loaded Successfully: false');
      console.log('Fallback Used: true (switching to English)');
      setCurrentThumb('/thumbnails/onboarding-en.jpg');
      setThumbStatus('fallback_loading');
    } else {
      console.log('Thumbnail Loaded Successfully: false');
      console.log('Fallback Used: true (neutral placeholder)');
      setThumbStatus('failed');
    }
  };

  const handleVideoError = () => {
    if (currentVideo !== '/videos/onboarding-en.mp4') {
      setCurrentVideo('/videos/onboarding-en.mp4');
      if (videoRef.current) {
        videoRef.current.load();
      }
    }
  };

  return (
    <div className="w-full">
      <div className="relative w-full pt-[56.25%] rounded-[24px] overflow-hidden shadow-xl border-2 border-brand/20 bg-slate-900 transition-all duration-300 hover:shadow-2xl hover:border-brand/40 group">
        
        {/* Actual Video Player */}
        <video
          ref={videoRef}
          src={currentVideo}
          preload="metadata"
          controls={isPlaying}
          onPlay={handlePlay}
          onPause={handlePause}
          onEnded={handlePause}
          onError={handleVideoError}
          className="absolute top-0 left-0 w-full h-full block bg-black object-cover"
          aria-label={t('howItWorks.videoTitle')}
        >
          {t('howItWorks.videoFallback')}
        </video>
        
        {/* Dedicated Thumbnail Layer */}
        {!isPlaying && (
          <div 
            className="absolute inset-0 z-10 cursor-pointer group/overlay flex flex-col items-center justify-center bg-slate-900"
            onClick={handlePlayClick}
          >
            {/* Thumbnail Image or Neutral Placeholder */}
            {thumbStatus !== 'failed' ? (
              <img 
                src={currentThumb} 
                alt="Video Thumbnail" 
                onLoad={handleThumbLoad}
                onError={handleThumbError}
                className="absolute inset-0 w-full h-full object-cover"
              />
            ) : (
              <div className="absolute inset-0 w-full h-full flex flex-col items-center justify-center bg-slate-800 text-slate-500">
                <Leaf className="w-16 h-16 text-brand/40 mb-4" />
                <span className="text-lg font-medium">TERRAVYN</span>
              </div>
            )}
            
            {/* Play Button Overlay */}
            <div className="absolute inset-0 bg-black/20 transition-colors group-hover/overlay:bg-black/10" />
            <div className="relative z-20 w-16 h-16 md:w-20 md:h-20 bg-brand text-white rounded-full flex items-center justify-center shadow-lg shadow-brand/30 transform transition-transform group-hover/overlay:scale-110">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1 md:w-10 md:h-10 w-8 h-8">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-8 text-center px-4">
        <h4 className="text-xl font-bold text-slate-900 mb-2">{t('howItWorks.videoTitle')}</h4>
        <p className="text-lg text-slate-600">
          {t('howItWorks.videoDesc')}
        </p>
      </div>
    </div>
  );
};

// Wrapper forces remount of the inner component on language change
const OnboardingVideo = (props) => {
  const { i18n } = useTranslation();
  return <OnboardingVideoInner key={i18n.language || 'en'} {...props} />;
};

export default OnboardingVideo;
