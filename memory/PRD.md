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

## Prioritized Backlog

### P0 - MVP (Phase 1 Implementation)
- [ ] JWT authentication system
- [ ] User management CRUD
- [ ] Branch management with geofence
- [ ] Attendance punch in/out
- [ ] Real-time GPS tracking
- [ ] Basic reports

### P1 - Core Features
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
1. **Phase 3: API Implementation** - Auth, User, Branch, Attendance endpoints
2. Implement JWT authentication with login/register
3. Build CRUD APIs for users, branches, teams
4. Implement clock-in/out with GPS validation
5. Build report generation and export
6. Create PWA service worker for offline support
