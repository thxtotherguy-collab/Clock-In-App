# Workforce Management System - Architecture Foundation
## Phase 1: System Architecture Planning

---

## 1. HIGH-LEVEL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   PWA Mobile    │  │   Web Admin     │  │  Branch Manager │             │
│  │   (Workers)     │  │   Dashboard     │  │    Portal       │             │
│  │   React + SW    │  │   React SPA     │  │   React SPA     │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                            │
│                    ┌───────────▼───────────┐                                │
│                    │   Service Worker      │                                │
│                    │   (Offline Queue)     │                                │
│                    └───────────┬───────────┘                                │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                           API GATEWAY                                        │
├────────────────────────────────┼────────────────────────────────────────────┤
│                    ┌───────────▼───────────┐                                │
│                    │   FastAPI Gateway     │                                │
│                    │   - Rate Limiting     │                                │
│                    │   - JWT Validation    │                                │
│                    │   - Request Routing   │                                │
│                    └───────────┬───────────┘                                │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                         SERVICE LAYER                                        │
├────────────────────────────────┼────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  Auth   │ │Attendance│ │   GPS   │ │ Payroll │ │ Report  │ │ Branch  │   │
│  │ Service │ │ Service  │ │ Tracker │ │ Export  │ │ Service │ │ Service │   │
│  └────┬────┘ └────┬─────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       │          │            │           │           │           │         │
│       └──────────┴────────────┴───────────┴───────────┴───────────┘         │
│                                │                                            │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                          DATA LAYER                                          │
├────────────────────────────────┼────────────────────────────────────────────┤
│                    ┌───────────▼───────────┐                                │
│                    │      MongoDB          │                                │
│                    │   (Document Store)    │                                │
│                    │                       │                                │
│                    │ Collections:          │                                │
│                    │ - users               │                                │
│                    │ - branches            │                                │
│                    │ - attendance_records  │                                │
│                    │ - gps_logs            │                                │
│                    │ - shifts              │                                │
│                    │ - offline_sync_queue  │                                │
│                    └───────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. MULTI-ROLE STRUCTURE OVERVIEW

### Role Hierarchy
```
┌─────────────────────────────────────────┐
│           SUPER_ADMIN                   │  ← Full system access
│    (System-wide configuration)          │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│           COMPANY_ADMIN                 │  ← Company-level access
│    (All branches, all workers)          │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│         BRANCH_MANAGER                  │  ← Branch-specific access
│    (Single branch, assigned workers)    │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│           SUPERVISOR                    │  ← Team-level access
│    (Team within branch)                 │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│             WORKER                      │  ← Self-service only
│    (Own attendance, own data)           │
└─────────────────────────────────────────┘
```

### Permission Matrix

| Feature              | Super Admin | Company Admin | Branch Manager | Supervisor | Worker |
|---------------------|-------------|---------------|----------------|------------|--------|
| System Config       | ✓           | ✗             | ✗              | ✗          | ✗      |
| All Branches View   | ✓           | ✓             | ✗              | ✗          | ✗      |
| Branch Management   | ✓           | ✓             | Own Branch     | ✗          | ✗      |
| Worker Management   | ✓           | ✓             | Own Branch     | Own Team   | ✗      |
| Attendance Override | ✓           | ✓             | ✓              | ✓          | ✗      |
| Reports - All       | ✓           | ✓             | ✗              | ✗          | ✗      |
| Reports - Branch    | ✓           | ✓             | ✓              | ✗          | ✗      |
| Reports - Team      | ✓           | ✓             | ✓              | ✓          | ✗      |
| Payroll Export      | ✓           | ✓             | ✓              | ✗          | ✗      |
| Own Attendance      | ✓           | ✓             | ✓              | ✓          | ✓      |
| GPS Tracking View   | ✓           | ✓             | Own Branch     | Own Team   | Self   |

---

## 3. SCALABLE BACKEND DESIGN APPROACH

### Modular Service Architecture
```
/app/backend/
│
├── core/                      # Core shared utilities
│   ├── __init__.py
│   ├── config.py              # Environment & settings
│   ├── database.py            # MongoDB connection pool
│   ├── security.py            # JWT, password hashing
│   └── exceptions.py          # Custom exceptions
│
├── models/                    # Pydantic models & schemas
│   ├── __init__.py
│   ├── user.py
│   ├── branch.py
│   ├── attendance.py
│   ├── gps.py
│   └── payroll.py
│
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   ├── branch_service.py
│   ├── attendance_service.py
│   ├── gps_service.py
│   ├── report_service.py
│   └── export_service.py
│
├── routers/                   # API endpoints
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   ├── branches.py
│   ├── attendance.py
│   ├── gps.py
│   ├── reports.py
│   └── exports.py
│
├── middleware/                # Request processing
│   ├── __init__.py
│   ├── auth_middleware.py
│   ├── rate_limiter.py
│   └── branch_context.py
│
└── server.py                  # Application entry point
```

### Key Design Patterns

1. **Repository Pattern**: Data access abstraction
2. **Service Layer**: Business logic separation
3. **Dependency Injection**: FastAPI's `Depends()` for clean testing
4. **Branch Context Middleware**: Auto-inject branch scope per request

---

## 4. MULTI-BRANCH STRUCTURE LOGIC

### Branch Data Model
```python
Branch = {
    "id": "uuid",
    "name": "Branch Name",
    "code": "BR001",              # Unique identifier
    "address": {...},
    "geofence": {
        "latitude": 0.0,
        "longitude": 0.0,
        "radius_meters": 100      # For GPS validation
    },
    "timezone": "Asia/Kolkata",
    "settings": {
        "shift_start_tolerance_mins": 15,
        "shift_end_tolerance_mins": 15,
        "require_gps_for_punch": true,
        "allow_offline_punch": true
    },
    "managers": ["user_id_1"],
    "status": "active",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime"
}
```

### Branch-Scoped Query Pattern
```python
# All queries automatically filtered by branch
async def get_workers(branch_id: str, role_context: RoleContext):
    if role_context.role == "COMPANY_ADMIN":
        # Can access all branches
        filter = {} if not branch_id else {"branch_id": branch_id}
    elif role_context.role == "BRANCH_MANAGER":
        # Restricted to own branch
        filter = {"branch_id": role_context.branch_id}
    else:
        raise ForbiddenException()
    
    return await db.users.find(filter).to_list()
```

---

## 5. DATA SEPARATION MODEL

### Collection Schema Design

```
MongoDB Collections
├── users                     # All user types
│   ├── Indexes: email (unique), branch_id, role
│   └── Compound: {branch_id, status}
│
├── branches                  # Branch configuration
│   ├── Indexes: code (unique)
│   └── Geospatial: geofence.location (2dsphere)
│
├── attendance_records        # Punch in/out records
│   ├── Indexes: user_id, branch_id, date
│   └── Compound: {branch_id, date, status}
│
├── gps_logs                  # Real-time GPS tracking
│   ├── Indexes: user_id, timestamp
│   ├── Compound: {user_id, shift_id}
│   └── TTL Index: expires after 90 days
│
├── shifts                    # Shift definitions
│   ├── Indexes: branch_id
│   └── Compound: {branch_id, day_of_week}
│
├── schedules                 # Worker assignments
│   ├── Indexes: user_id, week_start
│   └── Compound: {branch_id, week_start}
│
└── offline_sync_queue        # Pending offline actions
    ├── Indexes: user_id, synced
    └── TTL: Auto-delete after sync
```

### Data Isolation Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layers                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Level 1: System-wide (Super Admin only)                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  All collections, no branch filter                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Level 2: Company-wide (Company Admin)                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  All branches within company                         │    │
│  │  Filter: company_id (future multi-tenant)            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Level 3: Branch-scoped (Branch Manager, Supervisor)        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Filter: branch_id = assigned_branch                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Level 4: Self-only (Worker)                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Filter: user_id = current_user                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. CORE MODULES LIST

### Phase 1 - MVP Modules

| Module | Priority | Description |
|--------|----------|-------------|
| **Auth Module** | P0 | JWT auth, role-based access, password management |
| **User Management** | P0 | CRUD users, role assignment, branch assignment |
| **Branch Management** | P0 | CRUD branches, geofence config, settings |
| **Attendance Core** | P0 | Punch in/out, shift assignment, manual override |
| **GPS Tracking** | P0 | Real-time location capture, continuous tracking during shift |
| **Basic Reports** | P1 | Attendance summary, late arrivals, overtime |
| **Payroll Export** | P1 | CSV/Excel export with configurable fields |

### Phase 2 - Extended Modules

| Module | Priority | Description |
|--------|----------|-------------|
| **Leave Management** | P2 | Leave requests, approvals, balance tracking |
| **Task Management** | P2 | Task assignment, completion tracking |
| **Notifications** | P2 | Push notifications, email alerts |
| **Advanced Reports** | P2 | Custom report builder, scheduled reports |

### Phase 3 - Future Modules

| Module | Priority | Description |
|--------|----------|-------------|
| **Vehicle Tracking** | P3 | Fleet management integration |
| **Payroll Integration** | P3 | Direct integration with payroll systems |
| **Biometric Integration** | P3 | Fingerprint/face recognition |
| **Multi-tenant** | P3 | Multiple companies on single instance |

---

## 7. FOLDER/PROJECT STRUCTURE

### Complete Project Structure
```
/app/
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings from env
│   │   ├── database.py         # MongoDB async client
│   │   ├── security.py         # JWT + bcrypt
│   │   └── exceptions.py       # HTTPException subclasses
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseModel with common fields
│   │   ├── user.py             # User schemas
│   │   ├── branch.py           # Branch schemas
│   │   ├── attendance.py       # Attendance schemas
│   │   ├── gps.py              # GPS log schemas
│   │   ├── shift.py            # Shift definition schemas
│   │   └── export.py           # Export config schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── branch_service.py
│   │   ├── attendance_service.py
│   │   ├── gps_service.py
│   │   ├── report_service.py
│   │   └── export_service.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # /api/auth/*
│   │   ├── users.py            # /api/users/*
│   │   ├── branches.py         # /api/branches/*
│   │   ├── attendance.py       # /api/attendance/*
│   │   ├── gps.py              # /api/gps/*
│   │   ├── reports.py          # /api/reports/*
│   │   └── exports.py          # /api/exports/*
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth_middleware.py  # JWT validation
│   │   └── branch_context.py   # Branch scope injection
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py       # Custom validators
│   │   ├── formatters.py       # Date/time formatting
│   │   └── geo.py              # Geospatial calculations
│   │
│   ├── server.py               # FastAPI app
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   ├── manifest.json       # PWA manifest
│   │   └── service-worker.js   # Offline support
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/             # Shadcn components
│   │   │   ├── layout/
│   │   │   │   ├── AdminLayout.jsx
│   │   │   │   ├── WorkerLayout.jsx
│   │   │   │   └── Sidebar.jsx
│   │   │   ├── attendance/
│   │   │   │   ├── PunchButton.jsx
│   │   │   │   ├── AttendanceList.jsx
│   │   │   │   └── AttendanceCalendar.jsx
│   │   │   ├── gps/
│   │   │   │   ├── LocationTracker.jsx
│   │   │   │   └── GPSMap.jsx
│   │   │   └── common/
│   │   │       ├── DataTable.jsx
│   │   │       └── ExportButton.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   │   ├── Login.jsx
│   │   │   │   └── ForgotPassword.jsx
│   │   │   ├── admin/
│   │   │   │   ├── Dashboard.jsx
│   │   │   │   ├── Workers.jsx
│   │   │   │   ├── Branches.jsx
│   │   │   │   ├── Reports.jsx
│   │   │   │   └── Settings.jsx
│   │   │   ├── manager/
│   │   │   │   ├── BranchDashboard.jsx
│   │   │   │   ├── TeamAttendance.jsx
│   │   │   │   └── Approvals.jsx
│   │   │   └── worker/
│   │   │       ├── Home.jsx
│   │   │       ├── MyAttendance.jsx
│   │   │       └── MySchedule.jsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.js
│   │   │   ├── useGPS.js
│   │   │   ├── useOfflineSync.js
│   │   │   └── useBranchContext.js
│   │   │
│   │   ├── services/
│   │   │   ├── api.js          # Axios instance
│   │   │   ├── auth.js
│   │   │   ├── attendance.js
│   │   │   ├── gps.js
│   │   │   └── offline.js      # IndexedDB operations
│   │   │
│   │   ├── store/
│   │   │   ├── authStore.js
│   │   │   ├── attendanceStore.js
│   │   │   └── offlineStore.js
│   │   │
│   │   ├── utils/
│   │   │   ├── constants.js
│   │   │   ├── permissions.js
│   │   │   └── formatters.js
│   │   │
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   │
│   ├── package.json
│   ├── tailwind.config.js
│   └── .env
│
├── docs/
│   └── architecture/
│       └── SYSTEM_ARCHITECTURE.md
│
├── tests/
│   ├── backend/
│   │   ├── test_auth.py
│   │   ├── test_attendance.py
│   │   └── test_gps.py
│   └── frontend/
│       └── e2e/
│
└── memory/
    └── PRD.md
```

---

## 8. FUTURE SCALABILITY PREPARATION

### Horizontal Scaling Path
```
Current (Phase 1)              Future (Phase 3+)
┌─────────────────┐           ┌─────────────────────────────┐
│  Single Server  │    →      │    Load Balancer            │
│  FastAPI        │           │         │                   │
│  MongoDB        │           │    ┌────┴────┐              │
└─────────────────┘           │    ▼         ▼              │
                              │  Server 1  Server 2         │
                              │    │         │              │
                              │    └────┬────┘              │
                              │         ▼                   │
                              │  MongoDB Replica Set        │
                              └─────────────────────────────┘
```

### Extension Points Built-In

1. **Leave Management** (Ready)
   - User model includes `leave_balance` field (empty by default)
   - Attendance model supports `type: "leave"` records
   - Permission matrix already includes leave approval

2. **Task Management** (Ready)
   - Branch structure supports team hierarchy
   - User assignments can extend to tasks
   - Notification hooks in place

3. **Vehicle Tracking** (Ready)
   - GPS logs structure supports `entity_type: "user" | "vehicle"`
   - Geofence logic reusable for vehicle boundaries
   - Real-time tracking infrastructure shared

4. **External Integrations** (Ready)
   - Export service designed as plugin architecture
   - Webhook support for payroll callbacks
   - API versioning from day 1

### Database Indexes Strategy
```javascript
// Attendance - optimized for daily queries
db.attendance_records.createIndex({ branch_id: 1, date: 1, user_id: 1 })

// GPS - optimized for real-time + historical
db.gps_logs.createIndex({ user_id: 1, timestamp: -1 })
db.gps_logs.createIndex({ shift_id: 1 })

// Users - optimized for branch filtering
db.users.createIndex({ branch_id: 1, role: 1, status: 1 })

// TTL for GPS logs (90 days retention)
db.gps_logs.createIndex({ timestamp: 1 }, { expireAfterSeconds: 7776000 })
```

### PWA Offline Strategy

```javascript
// Service Worker Cache Strategy
const CACHE_STRATEGIES = {
  // Static assets - Cache First
  static: ['/', '/manifest.json', '/static/*'],
  
  // API calls - Network First, fallback to cache
  api: ['/api/schedules/*', '/api/users/me'],
  
  // Attendance punch - Background Sync
  offline_queue: ['/api/attendance/punch'],
  
  // GPS - Store locally, batch upload
  gps_buffer: ['/api/gps/log']
};

// IndexedDB Schema for Offline
const OFFLINE_STORES = {
  pending_punches: { keyPath: 'local_id', indexes: ['timestamp'] },
  gps_buffer: { keyPath: 'local_id', indexes: ['timestamp'] },
  cached_schedule: { keyPath: 'week_start' }
};
```

---

## API ENDPOINTS OVERVIEW

### Authentication
```
POST   /api/auth/login          # JWT login
POST   /api/auth/refresh        # Token refresh
POST   /api/auth/logout         # Invalidate token
POST   /api/auth/password/reset # Password reset
```

### Users
```
GET    /api/users               # List (branch-scoped)
POST   /api/users               # Create worker
GET    /api/users/{id}          # Get user
PUT    /api/users/{id}          # Update user
DELETE /api/users/{id}          # Deactivate user
GET    /api/users/me            # Current user profile
```

### Branches
```
GET    /api/branches            # List branches
POST   /api/branches            # Create branch
GET    /api/branches/{id}       # Get branch
PUT    /api/branches/{id}       # Update branch
GET    /api/branches/{id}/workers  # Workers in branch
```

### Attendance
```
POST   /api/attendance/punch    # Punch in/out
GET    /api/attendance/today    # Today's status
GET    /api/attendance/history  # Historical records
PUT    /api/attendance/{id}     # Manual override
POST   /api/attendance/sync     # Offline sync
```

### GPS
```
POST   /api/gps/log             # Log single position
POST   /api/gps/batch           # Batch upload
GET    /api/gps/track/{user_id} # Live tracking
GET    /api/gps/history         # Historical path
```

### Reports
```
GET    /api/reports/attendance  # Attendance summary
GET    /api/reports/overtime    # Overtime report
GET    /api/reports/late        # Late arrivals
GET    /api/reports/branch      # Branch performance
```

### Exports
```
POST   /api/exports/payroll     # Generate payroll export
GET    /api/exports/{id}        # Download export
GET    /api/exports/templates   # Export templates
```

---

## NEXT STEPS

**Phase 1 Implementation Order:**
1. Core infrastructure (database, auth)
2. User & branch management
3. Basic attendance (punch in/out)
4. GPS tracking integration
5. PWA setup with offline support
6. Reports & export

**Ready for Phase 2:** Proceed when ready to implement.
