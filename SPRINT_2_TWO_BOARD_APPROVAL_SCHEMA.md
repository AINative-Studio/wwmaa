# Sprint 2: Two-Board Approval Workflow - Database Schema Design

**Date:** November 16, 2025
**Sprint:** Sprint 2 - Two-Board Approval Workflow
**Status:** 🔄 In Progress

---

## 📋 Requirements

From PRD User Stories:
- **US-016:** Board members can view and vote on pending applications
- **US-017:** System requires 2 board member approvals before membership activation
- Applications must support concurrent voting by multiple board members
- Need audit trail of all votes and decisions
- Support for conditional approvals and rejections
- Email notifications on status changes

---

## 🗂️ Current Schema Analysis

### Existing Collections:

**1. `applications` Collection** (from `backend/models/schemas.py:229`)
```python
class Application(BaseDocument):
    user_id: UUID
    status: ApplicationStatus  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED

    # Applicant info (name, email, address, etc.)
    # Martial arts info (disciplines, experience, rank)
    # Application details (motivation, goals)

    # Current workflow fields
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[UUID]  # ⚠️ Single reviewer only
    decision_notes: Optional[str]

    # Rejection fields
    rejected_at: Optional[datetime]
    rejected_by: Optional[UUID]  # ⚠️ Single rejector only
    rejection_reason: Optional[str]
```

**2. `approvals` Collection** (from `backend/models/schemas.py:292`)
```python
class Approval(BaseDocument):
    application_id: UUID
    approver_id: UUID  # Board member who voted
    status: ApprovalStatus  # PENDING, APPROVED, REJECTED
    action: ApprovalAction  # APPROVE, REJECT, INVALIDATE
    notes: Optional[str]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    invalidated_at: Optional[datetime]
    conditions: Optional[List[str]]
    priority: int
    is_active: bool
```

### ✅ Good News:
- `approvals` collection already exists and supports multiple approvals!
- Has timestamps for each action
- Has notes field for comments
- Has conditions field for conditional approvals

### ⚠️ Gaps Identified:
1. No `approval_count` tracking on Application
2. No `required_approvals` field (hardcoded to 2?)
3. No easy way to query "applications with 1 approval"
4. No denormalized vote summary for performance
5. Missing notification tracking
6. Missing approval order/sequence

---

## 🎯 Proposed Schema Enhancements

### Option 1: Minimal Changes (Recommended)

**Enhance `Application` model with approval tracking:**

```python
class Application(BaseDocument):
    # ... existing fields ...

    # NEW: Two-Board Approval Workflow
    approval_count: int = Field(default=0, ge=0, description="Number of approvals received")
    required_approvals: int = Field(default=2, ge=1, le=5, description="Required approvals")
    rejection_count: int = Field(default=0, ge=0, description="Number of rejections received")

    # Denormalized for performance
    board_votes: List[UUID] = Field(default_factory=list, description="Board member IDs who voted")
    approver_ids: List[UUID] = Field(default_factory=list, description="Board member IDs who approved")
    rejector_ids: List[UUID] = Field(default_factory=list, description="Board member IDs who rejected")

    # Timestamps
    first_approval_at: Optional[datetime] = Field(None, description="First approval timestamp")
    fully_approved_at: Optional[datetime] = Field(None, description="Full approval timestamp (2+ votes)")

    # Workflow state
    pending_board_review: bool = Field(default=False, description="Awaiting board votes")
    board_review_started_at: Optional[datetime] = Field(None, description="When first board member reviewed")
```

**Keep `Approval` model mostly unchanged, add sequence:**

```python
class Approval(BaseDocument):
    # ... existing fields ...

    # NEW: Sequence tracking
    sequence: int = Field(default=0, ge=0, description="Vote sequence (1st, 2nd, 3rd...)")
    vote_cast_at: datetime = Field(default_factory=datetime.utcnow, description="When vote was cast")

    # NEW: Notification tracking
    notification_sent: bool = Field(default=False, description="Email notification sent")
    notification_sent_at: Optional[datetime] = Field(None, description="Notification sent timestamp")
```

### Option 2: Full Redesign (More Complex)

Create new collections for better separation:

```python
class ApplicationVote(BaseDocument):
    """Individual board member vote"""
    application_id: UUID
    board_member_id: UUID
    vote: Literal["APPROVE", "REJECT", "ABSTAIN"]
    vote_cast_at: datetime
    notes: Optional[str]
    conditions: Optional[List[str]]

class ApplicationApprovalStatus(BaseDocument):
    """Aggregate approval status"""
    application_id: UUID
    total_votes: int
    approve_count: int
    reject_count: int
    abstain_count: int
    required_approvals: int
    status: Literal["PENDING", "APPROVED", "REJECTED"]
    updated_at: datetime
```

---

## 🏆 Recommended Approach: **Option 1 (Minimal Changes)**

### Rationale:
1. ✅ Leverages existing `approvals` collection
2. ✅ Minimal code changes needed
3. ✅ Denormalized fields improve query performance
4. ✅ Backward compatible with existing applications
5. ✅ Simpler to implement and test

---

## 📊 Workflow State Machine

### Application Status Flow:

```
DRAFT
  ↓ (user submits)
SUBMITTED
  ↓ (admin/system triggers review)
UNDER_REVIEW (pending_board_review = true)
  ↓
  ├─→ (1st approval) → UNDER_REVIEW (approval_count = 1)
  │     ↓
  │     └─→ (2nd approval) → APPROVED (approval_count = 2, fully_approved_at set)
  │
  └─→ (any rejection) → REJECTED (rejection_count ≥ 1)
```

### Approval Status Flow:

```
PENDING
  ↓
  ├─→ APPROVED (approver votes yes)
  ├─→ REJECTED (approver votes no)
  └─→ INVALIDATED (approval cancelled/expired)
```

---

## 🔄 Approval Workflow Logic

### Submitting Application for Review:

```python
def submit_for_review(application_id: UUID):
    application = get_application(application_id)

    # Update status
    application.status = ApplicationStatus.UNDER_REVIEW
    application.pending_board_review = True
    application.board_review_started_at = datetime.utcnow()

    # Create pending approvals for all board members
    board_members = get_all_board_members()
    for member in board_members:
        create_approval(
            application_id=application_id,
            approver_id=member.id,
            status=ApprovalStatus.PENDING
        )

    # Notify board members
    send_board_notification(application_id, board_members)
```

### Casting a Vote:

```python
def cast_vote(application_id: UUID, board_member_id: UUID, action: ApprovalAction, notes: str):
    application = get_application(application_id)

    # Check if already voted
    if board_member_id in application.board_votes:
        raise ValueError("Board member already voted on this application")

    # Get the pending approval
    approval = get_approval(application_id, board_member_id)

    if action == ApprovalAction.APPROVE:
        # Mark approval
        approval.status = ApprovalStatus.APPROVED
        approval.approved_at = datetime.utcnow()
        approval.sequence = application.approval_count + 1

        # Update application
        application.approval_count += 1
        application.approver_ids.append(board_member_id)
        application.board_votes.append(board_member_id)

        if application.approval_count == 1:
            application.first_approval_at = datetime.utcnow()

        # Check if fully approved
        if application.approval_count >= application.required_approvals:
            application.status = ApplicationStatus.APPROVED
            application.fully_approved_at = datetime.utcnow()
            application.pending_board_review = False

            # Activate membership
            activate_membership(application.user_id)

            # Send approval email
            send_approval_email(application.user_id)

    elif action == ApprovalAction.REJECT:
        # Mark rejection
        approval.status = ApprovalStatus.REJECTED
        approval.rejected_at = datetime.utcnow()
        approval.sequence = len(application.board_votes) + 1

        # Update application
        application.rejection_count += 1
        application.rejector_ids.append(board_member_id)
        application.board_votes.append(board_member_id)

        # Single rejection = application rejected
        application.status = ApplicationStatus.REJECTED
        application.pending_board_review = False
        application.rejected_at = datetime.utcnow()
        application.rejected_by = board_member_id

        # Send rejection email
        send_rejection_email(application.user_id, notes)

    approval.notes = notes
    approval.vote_cast_at = datetime.utcnow()

    save(approval)
    save(application)
```

---

## 📋 Database Queries Needed

### 1. Get Pending Applications for Board Member:

```python
def get_pending_applications(board_member_id: UUID) -> List[Application]:
    """Get applications awaiting this board member's vote"""

    # Find all pending approvals for this board member
    pending_approvals = db.query(Approval).filter(
        Approval.approver_id == board_member_id,
        Approval.status == ApprovalStatus.PENDING,
        Approval.is_active == True
    ).all()

    application_ids = [a.application_id for a in pending_approvals]

    # Get corresponding applications
    applications = db.query(Application).filter(
        Application.id.in_(application_ids),
        Application.status == ApplicationStatus.UNDER_REVIEW,
        Application.pending_board_review == True
    ).all()

    return applications
```

### 2. Get Applications with 1 Approval (Needs 1 More):

```python
def get_applications_needing_one_more_vote() -> List[Application]:
    """Get applications that have 1 approval and need 1 more"""

    return db.query(Application).filter(
        Application.status == ApplicationStatus.UNDER_REVIEW,
        Application.approval_count == 1,
        Application.required_approvals == 2,
        Application.pending_board_review == True
    ).all()
```

### 3. Get Vote History for Application:

```python
def get_vote_history(application_id: UUID) -> List[Approval]:
    """Get all votes for an application, ordered by sequence"""

    return db.query(Approval).filter(
        Approval.application_id == application_id
    ).order_by(Approval.sequence).all()
```

### 4. Board Member Voting Stats:

```python
def get_board_member_stats(board_member_id: UUID) -> dict:
    """Get voting statistics for a board member"""

    approvals = db.query(Approval).filter(
        Approval.approver_id == board_member_id
    ).all()

    return {
        "total_votes": len(approvals),
        "approved": len([a for a in approvals if a.status == ApprovalStatus.APPROVED]),
        "rejected": len([a for a in approvals if a.status == ApprovalStatus.REJECTED]),
        "pending": len([a for a in approvals if a.status == ApprovalStatus.PENDING]),
    }
```

---

## 🔐 Business Rules

### Voting Rules:
1. ✅ Board member can only vote once per application
2. ✅ Cannot change vote after casting
3. ✅ 2 approvals required for application approval
4. ✅ 1 rejection immediately rejects application
5. ✅ Board members cannot vote on their own applications (if applicable)

### Notification Rules:
1. ✅ Notify all board members when application submitted
2. ✅ Notify applicant when first approval received
3. ✅ Notify applicant when fully approved
4. ✅ Notify applicant when rejected
5. ✅ Notify remaining board members after first approval

### Edge Cases:
1. **What if both board members reject?**
   - Application = REJECTED after first rejection

2. **What if board member becomes inactive?**
   - Mark their pending approvals as INVALIDATED
   - Create new pending approval for replacement board member

3. **What if application is withdrawn?**
   - Set status = WITHDRAWN
   - Mark all pending approvals as INVALIDATED

---

## 🧪 Test Scenarios

### Happy Path:
1. ✅ User submits application
2. ✅ Application goes to UNDER_REVIEW
3. ✅ 2 pending approvals created (one per board member)
4. ✅ Board member 1 approves → approval_count = 1
5. ✅ Board member 2 approves → approval_count = 2, status = APPROVED

### Rejection Path:
1. ✅ User submits application
2. ✅ Board member 1 rejects → status = REJECTED immediately

### Concurrent Voting:
1. ✅ Both board members vote at the same time
2. ✅ System handles race conditions correctly
3. ✅ Final approval_count = 2 (no duplicates)

---

## 📈 Performance Considerations

### Indexes Needed:

```python
# Application indexes
application.create_index("status")
application.create_index("pending_board_review")
application.create_index("approval_count")
application.create_index(["status", "pending_board_review", "approval_count"])

# Approval indexes
approval.create_index("application_id")
approval.create_index("approver_id")
approval.create_index(["approver_id", "status"])
approval.create_index(["application_id", "sequence"])
```

### Denormalization Benefits:
- `approval_count` on Application → avoids COUNT query
- `approver_ids` list → avoids JOIN
- `board_votes` list → quick duplicate check

---

## ✅ Implementation Checklist

### Phase 1: Schema Updates
- [ ] Add new fields to `Application` model
- [ ] Add new fields to `Approval` model
- [ ] Create database migration script
- [ ] Add indexes for performance

### Phase 2: Business Logic
- [ ] Implement `submit_for_review()` function
- [ ] Implement `cast_vote()` function
- [ ] Implement vote validation logic
- [ ] Implement approval count tracking

### Phase 3: API Endpoints
- [ ] GET `/api/board/applications/pending` - Get pending applications
- [ ] POST `/api/board/applications/{id}/vote` - Cast vote
- [ ] GET `/api/board/applications/{id}/votes` - Get vote history
- [ ] GET `/api/board/stats` - Get voting statistics

### Phase 4: Testing
- [ ] Unit tests for vote logic
- [ ] Integration tests for workflow
- [ ] Test concurrent voting scenarios
- [ ] Test edge cases (withdrawals, invalidations)

---

## 🎯 Next Steps

1. **Review this schema design with stakeholders**
2. **Implement schema changes in `backend/models/schemas.py`**
3. **Build API endpoints for board voting**
4. **Create board member dashboard UI**
5. **Add email notifications**
6. **Test end-to-end workflow**

---

**Schema Design Status:** ✅ Complete
**Ready for Implementation:** Yes
**Next Task:** Implement schema changes

---

*End of Two-Board Approval Schema Design*
