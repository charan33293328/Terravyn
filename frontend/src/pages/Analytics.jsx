import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { ShieldCheck, AlertTriangle, CloudRain, Download } from 'lucide-react';
import apiClient from '../api/client';

const Analytics = () => {
  const [tempData, setTempData] = useState([]);
  const [moistureData, setMoistureData] = useState([]);
  const [efficiencyData, setEfficiencyData] = useState([
    { bin: '1', val: 40 }, { bin: '2', val: 50 }, { bin: '3', val: 65 }, { bin: '4', val: 80 },
    { bin: '5', val: 95 }, { bin: '6', val: 85 }, { bin: '7', val: 70 }, { bin: '8', val: 55 },
  ]);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const tempRes = await apiClient.get('/analytics/temperature');
        setTempData(tempRes.data.map(d => ({ day: d.day, temp: d.temp })));
        
        const moistureRes = await apiClient.get('/analytics/soil');
        setMoistureData(moistureRes.data.map(d => ({ time: d.day, fieldA: d.moisture, fieldB: d.moisture - 5 })));
      } catch (err) {
        console.error("Failed to fetch analytics", err);
      }
    };
    fetchAnalytics();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">System Analytics</h2>
          <p className="text-slate-500">Advanced performance insights across all registered sectors.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center bg-white border border-slate-200 rounded-lg px-4 py-2 text-sm text-slate-600 shadow-sm">
             <span className="font-medium mr-2">05/01/2026</span> / <span className="font-medium ml-2">05/31/2026</span>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg shadow-sm hover:bg-brand-dark transition-colors font-medium text-sm">
            <Download className="w-4 h-4"/> Download Detailed Analytics
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col">
           <div className="flex justify-between items-center mb-6">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-brand"/> AI Insights</h3>
              <span className="px-2 py-1 bg-green-50 text-green-600 text-xs font-bold rounded">Live</span>
           </div>
           <div className="space-y-4 flex-1">
              <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-100 flex items-start gap-3">
                 <ShieldCheck className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
                 <div>
                    <p className="text-sm font-semibold text-emerald-800 mb-1">Field A-1 health optimal</p>
                    <p className="text-xs text-emerald-600/80">Growth rate +12% vs last cycle. Moisture levels within target range.</p>
                 </div>
              </div>
              <div className="p-4 bg-red-50 rounded-lg border border-red-100 flex items-start gap-3">
                 <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                 <div>
                    <p className="text-sm font-semibold text-red-800 mb-1">Nutrient Deficiency</p>
                    <p className="text-xs text-red-600/80">Nitrogen levels slightly low in Sector B. Adjust fertigation schedule.</p>
                 </div>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-100 flex items-start gap-3">
                 <CloudRain className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" />
                 <div>
                    <p className="text-sm font-semibold text-blue-800 mb-1">Weather Alert</p>
                    <p className="text-xs text-blue-600/80">Incoming precipitation expected in &lt;6h. Irrigation paused to conserve.</p>
                 </div>
              </div>
           </div>
        </div>

        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
           <div className="flex justify-between items-center mb-6">
              <div>
                 <h3 className="font-semibold text-slate-800">Temperature Trends</h3>
                 <p className="text-xs text-slate-500">Average ambient temperature per sector (°C)</p>
              </div>
              <select className="px-3 py-1 bg-slate-50 border border-slate-200 rounded text-sm text-slate-600 outline-none">
                 <option>Last 7 Days</option>
                 <option>Last 30 Days</option>
              </select>
           </div>
           <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                 <BarChart data={tempData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                    <YAxis axisLine={false} tickLine={false} tick={false} />
                    <RechartsTooltip cursor={{fill: '#f1f5f9'}} contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}/>
                    <Bar dataKey="temp" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                 </BarChart>
              </ResponsiveContainer>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
         <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-6">
               <div>
                  <h3 className="font-semibold text-slate-800">Soil Moisture Trends</h3>
                  <p className="text-xs text-slate-500">Real-time percentage per field</p>
               </div>
               <div className="flex items-center gap-4 text-xs font-medium">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-brand"></span> Field A</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-300"></span> Field B</span>
               </div>
            </div>
            <div className="h-56">
               <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={moistureData}>
                    <XAxis dataKey="time" hide />
                    <YAxis hide />
                    <Line type="monotone" dataKey="fieldA" stroke="#0A7D40" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="fieldB" stroke="#cbd5e1" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                 </LineChart>
               </ResponsiveContainer>
            </div>
         </div>

         <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="mb-6">
               <h3 className="font-semibold text-slate-800">Efficiency vs Yield</h3>
               <p className="text-xs text-slate-500">Correlation of irrigation-to-growth ratio</p>
            </div>
            <div className="h-40 mb-4">
               <ResponsiveContainer width="100%" height="100%">
                 <BarChart data={efficiencyData}>
                    <Bar dataKey="val">
                       {efficiencyData.map((entry, index) => (
                          <cell key={`cell-${index}`} fill={entry.val > 80 ? '#22c55e' : entry.val > 60 ? '#4ade80' : '#86efac'} />
                       ))}
                    </Bar>
                 </BarChart>
               </ResponsiveContainer>
            </div>
            <div className="space-y-2 text-sm">
               <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                  <span className="text-slate-500 font-medium">Operational Efficiency</span>
                  <span className="font-bold text-slate-800">94.2%</span>
               </div>
               <div className="flex justify-between items-center pt-1">
                  <span className="text-slate-500 font-medium">Yield Projection</span>
                  <span className="font-bold text-green-600">+8.5%</span>
               </div>
            </div>
         </div>
      </div>
    </div>
  );
};

export default Analytics;
