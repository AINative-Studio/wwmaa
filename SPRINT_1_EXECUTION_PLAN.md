# Sprint 1: Critical Fixes & Quick Wins - Execution Plan

**Sprint Goal:** Reach 90% completion by end of Week 1
**Current Status:** 85% complete → Target: 90%
**Duration:** 5-7 days
**Start Date:** November 15, 2025

---

## 📋 Sprint 1 Backlog

### Task 1: Install Playwright Browsers ✅ DONE
**Priority:** P0 (Blocker)
**Effort:** 5 minutes
**Status:** ✅ Chromium working, Firefox/WebKit optional
**Issue:** N/A
**Agent:** Manual fix

**Result:**
- ✅ Chromium installed and working (16/25 tests passing)
- 🟡 Firefox/WebKit installation issues (can skip for now)
- **Decision:** Proceed with Chromium only for Sprint 1

---

### Task 2: Fix E2E Login Timeout Issue
**Priority:** P0 (Blocker - blocks 17 tests)
**Effort:** 2-4 hours
**Status:** 🔴 IN PROGRESS
**Issue:** Reported in PRODUCTION_READINESS_FINAL_REPORT.md
**Agent:** test-engineer or qa-bug-hunter

**Problem Analysis:**
- Location: `/e2e/fixtures/test-data.ts:67`
- Current timeout: 10000ms (10 seconds)
- Symptom: `TimeoutError: page.waitForURL: Timeout 10000ms exceeded`
- Root cause: Login redirect takes >10s or URL condition not met

**Solution Options:**
1. **Option A:** Increase timeout to 30 seconds
2. **Option B:** Fix redirect performance
3. **Option C:** Change URL wait condition
4. **Option D:** Hybrid - increase timeout + improve condition

**Recommended:** Option D (increase to 30s + better condition)

**Implementation:**
```typescript
// BEFORE (line 67):
await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });

// AFTER:
await page.waitForURL(
  url => !url.pathname.includes('/login') && !url.pathname.includes('/auth'),
  { timeout: 30000 }
);
```

**Verification:**
- Run E2E auth tests
- Verify login flow completes
- Check 17 blocked tests now pass

---

### Task 3: Fix Resources/Profile API Test Mocking
**Priority:** P1 (High - improves test coverage)
**Effort:** 2-3 hours
**Status:** 🔴 NOT STARTED
**Issue:** Reported in PRODUCTION_READINESS_FINAL_REPORT.md
**Agent:** test-engineer

**Problem Analysis:**
- Resources API: 3/19 tests failing
- Profile API: 6/6 tests failing (100% failure)
- Root cause: FastAPI dependency override issues for auth mocking
- Pattern: Same auth mocking issue in both APIs

**Solution:**
- Fix FastAPI `app.dependency_overrides` pattern
- Ensure mock auth user is properly injected
- Verify in both `test_resources_routes.py` and `test_profile_routes.py`

**Files to Modify:**
- `/backend/tests/test_resources_routes.py`
- `/backend/tests/test_profile_routes.py`
- Possibly `/backend/tests/conftest.py` (shared auth fixture)

**Verification:**
- Run: `pytest backend/tests/test_resources_routes.py -v`
- Run: `pytest backend/tests/test_profile_routes.py -v`
- Target: 95%+ pass rate on both

---

### Task 4: Complete Search Backend Integration
**Priority:** P1 (High - completes search feature)
**Effort:** 4-6 hours
**Status:** 🟡 PARTIAL (frontend done, backend needs completion)
**Issue:** Mentioned in MISSING_FEATURES_IMPLEMENTATION.md
**Agent:** backend-api-architect

**Current Status:**
- ✅ Frontend search page fixed (input attributes correct)
- ✅ Frontend proxies to `/api/search/query`
- 🟡 Backend API exists but incomplete
- ❌ Full search pipeline not connected

**What's Needed:**
1. Verify OpenAI embedding generation working
2. Ensure ZeroDB vector search connected
3. Test AI answer generation (AI Registry)
4. Verify media attachment (Cloudflare videos/images)
5. Test related queries generation
6. Validate caching and rate limiting

**Files to Review/Modify:**
- `/backend/routes/search.py` - Main search endpoint
- `/backend/services/embedding_service.py` - OpenAI embeddings
- `/backend/services/zerodb_service.py` - Vector search
- `/app/api/search/route.ts` - Frontend proxy (already done)

**Verification:**
- Test search query end-to-end
- Verify results include:
  - AI-generated answer
  - Relevant sources
  - Media attachments (if applicable)
  - Related queries
- Check caching working (X-Cache-Status header)

---

### Task 5: Build Member Management UI (#199)
**Priority:** P1 (High - critical admin feature)
**Effort:** 2 days
**Status:** 🔴 NOT STARTED
**Issue:** #199 (US-052: Member Management Interface)
**Agent:** frontend-ui-builder

**Requirements (from issue #199):**
- [ ] Member list view (table/grid)
- [ ] Search/filter members
- [ ] Sort by name, tier, status, join date
- [ ] Member detail view (modal or page)
- [ ] Edit member profile (admin)
- [ ] Update membership tier
- [ ] Activate/deactivate members
- [ ] View member activity history
- [ ] Export member list (CSV)

**Backend API Status:**
- ✅ Backend instructor API exists and working
- ✅ Member CRUD operations available
- ✅ Just needs frontend UI

**Files to Create:**
- `/app/dashboard/admin/members/page.tsx` - Main member management page
- `/components/admin/MemberTable.tsx` - Member list component
- `/components/admin/MemberFilters.tsx` - Search/filter component
- `/components/admin/MemberDetailsModal.tsx` - Member detail view
- `/lib/admin-api.ts` - Admin API methods (if not exists)

**Verification:**
- Admin can view all members
- Search/filter works correctly
- Member details can be viewed
- Profile updates persist to backend
- Tier changes work

---

## 🎯 Sprint 1 Success Criteria

**Completion Metrics:**
- ✅ Playwright browsers installed (Chromium working)
- 🎯 E2E login timeout fixed (17 tests unblocked)
- 🎯 Backend API tests: 95%+ pass rate
- 🎯 Search feature: 100% functional end-to-end
- 🎯 Member management UI: Complete and functional
- 🎯 **Overall completion: 90%** (up from 85%)

**Test Pass Rates:**
- Backend API tests: 82.5% → 95%+
- E2E tests: 62.7% → 75%+
- Frontend build: 100% (maintain)

**Production Readiness:**
- Zero critical bugs
- All admin tooling functional
- Search working properly
- Test suite reliable

---

## 🚀 Execution Strategy

### Parallel Execution (Recommended)
Launch multiple specialized agents simultaneously:

1. **test-engineer** → Fix E2E login timeout (Task 2)
2. **test-engineer** → Fix API test mocking (Task 3)
3. **backend-api-architect** → Complete search backend (Task 4)
4. **frontend-ui-builder** → Build member management UI (Task 5)

**Estimated Completion:** 2-3 days in parallel

### Sequential Execution (Alternative)
Complete tasks in order of priority:
1. Day 1: Tasks 2 + 3 (test fixes)
2. Day 2-3: Task 4 (search backend)
3. Day 4-5: Task 5 (member UI)

**Estimated Completion:** 5-7 days sequential

---

## 📊 Sprint 1 Tracking

### Day 1 Progress
- [x] Task 1: Playwright browsers (Chromium working)
- [ ] Task 2: E2E login timeout
- [ ] Task 3: API test mocking
- [ ] Task 4: Search backend
- [ ] Task 5: Member management UI

### Daily Standup Questions
1. What was completed yesterday?
2. What will be completed today?
3. Any blockers?

---

## 🎯 Sprint 1 Deliverables

**By End of Week 1:**
1. ✅ Playwright installed and verified
2. 🎯 E2E tests passing at 75%+
3. 🎯 Backend tests passing at 95%+
4. 🎯 Search feature 100% functional
5. 🎯 Member management UI complete
6. 🎯 Platform at 90% completion
7. 🎯 Ready for Sprint 2 (Two-Board Approval)

---

## 📝 Notes & Decisions

**Decision 1:** Proceed with Chromium only for E2E tests
- **Rationale:** Chromium is primary browser, Firefox/WebKit nice-to-have
- **Impact:** Can complete Sprint 1 without Firefox/WebKit

**Decision 2:** Parallel agent execution recommended
- **Rationale:** Tasks are independent, can run simultaneously
- **Impact:** Reduces Sprint 1 from 5-7 days to 2-3 days

**Decision 3:** Focus on PRD features only
- **Rationale:** Build contract obligations first, value-adds after
- **Impact:** Clear scope, no feature creep

---

## 🔗 Related Documents

- PATH_TO_100_PERCENT_COMPLETION.md - Full roadmap
- PRODUCTION_READINESS_FINAL_REPORT.md - Current status
- GITHUB_ISSUES_VS_PRD_ANALYSIS.md - Issue mapping
- MISSING_FEATURES_IMPLEMENTATION.md - Feature status

---

## ✅ Next Steps After Sprint 1

**Sprint 2: Two-Board Approval (Weeks 2-3)**
- Implement #30, #29 (backend APIs)
- Build #211 (board member dashboard UI)
- Target: 92% completion

**Sprint 3-6: Live Training (Weeks 4-6)**
- Implement issues #56-63
- Cloudflare Calls integration
- Target: 95% completion

**Sprint 7-10: Remaining Features (Weeks 7-10)**
- Belt progression (#209)
- Certificates (#210)
- VOD library
- Final polish
- Target: 100% completion

---

*Sprint 1 Plan Created: November 15, 2025*
*Target Completion: November 22, 2025 (7 days)*
*Goal: 85% → 90% completion*
