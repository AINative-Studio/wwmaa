# Member Management - Quick Start Guide

## Accessing Member Management

1. **Login as Admin**
   - Navigate to your admin dashboard
   - Credentials: Use your admin account

2. **Access Members Page**
   - URL: `/dashboard/admin/members`
   - Or click "Members" in admin sidebar navigation

## Key Features

### Search & Filter
```
Search: Type in search box to filter by name, email, or phone
Role Filter: Select from dropdown (Member, Instructor, Board Member, Admin)
Status Filter: Active or Inactive members
Clear Filters: X button to reset all filters
```

### View Member
1. Click "..." menu on any member row
2. Select "View Details"
3. See full profile information
4. Switch to "Activity" tab (placeholder)

### Create Member
1. Click "Add Member" button (top right)
2. Fill required fields:
   - First Name *
   - Last Name *
   - Email *
   - Password * (min 8 characters)
3. Optional: Phone, Role
4. Click "Create Member"

### Edit Member
1. Click "..." menu on member row
2. Select "Edit Member"
3. Update any field
4. Password optional (leave blank to keep current)
5. Click "Update Member"

### Delete Member
1. Click "..." menu on member row
2. Select "Delete Member"
3. Confirm deletion
4. Member permanently removed

### Export Data
1. Click "Export CSV" button
2. CSV file downloads with all filtered members
3. Includes: ID, Name, Email, Role, Phone, Location, Created Date

## Components Reference

```
/app/dashboard/admin/members/page.tsx
├── Main page component
├── Handles all state management
└── Coordinates child components

/components/admin/MemberTable.tsx
├── Displays members in table format
├── Action dropdowns
└── Role/status badges

/components/admin/MemberFilters.tsx
├── Search input (debounced)
├── Role filter dropdown
├── Status filter dropdown
└── Clear filters button

/components/admin/MemberDetailsModal.tsx
├── View mode (read-only)
├── Edit mode (update existing)
└── Create mode (add new)
```

## API Endpoints Used

```typescript
GET    /api/admin/members?limit=20&offset=0&search=...&role=...&is_active=...
POST   /api/admin/members
PUT    /api/admin/members/:id
DELETE /api/admin/members/:id
```

## Common Tasks

### Add Multiple Members
For bulk import, use CSV import feature (planned for future).

### Change Member Role
1. Edit member
2. Select new role from dropdown
3. Save changes

### Find Inactive Members
1. Set Status filter to "Inactive"
2. View filtered list

### Email All Instructors
1. Set Role filter to "Instructor"
2. Click "Export CSV" to get list
3. Use external email tool (integrated email planned)

## Troubleshooting

**Problem**: Members not loading
- **Solution**: Check network connection, verify admin authentication

**Problem**: Can't create member
- **Solution**: Ensure all required fields filled, password min 8 chars

**Problem**: Search not working
- **Solution**: Wait 500ms for debounce, or type more characters

**Problem**: Export CSV empty
- **Solution**: Check active filters, may be filtering out all members

## Technical Notes

- Pagination: 20 members per page
- Search debounce: 500ms
- Auto-refresh: After create/edit/delete
- Notifications: Auto-dismiss after 5 seconds
- CSV format: Standard RFC 4180 compliant

## Next Steps

After initial setup:
1. Create your first members via "Add Member"
2. Set up role hierarchy (member → instructor → board → admin)
3. Review and update existing member profiles
4. Export current member list for records
5. Plan bulk import if needed

## Support

For issues or questions:
- Check backend API status at `/api/admin/members`
- Review browser console for errors
- Check network tab for API responses
- Verify admin role permissions

---

Built for World Wide Martial Arts Association
Version: 1.0.0 | Date: 2025-11-15
