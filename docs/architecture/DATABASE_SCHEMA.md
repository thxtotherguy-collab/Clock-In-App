# Workforce Management System - Database Schema & RBAC
## Phase 2: Backend Structure

---

## 1. DATABASE SCHEMA (MongoDB Collections)

### 1.1 Users Collection
```javascript
{
  "id": "uuid",                          // Primary identifier
  "email": "worker@company.com",         // Unique, login credential
  "password_hash": "bcrypt_hash",        // Bcrypt hashed password
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "employee_id": "EMP001",               // Company employee ID
  "role": "WORKER",                      // SUPER_ADMIN | BRANCH_ADMIN | TEAM_LEADER | WORKER
  "status": "active",                    // active | inactive | suspended
  
  // Assignments
  "branch_id": "uuid",                   // Assigned branch
  "team_id": "uuid",                     // Assigned team (nullable)
  "job_site_ids": ["uuid"],              // Assigned job sites (can be multiple)
  
  // Profile
  "profile_photo_url": "https://...",
  "date_of_birth": "1990-01-15",
  "hire_date": "2024-01-01",
  "termination_date": null,
  
  // Work settings
  "hourly_rate_tier": "standard",        // Reference to rate configuration
  "overtime_eligible": true,
  "default_shift_id": "uuid",
  
  // Permissions override (optional granular control)
  "permission_overrides": {
    "can_approve_overtime": false,
    "can_export_reports": false
  },
  
  // Metadata
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "last_login_at": "2024-01-01T00:00:00Z"
}

// Indexes
- email: unique
- employee_id: unique
- { branch_id: 1, status: 1 }
- { team_id: 1 }
- { role: 1, status: 1 }
```

### 1.2 Roles Collection (Permission Definitions)
```javascript
{
  "id": "uuid",
  "name": "WORKER",                      // Role identifier
  "display_name": "Worker",
  "description": "Field worker with basic access",
  "level": 1,                            // Hierarchy level (higher = more access)
  
  "permissions": {
    // User management
    "users.view_self": true,
    "users.view_team": false,
    "users.view_branch": false,
    "users.view_all": false,
    "users.create": false,
    "users.update_self": true,
    "users.update_others": false,
    "users.delete": false,
    
    // Branch management
    "branches.view_assigned": true,
    "branches.view_all": false,
    "branches.create": false,
    "branches.update": false,
    "branches.delete": false,
    
    // Team management
    "teams.view_assigned": true,
    "teams.view_branch": false,
    "teams.view_all": false,
    "teams.create": false,
    "teams.update": false,
    
    // Time entries
    "time_entries.punch_self": true,
    "time_entries.view_self": true,
    "time_entries.view_team": false,
    "time_entries.view_branch": false,
    "time_entries.view_all": false,
    "time_entries.override": false,
    "time_entries.approve": false,
    
    // Reports
    "reports.view_self": true,
    "reports.view_team": false,
    "reports.view_branch": false,
    "reports.view_all": false,
    "reports.export": false,
    
    // Overtime
    "overtime.view_self": true,
    "overtime.view_team": false,
    "overtime.approve": false,
    
    // Audit logs
    "audit.view": false,
    
    // Settings
    "settings.view": false,
    "settings.update": false
  },
  
  "data_scope": "self",                  // self | team | branch | all
  
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 1.3 Branches Collection
```javascript
{
  "id": "uuid",
  "name": "Downtown Branch",
  "code": "BR-DT-001",                   // Unique branch code
  "status": "active",                    // active | inactive
  
  // Location
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  },
  
  // Geofence for GPS validation
  "geofence": {
    "center": {
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    "radius_meters": 150,                // Allowed punch radius
    "type": "circle"                     // circle | polygon (future)
  },
  
  // Timezone
  "timezone": "America/New_York",
  
  // Branch settings
  "settings": {
    "punch_tolerance_minutes": 15,       // Early/late punch tolerance
    "require_gps_for_punch": true,
    "require_photo_for_punch": false,
    "allow_offline_punch": true,
    "auto_clock_out_hours": 12,          // Auto clock-out after X hours
    "overtime_threshold_daily": 8,       // Hours before daily OT
    "overtime_threshold_weekly": 40      // Hours before weekly OT
  },
  
  // Assigned admins
  "admin_ids": ["uuid"],                 // Branch admins
  
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid"
}

// Indexes
- code: unique
- { "geofence.center": "2dsphere" }
- status: 1
```

### 1.4 Teams Collection
```javascript
{
  "id": "uuid",
  "name": "Alpha Team",
  "code": "TM-ALPHA",
  "branch_id": "uuid",                   // Parent branch
  "status": "active",
  
  // Leadership
  "leader_id": "uuid",                   // Team leader user
  "supervisor_ids": ["uuid"],            // Additional supervisors
  
  // Settings
  "settings": {
    "default_job_site_id": "uuid",
    "default_shift_id": "uuid"
  },
  
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid"
}

// Indexes
- code: unique
- { branch_id: 1, status: 1 }
- leader_id: 1
```

### 1.5 Job Sites Collection
```javascript
{
  "id": "uuid",
  "name": "Construction Site A",
  "code": "JS-CONST-A",
  "branch_id": "uuid",                   // Parent branch
  "status": "active",                    // active | inactive | completed
  
  // Location
  "address": {
    "street": "456 Project Ave",
    "city": "New York",
    "state": "NY",
    "postal_code": "10002",
    "country": "US"
  },
  
  // Geofence (if different from branch)
  "geofence": {
    "center": {
      "latitude": 40.7200,
      "longitude": -74.0100
    },
    "radius_meters": 200
  },
  
  // Project details
  "client_name": "ABC Construction",
  "project_code": "PRJ-2024-001",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  
  // Assigned teams
  "assigned_team_ids": ["uuid"],
  
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid"
}

// Indexes
- code: unique
- { branch_id: 1, status: 1 }
- { "geofence.center": "2dsphere" }
```

### 1.6 Time Entries Collection (Clock-in/out Records)
```javascript
{
  "id": "uuid",
  "user_id": "uuid",
  "branch_id": "uuid",
  "team_id": "uuid",
  "job_site_id": "uuid",
  
  // Date reference (for easy querying)
  "date": "2024-01-15",                  // YYYY-MM-DD local date
  
  // Clock in details
  "clock_in": {
    "timestamp": "2024-01-15T08:00:00Z",
    "local_time": "2024-01-15T08:00:00",
    "gps": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "accuracy_meters": 10,
      "captured_at": "2024-01-15T08:00:00Z"
    },
    "photo_url": "https://...",          // Optional punch photo
    "method": "mobile_app",              // mobile_app | web | manual | kiosk
    "device_info": {
      "device_id": "uuid",
      "platform": "ios",
      "app_version": "1.0.0"
    },
    "within_geofence": true,
    "geofence_distance_meters": 50
  },
  
  // Clock out details
  "clock_out": {
    "timestamp": "2024-01-15T17:00:00Z",
    "local_time": "2024-01-15T17:00:00",
    "gps": {
      "latitude": 40.7128,
      "longitude": -74.0061,
      "accuracy_meters": 15
    },
    "photo_url": null,
    "method": "mobile_app",
    "within_geofence": true
  },
  
  // Calculated fields
  "total_hours": 9.0,
  "regular_hours": 8.0,
  "overtime_hours": 1.0,
  "break_minutes": 60,                   // Deducted break time
  
  // Status tracking
  "status": "completed",                 // pending | completed | approved | rejected
  "approval": {
    "required": true,
    "approved_by": "uuid",
    "approved_at": "2024-01-16T09:00:00Z",
    "notes": "Approved"
  },
  
  // Offline sync
  "offline_sync": {
    "is_offline_entry": false,
    "offline_id": null,                  // Client-generated ID for offline
    "synced_at": null,
    "sync_conflicts": []
  },
  
  // Override/edit tracking
  "is_manual_entry": false,
  "original_values": null,               // Stores original if edited
  "edited_by": null,
  "edited_at": null,
  "edit_reason": null,
  
  // Flags
  "flags": {
    "late_clock_in": false,
    "early_clock_out": false,
    "missing_clock_out": false,
    "outside_geofence": false,
    "overtime_flagged": true
  },
  
  "created_at": "2024-01-15T08:00:00Z",
  "updated_at": "2024-01-15T17:00:00Z"
}

// Indexes
- { user_id: 1, date: -1 }
- { branch_id: 1, date: -1 }
- { team_id: 1, date: -1 }
- { job_site_id: 1, date: -1 }
- { status: 1, date: -1 }
- { "offline_sync.offline_id": 1 }       // For sync lookup
- { date: 1 }                            // Range queries
```

### 1.7 GPS Tracking Logs Collection
```javascript
{
  "id": "uuid",
  "user_id": "uuid",
  "time_entry_id": "uuid",               // Associated shift
  "branch_id": "uuid",
  
  // Location data
  "location": {
    "type": "Point",
    "coordinates": [-74.0060, 40.7128]   // [longitude, latitude] GeoJSON
  },
  "accuracy_meters": 10,
  "altitude_meters": 50,
  "speed_mps": 0,                        // Meters per second
  "heading": 180,                        // Degrees
  
  // Timestamps
  "captured_at": "2024-01-15T10:30:00Z",
  "received_at": "2024-01-15T10:30:05Z",
  
  // Context
  "is_within_geofence": true,
  "nearest_job_site_id": "uuid",
  "distance_from_site_meters": 25,
  
  // Battery/device info
  "battery_level": 85,
  "is_charging": false,
  
  // Sync status
  "is_offline_captured": false,
  "synced_at": null,
  
  "created_at": "2024-01-15T10:30:00Z"
}

// Indexes
- { user_id: 1, captured_at: -1 }
- { time_entry_id: 1 }
- { location: "2dsphere" }
- { captured_at: 1 }, { expireAfterSeconds: 7776000 }  // 90-day TTL
```

### 1.8 Overtime Records Collection
```javascript
{
  "id": "uuid",
  "user_id": "uuid",
  "branch_id": "uuid",
  "team_id": "uuid",
  
  // Period
  "period_type": "daily",                // daily | weekly
  "period_start": "2024-01-15",
  "period_end": "2024-01-15",
  
  // Overtime details
  "threshold_hours": 8.0,                // Threshold that triggered OT
  "total_worked_hours": 10.0,
  "overtime_hours": 2.0,
  
  // Rate tier (NOT hardcoded rate)
  "rate_tier": "standard_ot",            // References rate configuration
  "rate_multiplier": 1.5,                // Snapshot at time of calculation
  
  // Associated time entries
  "time_entry_ids": ["uuid"],
  
  // Approval workflow
  "status": "pending",                   // pending | approved | rejected | paid
  "requires_approval": true,
  "approval": {
    "approved_by": null,
    "approved_at": null,
    "rejected_reason": null
  },
  
  // Export tracking
  "exported": false,
  "export_batch_id": null,
  "exported_at": null,
  
  "calculated_at": "2024-01-16T00:00:00Z",
  "created_at": "2024-01-16T00:00:00Z",
  "updated_at": "2024-01-16T00:00:00Z"
}

// Indexes
- { user_id: 1, period_start: -1 }
- { branch_id: 1, period_start: -1 }
- { status: 1, period_start: -1 }
```

### 1.9 Audit Logs Collection
```javascript
{
  "id": "uuid",
  
  // Who
  "actor_id": "uuid",                    // User who performed action
  "actor_email": "admin@company.com",    // Denormalized for quick reference
  "actor_role": "BRANCH_ADMIN",
  "actor_ip": "192.168.1.1",
  "actor_device": "Chrome/Windows",
  
  // What
  "action": "time_entry.update",         // Standardized action codes
  "action_category": "time_entries",     // For filtering
  "description": "Modified clock-out time",
  
  // Target
  "target_type": "time_entry",
  "target_id": "uuid",
  "target_ref": "EMP001 - 2024-01-15",   // Human readable reference
  
  // Context
  "branch_id": "uuid",
  "team_id": "uuid",
  
  // Changes
  "changes": {
    "before": {
      "clock_out.timestamp": "2024-01-15T17:00:00Z",
      "total_hours": 9.0
    },
    "after": {
      "clock_out.timestamp": "2024-01-15T18:00:00Z",
      "total_hours": 10.0
    }
  },
  
  // Additional context
  "metadata": {
    "reason": "Employee forgot to clock out",
    "approval_id": "uuid",
    "request_id": "uuid"
  },
  
  // Timestamps
  "timestamp": "2024-01-16T09:00:00Z",
  "created_at": "2024-01-16T09:00:00Z"
}

// Indexes
- { actor_id: 1, timestamp: -1 }
- { target_type: 1, target_id: 1, timestamp: -1 }
- { action_category: 1, timestamp: -1 }
- { branch_id: 1, timestamp: -1 }
- { timestamp: -1 }
- { timestamp: 1 }, { expireAfterSeconds: 31536000 }  // 1-year TTL (optional)
```

### 1.10 Reports Collection (Saved/Scheduled Reports)
```javascript
{
  "id": "uuid",
  "name": "Weekly Attendance Summary",
  "type": "attendance_summary",          // attendance_summary | overtime | late_arrivals | payroll
  
  // Scope
  "scope": {
    "level": "branch",                   // self | team | branch | all
    "branch_id": "uuid",
    "team_id": null,
    "user_ids": []                       // Specific users (optional)
  },
  
  // Filters
  "filters": {
    "date_range": {
      "type": "relative",                // relative | absolute
      "relative_days": 7,                // Last 7 days
      "start_date": null,
      "end_date": null
    },
    "include_overtime": true,
    "include_late_arrivals": true,
    "status_filter": ["completed", "approved"]
  },
  
  // Output configuration
  "output": {
    "format": "xlsx",                    // csv | xlsx | pdf
    "columns": [
      "employee_id",
      "employee_name",
      "date",
      "clock_in",
      "clock_out",
      "total_hours",
      "overtime_hours"
    ],
    "group_by": "employee",
    "sort_by": "date"
  },
  
  // Schedule (optional)
  "schedule": {
    "enabled": false,
    "frequency": "weekly",               // daily | weekly | monthly
    "day_of_week": 1,                    // Monday
    "time": "06:00",
    "timezone": "America/New_York",
    "recipients": ["manager@company.com"]
  },
  
  // Last run
  "last_run": {
    "timestamp": "2024-01-15T06:00:00Z",
    "status": "success",
    "file_url": "https://...",
    "record_count": 150
  },
  
  // Ownership
  "created_by": "uuid",
  "visibility": "private",               // private | team | branch | all
  
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T06:00:00Z"
}

// Indexes
- { created_by: 1 }
- { type: 1, "scope.branch_id": 1 }
- { "schedule.enabled": 1, "schedule.frequency": 1 }
```

### 1.11 Rate Configuration Collection
```javascript
{
  "id": "uuid",
  "name": "Standard Rate Configuration",
  "code": "RATE-STD-2024",
  "effective_date": "2024-01-01",
  "expiry_date": null,
  "status": "active",
  
  // Rate tiers (NOT hardcoded values - configurable)
  "tiers": {
    "standard": {
      "description": "Regular hourly rate",
      "multiplier": 1.0
    },
    "standard_ot": {
      "description": "Standard overtime (1.5x)",
      "multiplier": 1.5,
      "applies_after_daily": 8,
      "applies_after_weekly": 40
    },
    "double_ot": {
      "description": "Double time overtime (2x)",
      "multiplier": 2.0,
      "applies_after_daily": 12,
      "applies_after_weekly": 60
    },
    "holiday": {
      "description": "Holiday rate",
      "multiplier": 2.0
    },
    "weekend": {
      "description": "Weekend rate",
      "multiplier": 1.25
    }
  },
  
  // Branch overrides
  "branch_overrides": {
    "branch_uuid": {
      "standard_ot": {
        "multiplier": 1.75
      }
    }
  },
  
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid"
}

// Indexes
- code: unique
- { status: 1, effective_date: -1 }
```

### 1.12 Shifts Collection
```javascript
{
  "id": "uuid",
  "name": "Morning Shift",
  "code": "SHIFT-AM",
  "branch_id": "uuid",
  
  // Timing
  "start_time": "08:00",                 // Local time HH:MM
  "end_time": "17:00",
  "break_minutes": 60,
  "total_hours": 8.0,
  
  // Days
  "days_of_week": [1, 2, 3, 4, 5],       // Monday=1, Sunday=7
  
  // Tolerance
  "early_clock_in_minutes": 15,
  "late_clock_in_minutes": 15,
  "early_clock_out_minutes": 15,
  
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}

// Indexes
- code: unique
- { branch_id: 1, status: 1 }
```

---

## 2. ROLE-BASED ACCESS CONTROL LOGIC

### Role Definitions

| Role | Level | Data Scope | Primary Capabilities |
|------|-------|------------|---------------------|
| SUPER_ADMIN | 100 | all | Full system access, configuration |
| BRANCH_ADMIN | 75 | branch | Branch management, all branch workers |
| TEAM_LEADER | 50 | team | Team oversight, time approval |
| WORKER | 25 | self | Self-service only |

### Permission Check Flow
```
Request → JWT Validation → Role Extraction → Permission Check → Data Scope Filter → Response

1. Extract user role from JWT
2. Load role permissions (cached)
3. Check specific permission for action
4. Apply data scope filter to query
5. Return filtered results
```

---

## 3. DATA RELATIONSHIPS (ERD)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   BRANCHES   │       │    TEAMS     │       │  JOB_SITES   │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄──┐   │ id (PK)      │   ┌──►│ id (PK)      │
│ name         │   │   │ name         │   │   │ name         │
│ code         │   │   │ branch_id(FK)│───┘   │ branch_id(FK)│
│ geofence     │   │   │ leader_id(FK)│──┐    │ geofence     │
└──────────────┘   │   └──────────────┘  │    └──────────────┘
       ▲           │          ▲          │           ▲
       │           │          │          │           │
       │           │          │          │           │
┌──────┴───────────┴──────────┴──────────┴───────────┴──────┐
│                         USERS                              │
├────────────────────────────────────────────────────────────┤
│ id (PK)                                                    │
│ email (unique)                                             │
│ employee_id (unique)                                       │
│ role ─────────────────────────────────────────────►ROLES   │
│ branch_id (FK) ───────────────────────────────────►BRANCHES│
│ team_id (FK) ─────────────────────────────────────►TEAMS   │
│ job_site_ids (FK[]) ──────────────────────────────►JOB_SITES│
└────────────────────────────────────────────────────────────┘
       │
       │ user_id
       ▼
┌──────────────────────────────────────────────────────────┐
│                    TIME_ENTRIES                           │
├──────────────────────────────────────────────────────────┤
│ id (PK)                                                   │
│ user_id (FK) ────────────────────────────────────►USERS   │
│ branch_id (FK) ──────────────────────────────────►BRANCHES│
│ team_id (FK) ────────────────────────────────────►TEAMS   │
│ job_site_id (FK) ────────────────────────────────►JOB_SITES│
│ clock_in { timestamp, gps, photo_url }                    │
│ clock_out { timestamp, gps, photo_url }                   │
│ offline_sync { is_offline, offline_id, synced_at }        │
└──────────────────────────────────────────────────────────┘
       │
       │ time_entry_id
       ▼
┌──────────────────────┐     ┌──────────────────────┐
│    GPS_LOGS          │     │  OVERTIME_RECORDS    │
├──────────────────────┤     ├──────────────────────┤
│ id (PK)              │     │ id (PK)              │
│ user_id (FK)         │     │ user_id (FK)         │
│ time_entry_id (FK)   │     │ time_entry_ids (FK[])│
│ location (GeoJSON)   │     │ rate_tier            │
│ captured_at          │     │ overtime_hours       │
└──────────────────────┘     │ status               │
                             └──────────────────────┘

┌──────────────────────┐     ┌──────────────────────┐
│    AUDIT_LOGS        │     │     REPORTS          │
├──────────────────────┤     ├──────────────────────┤
│ id (PK)              │     │ id (PK)              │
│ actor_id (FK)        │     │ created_by (FK)      │
│ target_type          │     │ scope { branch_id }  │
│ target_id            │     │ filters              │
│ action               │     │ schedule             │
│ changes { before,    │     │ output { format }    │
│           after }    │     └──────────────────────┘
└──────────────────────┘
```

---

## 4. CLOCK-IN DATA MODEL (Detailed)

```javascript
// Complete clock-in punch structure
{
  "timestamp": "2024-01-15T08:00:00Z",     // UTC timestamp
  "local_time": "2024-01-15T08:00:00",     // Local timezone time
  
  "gps": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "accuracy_meters": 10,                  // GPS accuracy
    "altitude_meters": 50,                  // Optional
    "captured_at": "2024-01-15T08:00:00Z", // When GPS was captured
    "provider": "gps"                       // gps | network | fused
  },
  
  "photo_url": "https://storage/punch-photo.jpg",  // Optional
  "photo_metadata": {
    "captured_at": "2024-01-15T08:00:00Z",
    "file_size_bytes": 102400,
    "verified": true                        // Face verification (future)
  },
  
  "method": "mobile_app",                   // mobile_app | web | manual | kiosk
  "device_info": {
    "device_id": "uuid",
    "platform": "ios",                      // ios | android | web
    "os_version": "17.0",
    "app_version": "1.0.0",
    "device_model": "iPhone 15"
  },
  
  "geofence_validation": {
    "within_geofence": true,
    "distance_from_center_meters": 50,
    "validated_against": "branch",          // branch | job_site
    "geofence_id": "uuid"
  }
}

// Offline sync structure
{
  "is_offline_entry": true,
  "offline_id": "client-generated-uuid",    // Generated on device
  "offline_captured_at": "2024-01-15T08:00:00Z",
  "synced_at": "2024-01-15T08:05:00Z",      // When synced to server
  "sync_attempts": 1,
  "sync_conflicts": [
    {
      "field": "clock_in.timestamp",
      "local_value": "...",
      "server_value": "...",
      "resolution": "local_wins"
    }
  ]
}
```

---

## 5. OVERTIME CALCULATION LOGIC STRUCTURE

```python
# Overtime calculation is CONFIGURATION-DRIVEN, not hardcoded

class OvertimeCalculator:
    """
    Overtime calculation based on configurable thresholds and multipliers.
    Rates are loaded from RateConfiguration collection.
    """
    
    def calculate_overtime(
        self,
        user_id: str,
        period_start: date,
        period_end: date,
        rate_config: RateConfiguration
    ) -> OvertimeResult:
        
        # 1. Load time entries for period
        time_entries = self.get_time_entries(user_id, period_start, period_end)
        
        # 2. Calculate daily overtime
        daily_overtime = []
        for entry in time_entries:
            daily_threshold = rate_config.get_threshold("daily", entry.branch_id)
            if entry.total_hours > daily_threshold:
                daily_overtime.append({
                    "date": entry.date,
                    "overtime_hours": entry.total_hours - daily_threshold,
                    "tier": self.determine_tier(
                        entry.total_hours, 
                        rate_config
                    )
                })
        
        # 3. Calculate weekly overtime (if applicable)
        weekly_total = sum(e.total_hours for e in time_entries)
        weekly_threshold = rate_config.get_threshold("weekly", branch_id)
        weekly_overtime = max(0, weekly_total - weekly_threshold)
        
        # 4. Determine applicable rate tier
        # Tiers are configurable: standard_ot (1.5x), double_ot (2x), etc.
        
        return OvertimeResult(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            daily_overtime=daily_overtime,
            weekly_overtime=weekly_overtime,
            applicable_tier=tier,
            rate_multiplier=rate_config.get_multiplier(tier)
        )

# Rate tiers loaded from database (NOT hardcoded)
RATE_TIERS = {
    "standard": {"multiplier": 1.0},
    "standard_ot": {"multiplier": "FROM_CONFIG"},    # e.g., 1.5
    "double_ot": {"multiplier": "FROM_CONFIG"},      # e.g., 2.0
    "holiday": {"multiplier": "FROM_CONFIG"},        # e.g., 2.0
    "weekend": {"multiplier": "FROM_CONFIG"}         # e.g., 1.25
}

# Thresholds loaded from branch settings (NOT hardcoded)
OVERTIME_THRESHOLDS = {
    "daily": "FROM_BRANCH_SETTINGS",                 # e.g., 8 hours
    "weekly": "FROM_BRANCH_SETTINGS"                 # e.g., 40 hours
}
```

---

## 6. AUDIT LOG TRACKING STRUCTURE

### Action Categories
```python
AUDIT_ACTIONS = {
    # Authentication
    "auth.login": "User logged in",
    "auth.logout": "User logged out",
    "auth.password_change": "Password changed",
    "auth.password_reset": "Password reset requested",
    
    # Users
    "user.create": "User created",
    "user.update": "User updated",
    "user.delete": "User deactivated",
    "user.role_change": "User role changed",
    "user.branch_assign": "User assigned to branch",
    
    # Branches
    "branch.create": "Branch created",
    "branch.update": "Branch updated",
    "branch.settings_change": "Branch settings modified",
    
    # Teams
    "team.create": "Team created",
    "team.update": "Team updated",
    "team.member_add": "Member added to team",
    "team.member_remove": "Member removed from team",
    
    # Time Entries
    "time_entry.clock_in": "Clock in recorded",
    "time_entry.clock_out": "Clock out recorded",
    "time_entry.update": "Time entry modified",
    "time_entry.delete": "Time entry deleted",
    "time_entry.approve": "Time entry approved",
    "time_entry.reject": "Time entry rejected",
    "time_entry.override": "Time entry overridden",
    
    # Overtime
    "overtime.calculate": "Overtime calculated",
    "overtime.approve": "Overtime approved",
    "overtime.reject": "Overtime rejected",
    
    # Reports
    "report.generate": "Report generated",
    "report.export": "Report exported",
    "report.schedule": "Report scheduled",
    
    # Settings
    "settings.update": "System settings updated",
    "rate_config.update": "Rate configuration updated"
}
```

### Audit Service Pattern
```python
class AuditService:
    async def log(
        self,
        actor: User,
        action: str,
        target_type: str,
        target_id: str,
        changes: dict = None,
        metadata: dict = None,
        request: Request = None
    ):
        audit_entry = {
            "id": str(uuid4()),
            "actor_id": actor.id,
            "actor_email": actor.email,
            "actor_role": actor.role,
            "actor_ip": self.get_client_ip(request),
            "actor_device": self.get_user_agent(request),
            "action": action,
            "action_category": action.split(".")[0],
            "description": AUDIT_ACTIONS.get(action, action),
            "target_type": target_type,
            "target_id": target_id,
            "branch_id": actor.branch_id,
            "changes": changes,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.audit_logs.insert_one(audit_entry)
```

---

## NEXT STEPS

Phase 2 database schema is complete. Ready for:
- **Phase 3**: Backend API implementation
- **Phase 4**: Frontend UI development
