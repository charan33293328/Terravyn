import React from 'react';

const SkeletonLoader = ({ type = "card", count = 1 }) => {
  const CardSkeleton = () => (
    <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 flex items-center gap-4 animate-pulse">
      <div className="w-14 h-14 bg-slate-200 rounded-xl shrink-0"></div>
      <div className="w-full space-y-2">
        <div className="h-4 bg-slate-200 rounded w-1/3"></div>
        <div className="h-6 bg-slate-200 rounded w-1/2"></div>
      </div>
    </div>
  );

  const ListSkeleton = () => (
    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 overflow-hidden animate-pulse">
      <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 flex justify-between">
        <div className="h-5 bg-slate-200 rounded w-1/4"></div>
      </div>
      <div className="divide-y divide-slate-50">
        {[1, 2, 3].map(i => (
          <div key={i} className="p-4 px-6 flex justify-between">
            <div className="space-y-2 w-1/2">
              <div className="h-4 bg-slate-200 rounded w-3/4"></div>
              <div className="h-3 bg-slate-200 rounded w-1/2"></div>
            </div>
            <div className="h-6 bg-slate-200 rounded w-16"></div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className={`gap-4 ${type === 'card' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4' : 'flex flex-col'}`}>
      {Array.from({ length: count }).map((_, i) => (
        <React.Fragment key={i}>
          {type === 'card' && <CardSkeleton />}
          {type === 'list' && <ListSkeleton />}
        </React.Fragment>
      ))}
    </div>
  );
};

export default SkeletonLoader;
