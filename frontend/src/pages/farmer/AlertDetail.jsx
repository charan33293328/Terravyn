import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
    AlertTriangle, Bell, ArrowLeft, Server, Activity, Clock, CheckCircle, UserCircle, MapPin
} from "lucide-react";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import apiClient from "../../api/client";

dayjs.extend(relativeTime);

export default function AlertDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [alert, setAlert] = useState(null);
    const [loading, setLoading] = useState(true);
    const [resolving, setResolving] = useState(false);
    const [resolutionNotes, setResolutionNotes] = useState("");

    useEffect(() => {
        const loadAlert = async () => {
            try {
                const res = await apiClient.get(`/farmer/alerts/${id}`);
                setAlert(res.data);
                if (res.data.status === "UNREAD") {
                    await apiClient.put(`/farmer/alerts/${id}/read`);
                }
            } catch (err) {
                console.error("Failed to load alert details", err);
            } finally {
                setLoading(false);
            }
        };
        loadAlert();
    }, [id]);

    const handleResolve = async () => {
        if (!resolutionNotes.trim()) {
            alert("Please provide resolution notes before resolving.");
            return;
        }
        setResolving(true);
        try {
            await apiClient.put(`/farmer/alerts/${id}/resolve`, {
                resolution_notes: resolutionNotes
            });
            const res = await apiClient.get(`/farmer/alerts/${id}`);
            setAlert(res.data);
        } catch (err) {
            console.error("Failed to resolve alert", err);
        } finally {
            setResolving(false);
        }
    };

    if (loading) return <div className="p-8 text-center text-slate-500">Loading alert details...</div>;
    if (!alert) return <div className="p-8 text-center text-red-500">Alert not found.</div>;

    const getSeverityStyles = (sev) => {
        switch(sev) {
            case "CRITICAL": return "bg-red-50 text-red-600 border-red-200";
            case "WARNING": return "bg-amber-50 text-amber-600 border-amber-200";
            case "INFO": return "bg-blue-50 text-blue-600 border-blue-200";
            default: return "bg-slate-50 text-slate-600 border-slate-200";
        }
    };

    const triggerData = alert.trigger_data ? JSON.parse(alert.trigger_data) : {};

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <button 
                onClick={() => navigate('/farmer/alerts')}
                className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors mb-6"
            >
                <ArrowLeft className="w-4 h-4" /> Back to Alerts Center
            </button>

            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                {/* Alert Title Banner */}
                <div className={`p-6 border-b flex items-start gap-4 ${getSeverityStyles(alert.severity)}`}>
                    <div className="p-3 bg-white/60 rounded-full shrink-0">
                        {alert.severity === 'CRITICAL' ? <AlertTriangle className="w-8 h-8" /> :
                         alert.severity === 'WARNING' ? <AlertTriangle className="w-8 h-8" /> :
                         <Bell className="w-8 h-8" />}
                    </div>
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <span className="px-2.5 py-1 bg-white/80 rounded-md text-xs font-bold tracking-wide uppercase shadow-sm">
                                {alert.severity}
                            </span>
                            <span className="text-sm font-medium opacity-80">{alert.category}</span>
                        </div>
                        <h1 className="text-2xl font-bold">{alert.title}</h1>
                        <p className="mt-2 text-lg opacity-90">{alert.description}</p>
                    </div>
                </div>

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Details Column */}
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 border-b pb-2">
                                Alert Information
                            </h3>
                            <dl className="space-y-3">
                                <div className="flex justify-between">
                                    <dt className="text-sm text-slate-500 flex items-center gap-2"><Clock className="w-4 h-4" /> Generated At</dt>
                                    <dd className="text-sm font-medium text-slate-900">{dayjs(alert.created_at).format('MMM D, YYYY h:mm A')}</dd>
                                </div>
                                <div className="flex justify-between">
                                    <dt className="text-sm text-slate-500 flex items-center gap-2"><Activity className="w-4 h-4" /> Status</dt>
                                    <dd className="text-sm font-medium text-slate-900">
                                        {alert.status === "RESOLVED" ? (
                                            <span className="text-emerald-600 flex items-center gap-1"><CheckCircle className="w-4 h-4" /> Resolved</span>
                                        ) : alert.status}
                                    </dd>
                                </div>
                                {Object.keys(triggerData).length > 0 && (
                                    <div className="pt-2">
                                        <dt className="text-sm text-slate-500 mb-2">Trigger Conditions</dt>
                                        <dd className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                                            {Object.entries(triggerData).map(([key, value]) => (
                                                <div key={key} className="flex justify-between text-sm">
                                                    <span className="text-slate-600">{key}:</span>
                                                    <span className="font-mono font-medium text-slate-900">{value}</span>
                                                </div>
                                            ))}
                                        </dd>
                                    </div>
                                )}
                            </dl>
                        </div>

                        <div>
                            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 border-b pb-2">
                                Source Information
                            </h3>
                            <dl className="space-y-3">
                                <div className="flex justify-between">
                                    <dt className="text-sm text-slate-500 flex items-center gap-2"><Server className="w-4 h-4" /> Device</dt>
                                    <dd className="text-sm font-medium text-slate-900">{alert.device_name || alert.device_uid || 'N/A'}</dd>
                                </div>
                                <div className="flex justify-between">
                                    <dt className="text-sm text-slate-500 flex items-center gap-2"><MapPin className="w-4 h-4" /> Farm</dt>
                                    <dd className="text-sm font-medium text-slate-900">{alert.farm_name || 'Unassigned'}</dd>
                                </div>
                            </dl>
                        </div>
                    </div>

                    {/* Resolution Column */}
                    <div>
                        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 border-b pb-2">
                            Resolution Action
                        </h3>
                        
                        {alert.status === "RESOLVED" ? (
                            <div className="bg-emerald-50 rounded-xl p-5 border border-emerald-200">
                                <div className="flex items-start gap-3 mb-4">
                                    <CheckCircle className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
                                    <div>
                                        <h4 className="font-semibold text-emerald-900">Alert Resolved</h4>
                                        <p className="text-sm text-emerald-700 mt-1">
                                            Resolved on {dayjs(alert.resolved_at).format('MMM D, YYYY h:mm A')}
                                        </p>
                                    </div>
                                </div>
                                
                                <div className="bg-white rounded-lg p-4 border border-emerald-100 mb-3">
                                    <h5 className="text-xs font-semibold uppercase text-emerald-800 mb-1">Resolution Notes</h5>
                                    <p className="text-sm text-slate-700">{alert.resolution_notes}</p>
                                </div>
                                
                                <div className="flex items-center gap-2 text-sm text-emerald-800">
                                    <UserCircle className="w-4 h-4" />
                                    <span>Resolved by: <span className="font-medium">{alert.resolved_by || 'Unknown User'}</span></span>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-slate-50 rounded-xl p-5 border border-slate-200">
                                <p className="text-sm text-slate-600 mb-4">
                                    Please investigate the issue. Once the problem is fixed or the alert is verified as a false positive, you can resolve it here.
                                </p>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">
                                            Resolution Notes <span className="text-red-500">*</span>
                                        </label>
                                        <textarea
                                            value={resolutionNotes}
                                            onChange={(e) => setResolutionNotes(e.target.value)}
                                            placeholder="Explain what was done to fix this issue..."
                                            className="w-full p-3 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-brand focus:border-brand h-24"
                                            required
                                        ></textarea>
                                    </div>
                                    <button
                                        onClick={handleResolve}
                                        disabled={resolving || !resolutionNotes.trim()}
                                        className="w-full py-2.5 bg-brand text-white font-medium rounded-lg hover:bg-brand-dark transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
                                    >
                                        {resolving ? "Resolving..." : (
                                            <><CheckCircle className="w-5 h-5" /> Mark as Resolved</>
                                        )}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
