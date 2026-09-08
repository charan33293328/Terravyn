import React, { useState, useEffect } from "react";
import { 
    AlertTriangle, Bell, CheckCircle, Filter, Server, Clock, Check, ChevronRight, Activity
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import apiClient from "../../api/client";
import { useNavigate } from "react-router-dom";

dayjs.extend(relativeTime);

export default function AlertsCenter() {
    const navigate = useNavigate();
    const [summary, setSummary] = useState(null);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Filters
    const [severity, setSeverity] = useState("All");
    const [status, setStatus] = useState("All");
    const [page, setPage] = useState(1);
    const [totalAlerts, setTotalAlerts] = useState(0);

    const loadSummary = async () => {
        try {
            const res = await apiClient.get("/farmer/alerts/summary");
            setSummary(res.data);
        } catch (err) {
            console.error("Failed to load alerts summary", err);
        }
    };

    const loadAlerts = async () => {
        setLoading(true);
        try {
            const res = await apiClient.get("/farmer/alerts", {
                params: {
                    severity,
                    status,
                    page,
                    page_size: 20
                }
            });
            setAlerts(res.data.alerts);
            setTotalAlerts(res.data.total);
        } catch (err) {
            console.error("Failed to load alerts", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadSummary();
    }, []);

    useEffect(() => {
        loadAlerts();
    }, [severity, status, page]);

    const handleMarkAsRead = async (e, alertId) => {
        e.stopPropagation();
        try {
            await apiClient.put(`/farmer/alerts/${alertId}/read`);
            // Update local state
            setAlerts(alerts.map(a => a.id === alertId ? { ...a, status: "READ" } : a));
        } catch (err) {
            console.error("Failed to mark as read", err);
        }
    };

    const getSeverityStyles = (sev) => {
        switch(sev) {
            case "CRITICAL": return "bg-red-50 text-red-600 border-red-200";
            case "WARNING": return "bg-amber-50 text-amber-600 border-amber-200";
            case "INFO": return "bg-blue-50 text-blue-600 border-blue-200";
            default: return "bg-slate-50 text-slate-600 border-slate-200";
        }
    };

    return (
        <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
                        <Bell className="w-8 h-8 text-brand" /> Alerts Center
                    </h1>
                    <p className="text-slate-500 mt-2 max-w-2xl">
                        Stay informed with real-time notifications and actionable insights from your TERRAVYN ecosystem.
                    </p>
                </div>
                <button 
                    onClick={() => {
                        apiClient.get('/farmer/alerts/check-offline').then(() => {
                            loadSummary();
                            loadAlerts();
                        });
                    }}
                    className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 flex items-center gap-2"
                >
                    <Activity className="w-4 h-4" /> Run Connectivity Check
                </button>
            </div>

            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-sm font-medium text-slate-500">Active Alerts</p>
                                <p className="text-2xl font-bold text-slate-900 mt-1">{summary.total_active}</p>
                            </div>
                            <div className="p-2 bg-blue-50 rounded-lg"><Bell className="w-5 h-5 text-blue-600" /></div>
                        </div>
                    </motion.div>
                    
                    <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} transition={{delay:0.1}} className="bg-white p-5 rounded-xl border border-red-200 shadow-sm">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-sm font-medium text-red-600">Critical Status</p>
                                <p className="text-2xl font-bold text-red-700 mt-1">{summary.total_critical}</p>
                            </div>
                            <div className="p-2 bg-red-100 rounded-lg"><AlertTriangle className="w-5 h-5 text-red-600" /></div>
                        </div>
                    </motion.div>

                    <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} transition={{delay:0.2}} className="bg-white p-5 rounded-xl border border-amber-200 shadow-sm">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-sm font-medium text-amber-600">Warnings</p>
                                <p className="text-2xl font-bold text-amber-700 mt-1">{summary.total_warning}</p>
                            </div>
                            <div className="p-2 bg-amber-100 rounded-lg"><AlertTriangle className="w-5 h-5 text-amber-600" /></div>
                        </div>
                    </motion.div>

                    <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} transition={{delay:0.3}} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-sm font-medium text-slate-500">Resolved (30d)</p>
                                <p className="text-2xl font-bold text-emerald-600 mt-1">{summary.total_resolved}</p>
                            </div>
                            <div className="p-2 bg-emerald-50 rounded-lg"><CheckCircle className="w-5 h-5 text-emerald-600" /></div>
                        </div>
                    </motion.div>
                </div>
            )}

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-wrap gap-4 items-center shadow-sm">
                <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-slate-400" />
                    <span className="text-sm font-medium text-slate-700">Filters:</span>
                </div>
                
                <select 
                    value={severity} 
                    onChange={e => {setSeverity(e.target.value); setPage(1);}}
                    className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:ring-2 focus:ring-brand"
                >
                    <option value="All">All Severities</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="WARNING">Warning</option>
                    <option value="INFO">Info</option>
                </select>

                <select 
                    value={status} 
                    onChange={e => {setStatus(e.target.value); setPage(1);}}
                    className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:ring-2 focus:ring-brand"
                >
                    <option value="All">All Statuses</option>
                    <option value="UNREAD">Unread</option>
                    <option value="READ">Read</option>
                    <option value="RESOLVED">Resolved</option>
                </select>
            </div>

            {/* Alerts List */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-slate-500">Loading alerts...</div>
                ) : alerts.length === 0 ? (
                    <div className="p-12 text-center flex flex-col items-center">
                        <CheckCircle className="w-12 h-12 text-emerald-500 mb-3" />
                        <h3 className="text-lg font-medium text-slate-900">All Clear</h3>
                        <p className="text-slate-500">No alerts found for the selected filters.</p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-100">
                        <AnimatePresence>
                            {alerts.map((alert) => (
                                <motion.div 
                                    initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}
                                    key={alert.id}
                                    onClick={() => navigate(`/farmer/alerts/${alert.id}`)}
                                    className={`p-5 hover:bg-slate-50 transition-colors cursor-pointer flex items-start gap-4 ${alert.status === 'UNREAD' ? 'bg-slate-50/50' : ''}`}
                                >
                                    <div className={`p-2 rounded-full border ${getSeverityStyles(alert.severity)}`}>
                                        {alert.severity === 'CRITICAL' ? <AlertTriangle className="w-5 h-5" /> :
                                         alert.severity === 'WARNING' ? <AlertTriangle className="w-5 h-5" /> :
                                         <Bell className="w-5 h-5" />}
                                    </div>
                                    
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-4">
                                            <div>
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h3 className={`text-base font-semibold ${alert.status === 'UNREAD' ? 'text-slate-900' : 'text-slate-700'}`}>
                                                        {alert.title}
                                                    </h3>
                                                    {alert.status === 'UNREAD' && (
                                                        <span className="w-2 h-2 rounded-full bg-brand"></span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-slate-600 line-clamp-1">{alert.description}</p>
                                            </div>
                                            <div className="flex flex-col items-end gap-2 flex-shrink-0">
                                                <div className="flex items-center gap-1 text-xs text-slate-500">
                                                    <Clock className="w-3 h-3" />
                                                    {dayjs(alert.created_at).fromNow()}
                                                </div>
                                                {alert.status === 'UNREAD' ? (
                                                    <button 
                                                        onClick={(e) => handleMarkAsRead(e, alert.id)}
                                                        className="text-xs font-medium text-brand hover:text-brand-dark flex items-center gap-1"
                                                    >
                                                        <Check className="w-3 h-3" /> Mark as read
                                                    </button>
                                                ) : alert.status === 'RESOLVED' ? (
                                                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-md text-xs font-medium border border-emerald-200">
                                                        Resolved
                                                    </span>
                                                ) : (
                                                    <span className="text-xs text-slate-400">Read</span>
                                                )}
                                            </div>
                                        </div>
                                        
                                        <div className="mt-3 flex items-center gap-4 text-xs">
                                            <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-100 text-slate-600 rounded-md">
                                                <Server className="w-3.5 h-3.5" />
                                                <span className="font-medium truncate max-w-[150px]">
                                                    {alert.device_name || alert.device_uid || 'Unknown Device'}
                                                </span>
                                            </div>
                                            {alert.farm_name && (
                                                <div className="flex items-center gap-1 text-slate-500">
                                                    <span className="w-1 h-1 rounded-full bg-slate-300"></span>
                                                    <span>Farm: {alert.farm_name}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    
                                    <div className="self-center pl-4 text-slate-300">
                                        <ChevronRight className="w-5 h-5" />
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                )}
                
                {/* Pagination (Simple) */}
                {totalAlerts > 20 && (
                    <div className="p-4 border-t border-slate-200 flex justify-between items-center bg-slate-50">
                        <button 
                            disabled={page === 1}
                            onClick={() => setPage(p => p - 1)}
                            className="px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <span className="text-sm text-slate-500">
                            Page {page} of {Math.ceil(totalAlerts / 20)}
                        </span>
                        <button 
                            disabled={page >= Math.ceil(totalAlerts / 20)}
                            onClick={() => setPage(p => p + 1)}
                            className="px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
