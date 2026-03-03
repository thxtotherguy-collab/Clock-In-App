# Workforce Management System - PRD

## Original Problem Statement
Production-ready web & mobile responsive workforce management application supporting:
- 300+ workers
- 12-15 branches
- Mobile-first usage
- Admin dashboard
- GPS tracking
- Offline support (PWA)

## User Personas

| Persona | Role | Primary Goals |
|---------|------|---------------|
| Super Admin | System Owner | Full system config, all data access |
| Company Admin | Operations Head | All branches management, reporting |
| Branch Manager | Location Head | Own branch workers, attendance, reports |
| Supervisor | Team Lead | Team oversight, basic approvals |
| Worker | Field Staff | Punch attendance, view schedule |

## User Choices (Gathered)
- **Authentication**: JWT-based custom auth
- **GPS Tracking**: Real-time continuous tracking during shifts
- **Payroll Export**: CSV/Excel format
- **Offline Priority**: Attendance punch-in, viewing schedules
- **Compliance**: No specific requirements

## Core Requirements (Static)
1. Multi-role access control (5 roles)
2. Multi-branch data isolation
3. GPS-enabled attendance
4. PWA with offline support
5. Scalable for 300+ workers, 12-15 branches
6. CSV/Excel payroll export

## What's Been Implemented

### Phase 1 - Architecture Planning (Jan 2026)
- [x] High-level system architecture diagram
- [x] Multi-role structure with permission matrix
- [x] Scalable backend folder structure
- [x] Multi-branch data model & query patterns
- [x] MongoDB collection schemas with indexes
- [x] Core modules prioritization (P0, P1, P2, P3)
- [x] Complete project folder structure
- [x] Future scalability extensions documented
- [x] API endpoints overview
- [x] PWA offline strategy

### Phase 2 - Database & RBAC Structure (Jan 2026)
- [x] Complete database schema (11 collections)
- [x] User model with role assignment
- [x] Branch model with geofence configuration
- [x] Team and Job Site models
- [x] Time Entry (Clock-in) model with GPS & offline sync
- [x] GPS Tracking logs model
- [x] Overtime records model (configurable rates)
- [x] Audit logs model with change tracking
- [x] Rate Configuration model (not hardcoded)
- [x] Shift definition model
- [x] Report configuration model
- [x] Role-based permission system (4 roles, 48 permissions)
- [x] Data scope filtering (self/team/branch/all)
- [x] Permission middleware
- [x] Audit service
- [x] Overtime calculation service
- [x] Geospatial utilities for GPS

### Phase 3 - Worker Mobile MVP (Jan 2026)
- [x] Backend: JWT authentication (login/register/refresh)
- [x] Backend: Clock-in/out APIs with GPS validation
- [x] Backend: Double clock-in prevention (409 conflict)
- [x] Backend: Today status & week summary APIs
- [x] Backend: Offline sync endpoint
- [x] Backend: GPS logging endpoints (single & batch)
- [x] Frontend: PWA manifest & service worker
- [x] Frontend: IndexedDB offline storage
- [x] Frontend: Login/Register screen (mobile-first)
- [x] Frontend: Worker Dashboard with large clock button
- [x] Frontend: Real-time elapsed timer (HH:MM:SS)
- [x] Frontend: Stats cards (today/week hours, OT)
- [x] Frontend: Online/offline indicator with sync count
- [x] Frontend: GPS capture hook with battery optimization
- [x] Frontend: Mobile-first high contrast dark theme
- [x] Design: Max 2 taps to clock in (1 tap from dashboard)
- [x] Design: Outdoor readable (high contrast green/red buttons)
- [x] Design: Large touch targets (200px clock button)

## Prioritized Backlog

### P0 - MVP (Completed)
- [x] JWT authentication system
- [x] Attendance punch in/out
- [x] Real-time GPS tracking
- [x] Worker mobile interface

### P1 - Core Features (Next)
- [ ] Admin dashboard UI
- [ ] User management CRUD (admin)
- [ ] Branch management with geofence (admin)
- [ ] Payroll CSV/Excel export
- [ ] Attendance history & calendar
- [ ] Manual attendance override
- [ ] Late arrival reports

### P2 - Extended Features
- [ ] Leave management
- [ ] Task management
- [ ] Push notifications
- [ ] Advanced report builder

### P3 - Future
- [ ] Vehicle tracking
- [ ] Payroll system integration
- [ ] Biometric integration
- [ ] Multi-tenant support

## Next Tasks
1. **Phase 4: Admin Dashboard** - Branch admin & company admin interfaces
2. User CRUD APIs with role-based filtering
3. Branch CRUD with geofence management
4. Payroll export (CSV/Excel)
5. Attendance approval workflow
6. Report generation
