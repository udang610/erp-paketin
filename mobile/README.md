# Paketin HRGA Mobile App (Flutter)

This directory contains the initial structure and configuration for the Paketin Cargo HRGA mobile application.

## Overview
The mobile application is intended primarily for employees to:
1. **Clock-In / Clock-Out** (Absensi) with Face Verification and Location checking.
2. **Apply for Leave** (Pengajuan Cuti).
3. **View Attendance History** and Schedules.

## Architecture
- **State Management**: `flutter_riverpod` (Modern, compile-safe dependency injection & state management).
- **Networking**: `dio` + `retrofit` (Type-safe HTTP client mapped to the Django REST Framework API).
- **Face Verification**: `google_mlkit_face_detection` (For extracting face embeddings/liveliness directly on device).
- **Location**: `geolocator` (For enforcing attendance radius checks against Branch location).
- **Local Storage**: `flutter_secure_storage` (To securely store the JWT access & refresh tokens).

## Directory Structure Idea
- `lib/core/` (Networking, theme, routing, constants)
- `lib/features/`
  - `auth/` (Login, Token handling)
  - `attendance/` (Check-in/out logic, Face Camera UI, GPS check)
  - `leave/` (Leave balances, Request form)
  - `home/` (Dashboard, KPIs)

## Note
Because Flutter SDK is not installed locally on this environment, this serves as the foundational setup. You can run `flutter pub get` and build this project on your development machine where Flutter is fully installed.
