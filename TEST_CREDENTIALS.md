# Test User Credentials

These test accounts are seeded in the ZeroDB database and ready for testing.

---

## Test Accounts

### 1. Admin User
```
Email:    admin@wwmaa.com
Password: AdminPass123!
Role:     admin
```
**Access:** Full administrative access

### 2. Regular Member
```
Email:    test@wwmaa.com
Password: TestPass123!
Role:     member
```
**Access:** Standard member features

### 3. Board Member
```
Email:    board@wwmaa.com
Password: BoardPass123!
Role:     board_member
```
**Access:** Board-level permissions

---

## Quick Test URLs

- **Login:** https://wwmaa.ainative.studio/login
- **Register:** https://wwmaa.ainative.studio/register
- **Dashboard:** https://wwmaa.ainative.studio/dashboard
- **Profile:** https://wwmaa.ainative.studio/profile
- **Events:** https://wwmaa.ainative.studio/events

---

## What to Test

### Authentication
- [x] Login with each account
- [x] Logout functionality
- [x] Password validation
- [x] Role-based access control

### User Features
- [x] View profile
- [x] Update profile information
- [x] View membership tier
- [x] Access dashboard

### Admin Features (admin@wwmaa.com only)
- [x] Access admin panel
- [x] Manage users
- [x] Approve applications
- [x] Create/edit events

### Events
- [x] View event listings
- [x] RSVP to events
- [x] View event details
- [x] Cancel RSVP

---

## Password Format

All test passwords follow this pattern:
```
[Role]Pass123!
```

Examples:
- Admin → `AdminPass123!`
- Test → `TestPass123!`
- Board → `BoardPass123!`

---

## Database Info

- **Project ID:** e4f3d95f-593f-4ae6-9017-24bff5f72c5e
- **Tables:** users, profiles, events
- **Passwords:** Bcrypt hashed
- **Status:** All users active and verified

---

## Need More Test Users?

To create additional test users, run:
```bash
cd /Users/aideveloper/Desktop/wwmaa
python3 scripts/seed_zerodb.py
```

Or use the registration page to create new accounts.

---

*Last Updated: November 12, 2025*
*For production deployment on Railway*
