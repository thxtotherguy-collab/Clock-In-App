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

### P1 - Core Features (Completed - Phase 4 & 5)
- [x] Admin dashboard UI with sidebar navigation
- [x] User management CRUD (admin)
- [x] Branch management with geofence (admin)
- [x] Payroll CSV/Excel export (openpyxl)
- [x] Attendance history & time entries
- [x] Manual attendance override with audit trail
- [x] Late arrival reports
- [x] Timesheet approval workflow (approve/reject/bulk)
- [x] Role-based routing (admin vs worker views)
- [x] Automated daily email reports (6PM trigger, MOCKED sender)
- [x] Configurable recipients list (global, HR CC, Finance CC)
- [x] SA BCEA overtime configuration (9hrs/day, 45hrs/week, 1.5x/2x rates)
- [x] Report preview (data + HTML email template)
- [x] Report run history & email logs
- [x] Payroll summary with overtime calculations
- [x] APScheduler-based automation (branch-specific distribution)
- [x] Audit logs viewer

### P2 - Extended Features
- [ ] Leave management
- [ ] Task management
- [ ] Push notifications
- [ ] Advanced report builder
- [ ] Real email integration (SendGrid/SMTP)

### P3 - Future
- [ ] Vehicle tracking
- [ ] Payroll system integration
- [ ] Biometric integration
- [ ] Multi-tenant support

## Phase 4 - Admin Dashboard MVP (March 2026)
- [x] AdminLayout with sidebar navigation (8 nav items)
- [x] Role-based routing in App.js
- [x] Dashboard overview (real-time stats, branch/date filters)
- [x] Time entries management (list, edit modal, approve/reject)
- [x] Approvals manager (dedicated queue, bulk actions)
- [x] Workers CRUD (role/branch/status filters)
- [x] Branches management (cards, create/edit, geofence, details)
- [x] Export center (CSV + Excel: payroll, timesheet, attendance)
- [x] Audit logs viewer (category/type/date filters)
- [x] Branch admin data restriction

## Phase 5 - Automated Reporting & Payroll Engine (March 2026)
- [x] Report generation service (daily aggregation)
- [x] Email service (MOCKED - professional HTML templates)
- [x] APScheduler with 6PM UTC daily cron trigger
- [x] Configurable recipients (global, per-branch, HR CC, Finance CC)
- [x] "Send Report Now" manual trigger
- [x] Report preview (data + HTML email)
- [x] SA BCEA overtime configuration (configurable per branch)
- [x] Payroll summary endpoint
- [x] Scheduler status monitoring
- [x] ReportsManager frontend with 4 tabs (Overview, Config, Overtime, History)

## Next Tasks
1. **Phase 6: Leave Management** - Leave types, requests, approvals
2. Push notifications
3. Real email provider integration (SendGrid/SMTP)
4. Advanced report builder
