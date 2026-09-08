import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.connection import engine, Base, SessionLocal
from models import domain
from routes import (
    auth, admin, user_devices, provision, devices, devices_api, sensors, control, 
    analytics, alerts, orders, invoices, user_orders, admin_devices, admin_farmers,
    admin_orders, admin_notifications, admin_dashboard, admin_customers, support,
    admin_support, admin_analytics, admin_cms, admin_settings, admin_rbac, admin_system,
    public_cms, admin_products, public_products, uploads, farmer_devices, farmer_dashboard, farmer_farms, farmer_monitoring, farmer_alerts, farmer_orders, farmer_support, farmer_profile,
    farmer_weather, farmer_decision, research_knowledge, experiment_routes, validation_routes,
    irrigation_intelligence_routes, learning_routes
)
from services.websocket import manager

# Ensure static directories exist
import os
os.makedirs("static/media", exist_ok=True)

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TERRAVYN Smart Agriculture API")

@app.on_event("startup")
async def startup_event():
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.info("Application Startup: Logging registered routes...")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            logger.info(f"{route.methods} {route.path}")
    logger.info("Application Startup: Validating environment variables...")

import logging
logger = logging.getLogger("uvicorn.error")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    ESP32_EXEMPT_ROUTES = [
        "/api/devices",
        "/devices",
        "/api/device",
        "/device",
        "/api/sensors",
        "/sensors",
        "/telemetry",
        "/data",
        "/heartbeat",
        "/config",
    ]
    
    path = request.url.path
    import re
    logger.info(f"Middleware Path: {path}")

    if any(path.startswith(route) for route in ESP32_EXEMPT_ROUTES) or re.search(r"/mode$", path):
        logger.info(f"ESP32 route bypassed: {path}")
        return await call_next(request)

    logger.info(f"Auth check applied: {path}")
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://terravyn.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    if (request.url.path.startswith('/api/admin') 
            or request.url.path.startswith('/static') 
            or request.url.path.startswith('/api/auth')
            or request.url.path.startswith('/api/uploads')
            or request.url.path.startswith('/api/public')):
        return await call_next(request)
        
    db = SessionLocal()
    try:
        from models.domain import MaintenanceSchedule
        schedule = db.query(MaintenanceSchedule).first()
        if schedule and schedule.is_active:
            now = datetime.utcnow()
            if schedule.start_time and now < schedule.start_time:
                return await call_next(request)
            if schedule.end_time and now > schedule.end_time:
                return await call_next(request)
                
            return JSONResponse(
                status_code=503,
                content={'detail': schedule.message or 'System is under maintenance. Please try again later.'}
            )
    finally:
        db.close()
        
    return await call_next(request)

# Include Routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user_devices.router)
app.include_router(farmer_devices.router)
app.include_router(farmer_farms.router)
app.include_router(farmer_weather.router)
app.include_router(farmer_decision.router)
app.include_router(research_knowledge.router)
app.include_router(experiment_routes.router)
app.include_router(validation_routes.router)
app.include_router(irrigation_intelligence_routes.router)
app.include_router(learning_routes.router)
app.include_router(learning_routes.outcomes_router)
app.include_router(learning_routes.perf_router)
app.include_router(provision.router)
app.include_router(devices.router)
app.include_router(devices_api.router)
app.include_router(devices_api.compat_router)
app.include_router(sensors.router) # includes websocket
app.include_router(control.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(orders.router)
app.include_router(invoices.router)
app.include_router(user_orders.router)
app.include_router(admin_devices.router)
app.include_router(admin_farmers.router)
app.include_router(admin_orders.router)
app.include_router(admin_notifications.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_customers.router)
app.include_router(support.router)
app.include_router(admin_support.router)
app.include_router(admin_analytics.router)
app.include_router(admin_products.router)
app.include_router(public_products.router)
app.include_router(admin_cms.router)
app.include_router(public_cms.router)
app.include_router(admin_settings.router, prefix="/api/admin/settings", tags=["Admin Settings"])
app.include_router(admin_rbac.router, prefix="/api/admin", tags=["Admin RBAC"])
app.include_router(admin_system.router, prefix="/api/admin", tags=["Admin System"])
app.include_router(uploads.router)
app.include_router(farmer_dashboard.router)
app.include_router(farmer_monitoring.router)
app.include_router(farmer_alerts.router)
app.include_router(farmer_orders.router, prefix="/api/farmer/orders", tags=["Farmer Orders"])
app.include_router(farmer_support.router, tags=["Farmer Support"])
app.include_router(farmer_profile.router, prefix="/api/farmer", tags=["Farmer Profile"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Background Tasks ---
@app.on_event("startup")
async def startup_event():
    import logging
    from database.connection import settings
    logger = logging.getLogger("uvicorn.error")

    logger.info("Application Startup: Validating environment variables...")
    
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Startup Warning: Razorpay configuration is missing.")
        if not settings.RAZORPAY_KEY_ID:
            logger.error("Missing Environment Variable: RAZORPAY_KEY_ID")
        if not settings.RAZORPAY_KEY_SECRET:
            logger.error("Missing Environment Variable: RAZORPAY_KEY_SECRET")
        raise RuntimeError("Application startup halted: Razorpay configuration missing.")
    else:
        logger.info("Razorpay Key ID Loaded successfully.")

    asyncio.create_task(check_offline_devices())

async def check_offline_devices():
    while True:
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=60)
            devices_list = db.query(domain.Device).filter(
                domain.Device.status == "online",
                domain.Device.last_heartbeat < cutoff_time
            ).all()
            
            for d in devices_list:
                d.status = "offline"
                
                # Retrieve owner language preference
                owner_lang = "en"
                if d.owner:
                    owner_lang = d.owner.preferred_language or "en"
                
                translations = {
                    "en": "Device {name} ({uid}) has gone offline unexpectedly.",
                    "te": "పరికరం {name} ({uid}) ఊహించని విధంగా ఆఫ్‌లైన్‌కి వెళ్ళింది.",
                    "hi": "डिवाइस {name} ({uid}) अप्रत्याशित रूप से ऑफ़लाइन हो गया है।",
                    "ta": "சாதனம் {name} ({uid}) எதிர்பாராதவிதமாக ஆஃப்லைனில் சென்றுவிட்டது.",
                    "kn": "ಸಾಧನ {name} ({uid}) ಅನಿರೀಕ್ಷಿತವಾಗಿ ಆಫ್‌ಲೈನ್‌ಗೆ ಹೋಗಿದೆ.",
                    "mr": "डिव्हाइस {name} ({uid}) अनपेक्षितपणे ऑफलाइन गेले आहे."
                }
                
                alert_type_translations = {
                    "en": "Device Offline",
                    "te": "పరికరం ఆఫ్‌లైన్",
                    "hi": "डिवाइस ऑफ़लाइन",
                    "ta": "சாதனம் ஆஃப்லைன்",
                    "kn": "ಸಾಧನ ಆಫ್‌ಲೈನ್",
                    "mr": "डिव्हाइस ऑफलाइन"
                }

                msg_template = translations.get(owner_lang, translations["en"])
                msg = msg_template.format(name=d.name or "Unknown", uid=d.device_uid)
                
                # Also create an offline alert
                new_alert = domain.Alert(
                    device_id=d.id,
                    title=alert_type_translations.get(owner_lang, "Device Offline"),
                    description=msg,
                    category="System Alerts",
                    severity="CRITICAL"
                )
                db.add(new_alert)

                await manager.broadcast_to_device(d.id, {
                    "type": "status_update",
                    "status": "offline",
                    "device_id": d.id
                })
            
            if devices_list:
                db.commit()
        finally:
            db.close()
        await asyncio.sleep(5)

@app.get("/")
def read_root():
    return {"message": "TERRAVYN API is running - Production Architecture"}

import socket
import urllib.request

@app.get("/api/health/network-diagnostics")
def network_diagnostics():
    """Diagnostic check for outbound DNS, general HTTPS, and SMTP ports."""
    results = {}
    
    # 1. DNS check for smtp.gmail.com
    try:
        ips = socket.gethostbyname_ex("smtp.gmail.com")
        results["dns_resolution"] = {
            "status": "PASS",
            "host": "smtp.gmail.com",
            "resolved_ips_count": len(ips[2])
        }
    except Exception as e:
        results["dns_resolution"] = {
            "status": "FAIL",
            "host": "smtp.gmail.com",
            "error": str(e)
        }

    # 2. General Outbound HTTPS Internet Connectivity
    try:
        req = urllib.request.Request("https://www.google.com", headers={"User-Agent": "TERRAVYN/1.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            results["general_https_outbound"] = {
                "status": "PASS" if res.status == 200 else "FAIL",
                "http_status": res.status
            }
    except Exception as e:
        results["general_https_outbound"] = {"status": "FAIL", "error": str(e)}

    # 3. Test TCP 587, 465, 2525
    for port in [587, 465, 2525]:
        port_key = f"smtp_tcp_{port}"
        try:
            sock = socket.create_connection(("smtp.gmail.com", port), timeout=4)
            sock.close()
            results[port_key] = {"status": "PASS", "port": port}
        except OSError as e:
            results[port_key] = {
                "status": "FAIL",
                "port": port,
                "error_type": type(e).__name__,
                "error": str(e)
            }
        except Exception as e:
            results[port_key] = {
                "status": "FAIL",
                "port": port,
                "error_type": type(e).__name__,
                "error": str(e)
            }

    return results
