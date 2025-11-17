# WWMAA Platform - Week 2 Sprint Plan

**Sprint Duration:** November 15-21, 2025 (7 days)
**Focus:** Bug Fixes, Data Persistence, Client Onboarding, UX Polish
**Team:** AINative Studio Development Team

---

## 🎯 Week 2 Objectives

### Primary Goals
1. ✅ **Fix All Critical Bugs** - Address 23 identified issues from Week 1 testing
2. ✅ **Enable Data Persistence** - All CRUD operations save to database
3. ✅ **Client Credential Transition** - Collect and configure production keys
4. ✅ **Complete Strapi Integration** - Full CMS for content management
5. ✅ **Production Smoke Testing** - End-to-end validation with real data

### Success Criteria
- [ ] Zero P0/P1 bugs remaining
- [ ] All admin forms functional (add, edit, delete)
- [ ] All student dashboard features working
- [ ] Client production credentials configured
- [ ] Public site pages fully dynamic (Strapi-backed)
- [ ] Payment flow tested end-to-end with client Stripe account

---

## 📋 Week 2 Backlog (23 Issues)

### 🔴 Priority 1 - Critical (Must Fix This Week)

#### Issue #1: Fix role-based redirect after login
**Impact:** Admins land on student dashboard instead of admin dashboard
**Status:** ✅ FIXED (deployed November 14)
**Tasks:**
- [x] Update Role type to lowercase
- [x] Fix server-side cookie authentication
- [x] Remove mock data dependencies
**Estimated:** Already complete
**Actual:** 4 commits, 6 hours

#### Issue #2: Student dashboard - Profile edits not persisting
**Impact:** Users can't update their profiles
**Tasks:**
- [ ] Verify `PATCH /api/me/profile` endpoint exists
- [ ] Wire Edit Profile form to endpoint
- [ ] Implement profile photo upload (S3/Cloudflare R2)
- [ ] Add success/error notifications
- [ ] Test: edit → save → refresh → verify changes
**Estimated:** 1 day
**Assigned:** Backend + Frontend dev

#### Issue #3: Student dashboard - Resources page static
**Impact:** Students see "Coming soon" instead of actual resources
**Tasks:**
- [ ] Create `GET /api/resources` endpoint
- [ ] Define resource schema (title, description, file_url, category)
- [ ] Replace static text with API-backed component
- [ ] Show empty state when no resources exist
**Estimated:** 4 hours
**Assigned:** Backend dev

#### Issue #4: Renew Membership button not wired
**Impact:** Members cannot renew subscriptions
**Tasks:**
- [ ] Implement `POST /api/payments/create-renewal-session`
- [ ] Wire button click to create Stripe checkout
- [ ] Handle webhook for successful renewal
- [ ] Update expiry date in UI after payment
**Estimated:** 6 hours
**Assigned:** Backend dev (requires client Stripe keys)

#### Issue #5: Public events page shows no events
**Impact:** Public calendar is empty even with events in DB
**Tasks:**
- [ ] Verify frontend calls `GET /api/events/public`
- [ ] Confirm request parameters match backend expectations
- [ ] Seed at least 3 test events
- [ ] Bind API response to calendar/list components
- [ ] Add empty state message
**Estimated:** 4 hours
**Assigned:** Frontend dev

#### Issue #7: Navigation 404s (Dashboard/Profile/Settings)
**Impact:** Users can't navigate to key pages
**Tasks:**
- [ ] Review all navigation links and routes
- [ ] Fix hardcoded paths
- [ ] Add role guards for protected routes
- [ ] Test all nav links for all roles
**Estimated:** 4 hours
**Assigned:** Frontend dev

**Total P1 Estimated Effort:** 2.5 days

---

### 🟠 Priority 2 - High (Should Fix This Week)

#### Issue #8: Admin Members - Add Member modal not saving
**Tasks:**
- [ ] Implement `POST /admin/members` endpoint
- [ ] Wire form submission
- [ ] Handle validation errors
- [ ] Refresh table after success
**Estimated:** 4 hours

#### Issue #9: Admin Members - Edit/Delete not functional
**Tasks:**
- [ ] Wire Edit to open modal with member data
- [ ] Connect to `PUT /admin/members/:id`
- [ ] Implement `DELETE /admin/members/:id`
- [ ] Add confirmation dialog for delete
**Estimated:** 6 hours

#### Issue #10: Admin Instructors - Add Instructor not saving
**Tasks:**
- [ ] Implement `POST /admin/instructors` endpoint
- [ ] Wire form submission
- [ ] Handle success/error states
**Estimated:** 3 hours

#### Issue #11: Admin Instructors - Actions not implemented
**Tasks:**
- [ ] Edit profile → `PUT /admin/instructors/:id`
- [ ] View performance → create performance endpoint + UI
- [ ] Assign class → create class assignment endpoint + UI
**Estimated:** 1 day

#### Issue #12: Admin Events - Create Event not saving
**Tasks:**
- [ ] Verify `POST /admin/events` endpoint
- [ ] Wire modal form submission
- [ ] Handle date/time, capacity, location correctly
- [ ] Refresh events list after creation
**Estimated:** 4 hours

#### Issue #13: Admin Events - Modal styling (transparent)
**Tasks:**
- [ ] Update modal component CSS (white background)
- [ ] Add proper backdrop overlay
- [ ] Test on desktop and mobile
**Estimated:** 1 hour

**Total P2 Estimated Effort:** 3 days

---

### 🟡 Priority 3 - Medium (If Time Permits)

#### Issue #14: Admin Analytics - Hard-coded metrics
**Tasks:**
- [ ] Implement `GET /admin/analytics` endpoint
- [ ] Return real metrics from DB
- [ ] Wire dashboard to API
**Estimated:** 6 hours

#### Issue #18: Admin Settings - Org/tier settings not persisting
**Tasks:**
- [ ] Implement `PATCH /admin/settings/org`
- [ ] Implement `PATCH /admin/settings/membership-tiers`
- [ ] Wire Settings forms to endpoints
**Estimated:** 4 hours

#### Issue #19: Admin Settings - Email settings
**Tasks:**
- [ ] Create email config model
- [ ] Implement settings endpoint
- [ ] Add "Send test email" button
**Estimated:** 4 hours

#### Issue #20: Admin Settings - Stripe configuration UI
**Tasks:**
- [ ] Add Stripe key input fields (publishable, secret, webhook)
- [ ] Implement secure storage endpoint
- [ ] Mask sensitive values in UI
**Estimated:** 4 hours

**Total P3 Estimated Effort:** 2 days

---

### 🔵 Priority 4 - Enhancement (Week 3 or Post-Launch)

#### Issue #15: Strapi CMS - Article CRUD
**Tasks:**
- [ ] Audit Strapi setup and content types
- [ ] Wire article listing/detail to Strapi API
- [ ] Add article creation/edit forms
- [ ] Test publish → public site workflow
**Estimated:** 2 days

#### Issue #16: Admin Content - Video upload
**Tasks:**
- [ ] Design video upload workflow
- [ ] Integrate with Cloudflare Stream
- [ ] Store metadata in DB
- [ ] Display video list
**Estimated:** 1.5 days

#### Issue #17: Admin Content - Training resources manager
**Tasks:**
- [ ] Create Resources manager in admin
- [ ] Add CRUD endpoints for resources
- [ ] Wire to student Resources page
**Estimated:** 1 day

#### Issue #21: PayPal - Clarify or remove
**Tasks:**
- [ ] Confirm if PayPal in scope
- [ ] Remove toggle if not needed
- [ ] OR add PayPal configuration
**Estimated:** 1 hour (to remove) or 1 week (to implement)

#### Issue #22: Membership lifecycle - APPROVED → PAYMENT → ACTIVE
**Tasks:**
- [ ] Add membership status transitions
- [ ] Show payment CTA for approved users
- [ ] Update status to ACTIVE after payment
**Estimated:** 1 day

#### Issue #23: Strapi - Core site pages integration
**Tasks:**
- [ ] Define Strapi content types for main pages
- [ ] Update public site to fetch from Strapi
- [ ] Add link to Strapi admin in WWMAA admin
**Estimated:** 2 days

**Total P4 Estimated Effort:** 8 days (deferred to Week 3)

---

## 📅 Week 2 Daily Schedule

### Monday, November 15
**Theme:** Client Onboarding + P1 Bug Fixes

**Morning:**
- 9:00 AM: Sprint Planning & Standup
- 9:30 AM: Client kickoff call
  - Review Week 1 progress report
  - Walk through credential checklist
  - Set timeline for credential delivery
- 10:30 AM: Begin P1 fixes

**Afternoon:**
- Continue P1 fixes (Issues #2, #3, #4, #5, #7)
- Deploy fixes incrementally
- Test on staging

**Goals:**
- [ ] Client call complete
- [ ] 2-3 P1 issues resolved

---

### Tuesday, November 16
**Theme:** P1 Completion + Client Credentials

**All Day:**
- Complete remaining P1 issues
- Configure client Stripe keys (if received)
- Test payment flow end-to-end
- Deploy to production

**Goals:**
- [ ] All P1 issues closed
- [ ] Stripe production keys configured (if available)
- [ ] Payment flow tested

---

### Wednesday, November 17
**Theme:** P2 Admin Dashboard Fixes

**Focus:**
- Issues #8, #9, #10, #11, #12, #13
- All admin CRUD operations functional
- Modal styling fixes

**Goals:**
- [ ] Admin Members CRUD working
- [ ] Admin Instructors CRUD working
- [ ] Admin Events CRUD working
- [ ] Modal styling fixed

---

### Thursday, November 18
**Theme:** P3 Settings & Analytics

**Focus:**
- Issues #14, #18, #19, #20
- Admin Settings persistence
- Live analytics dashboard

**Goals:**
- [ ] Settings persistence working
- [ ] Email configuration functional
- [ ] Stripe UI settings available
- [ ] Analytics pulling live data

---

### Friday, November 19
**Theme:** Strapi Integration

**Focus:**
- Issue #15, #23
- Full Strapi CMS for content
- Public site pages dynamic

**Goals:**
- [ ] Strapi article CRUD working
- [ ] Public blog pulling from Strapi
- [ ] Core pages (Programs, About, etc.) Strapi-backed

---

### Saturday, November 20 (Optional)
**Theme:** Polish & Testing

**Focus:**
- Catch-up on any blocked items
- End-to-end smoke tests
- Performance optimization
- Documentation

**Goals:**
- [ ] All Week 2 issues closed
- [ ] Production smoke tests passing
- [ ] Documentation updated

---

### Sunday, November 21
**Theme:** Week 3 Planning

**Focus:**
- Review Week 2 completion
- Plan Week 3 launch preparation
- Client training materials prep

---

## 🔧 Technical Approach

### Data Persistence Strategy
All CRUD operations must:
1. Make API call to backend endpoint
2. Handle loading state (spinner/disable button)
3. Handle success (close modal, show toast, refresh list)
4. Handle errors (show error message, keep modal open)
5. Validate input before submission

### Endpoint Development Checklist
For each new endpoint:
- [ ] Pydantic model for request/response
- [ ] Database query with proper filtering
- [ ] Error handling (404, 400, 401, 403, 500)
- [ ] Authorization check (role-based)
- [ ] Input validation
- [ ] Unit test
- [ ] API documentation (auto-generated by FastAPI)

### Frontend Integration Checklist
For each form/modal:
- [ ] Form state management (React Hook Form or useState)
- [ ] Input validation (client-side + server-side)
- [ ] Loading state during API call
- [ ] Success notification (toast/banner)
- [ ] Error handling (display error message)
- [ ] Refresh data after success
- [ ] Close modal/reset form after success

---

## 🚨 Risk Management

### Known Risks

**Risk 1: Client Credentials Delayed**
- **Impact:** Cannot test payments, emails in production
- **Mitigation:** Continue with test credentials, prepare documentation
- **Owner:** Project Manager

**Risk 2: Strapi Integration Complexity**
- **Impact:** May take longer than estimated
- **Mitigation:** Defer to Week 3 if needed, focus on P1/P2 first
- **Owner:** Backend Lead

**Risk 3: Data Migration Issues**
- **Impact:** Existing data may not persist correctly
- **Mitigation:** Thorough testing, database backups before changes
- **Owner:** Backend Dev

**Risk 4: UI/UX Changes Requested**
- **Impact:** Scope creep, timeline impact
- **Mitigation:** Document changes, defer non-critical to post-launch
- **Owner:** Project Manager

### Blockers to Escalate
- If client credentials not received by Wednesday
- If Stripe integration has unexpected issues
- If database schema changes break existing data
- If Strapi integration requires architecture changes

---

## 📊 Definition of Done

### For Each Issue:
- [ ] Code implemented and reviewed
- [ ] Unit tests passing
- [ ] E2E test added (if applicable)
- [ ] Deployed to staging
- [ ] QA tested on staging
- [ ] Client approval (for UI changes)
- [ ] Deployed to production
- [ ] Smoke tested on production
- [ ] Documentation updated
- [ ] Issue closed with comment

### For Week 2 Sprint:
- [ ] All P1 issues closed
- [ ] 80%+ of P2 issues closed
- [ ] Client credentials configured
- [ ] Production smoke tests passing
- [ ] No critical bugs in production
- [ ] Week 3 plan drafted

---

## 🎯 Success Metrics

### Velocity
- **Target:** 15-20 issues closed
- **Stretch:** All 23 issues closed

### Quality
- **Target:** Zero P0 bugs introduced
- **Target:** 90%+ test coverage maintained
- **Target:** Build success rate > 95%

### Client Satisfaction
- **Target:** Client credentials received by Wednesday
- **Target:** Weekly demo shows visible progress
- **Target:** No surprise blockers

---

## 📞 Communication Plan

### Daily Standups
- **Time:** 9:00 AM PST
- **Duration:** 15 minutes
- **Format:** What I did, What I'm doing, Blockers

### Client Check-ins
- **Monday:** Week kickoff call (credential review)
- **Wednesday:** Mid-week progress update (async)
- **Friday:** End-of-week demo (30 minutes)

### Deployment Notifications
- All production deployments announced in team chat
- Critical changes require client approval before deploy

---

## 🚀 Week 3 Preview

### Tentative Focus Areas
1. **Launch Preparation** - Final QA, performance tuning
2. **Client Training** - Admin dashboard tutorial, content management
3. **Marketing Materials** - Screenshots, feature list, FAQ
4. **Go-Live Plan** - DNS cutover, final smoke tests
5. **Post-Launch Support** - Bug hotfix process, monitoring

---

## ✅ Checklist: Before Starting Week 2

**Client Side:**
- [ ] Review Week 1 progress report
- [ ] Review credentials checklist
- [ ] Schedule Monday kickoff call
- [ ] Begin gathering production credentials

**Development Team:**
- [ ] Review all 23 issues
- [ ] Assign issues to team members
- [ ] Set up tracking board (Kanban/Sprint)
- [ ] Prepare dev/staging environments
- [ ] Review PRD for any missed requirements

**DevOps:**
- [ ] Ensure staging is stable
- [ ] Prepare rollback procedures
- [ ] Set up deployment pipeline for rapid iteration
- [ ] Monitor Railway quotas/usage

---

*Sprint Plan Prepared By: AINative Studio*
*Date: November 14, 2025*
*Sprint Start: November 15, 2025*
*Sprint End: November 21, 2025*
