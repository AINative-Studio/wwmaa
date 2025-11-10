import {
  MembershipApplication,
  ApplicationApproval,
  ApplicationTimeline
} from './types';

const MODE = process.env.NEXT_PUBLIC_API_MODE ?? 'mock';

const ENDPOINTS = {
  applicationById: (id: string) => `/api/membership-applications/${id}`,
  applicationByEmail: (email: string) => `/api/membership-applications/lookup?email=${encodeURIComponent(email)}`,
  applicationApprovals: (id: string) => `/api/membership-applications/${id}/approvals`,
  applicationTimeline: (id: string) => `/api/membership-applications/${id}/timeline`,
};

// Mock data for development
const mockApplication: MembershipApplication = {
  id: 'app_123456',
  applicant_email: 'john.doe@example.com',
  applicant_name: 'John Doe',
  applicant_phone: '+1-555-0100',
  applicant_address: '123 Main St, Boston, MA 02101',
  martial_arts_style: 'Shotokan Karate',
  years_experience: 8,
  current_rank: '2nd Dan Black Belt',
  instructor_name: 'Sensei Mike Wilson',
  school_affiliation: 'Boston Karate Academy',
  reason_for_joining: 'I want to connect with other martial artists and expand my knowledge across different disciplines.',
  status: 'UNDER_REVIEW',
  submitted_at: '2025-01-15T10:30:00Z',
  first_approval_at: '2025-01-16T14:20:00Z',
  approval_count: 1,
  required_approvals: 2,
  approved_by: ['Board Member Sarah Chen'],
  created_at: '2025-01-15T10:00:00Z',
  updated_at: '2025-01-16T14:20:00Z',
};

const mockApprovals: ApplicationApproval[] = [
  {
    id: 'approval_1',
    application_id: 'app_123456',
    board_member_id: 'user_board_1',
    board_member_name: 'Sarah Chen',
    approved_at: '2025-01-16T14:20:00Z',
    comments: 'Strong martial arts background and excellent references.',
  },
];

const mockTimeline: ApplicationTimeline[] = [
  {
    event: 'Application Submitted',
    timestamp: '2025-01-15T10:30:00Z',
    description: 'Application submitted for membership review',
    actor: 'John Doe',
  },
  {
    event: 'Under Review',
    timestamp: '2025-01-16T09:00:00Z',
    description: 'Application moved to review status',
  },
  {
    event: 'First Approval Received',
    timestamp: '2025-01-16T14:20:00Z',
    description: 'Application approved by board member (1 of 2 required)',
    actor: 'Sarah Chen',
  },
];

export const applicationApi = {
  /**
   * Fetch application by ID
   */
  async getApplicationById(id: string): Promise<MembershipApplication | null> {
    if (MODE === 'mock') {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 300));
      return id === mockApplication.id ? mockApplication : null;
    }

    try {
      const response = await fetch(ENDPOINTS.applicationById(id), {
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch application');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching application:', error);
      throw error;
    }
  },

  /**
   * Fetch application by email
   */
  async getApplicationByEmail(email: string): Promise<MembershipApplication | null> {
    if (MODE === 'mock') {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 300));
      return email === mockApplication.applicant_email ? mockApplication : null;
    }

    try {
      const response = await fetch(ENDPOINTS.applicationByEmail(email), {
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch application');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching application by email:', error);
      throw error;
    }
  },

  /**
   * Fetch application approvals
   */
  async getApplicationApprovals(applicationId: string): Promise<ApplicationApproval[]> {
    if (MODE === 'mock') {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 200));
      return applicationId === mockApplication.id ? mockApprovals : [];
    }

    try {
      const response = await fetch(ENDPOINTS.applicationApprovals(applicationId), {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch approvals');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching approvals:', error);
      throw error;
    }
  },

  /**
   * Fetch application timeline
   */
  async getApplicationTimeline(applicationId: string): Promise<ApplicationTimeline[]> {
    if (MODE === 'mock') {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 200));
      return applicationId === mockApplication.id ? mockTimeline : [];
    }

    try {
      const response = await fetch(ENDPOINTS.applicationTimeline(applicationId), {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch timeline');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching timeline:', error);
      throw error;
    }
  },
};
