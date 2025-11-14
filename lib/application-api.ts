import {
  MembershipApplication,
  ApplicationApproval,
  ApplicationTimeline
} from './types';

const ENDPOINTS = {
  applicationById: (id: string) => `/api/membership-applications/${id}`,
  applicationByEmail: (email: string) => `/api/membership-applications/lookup?email=${encodeURIComponent(email)}`,
  applicationApprovals: (id: string) => `/api/membership-applications/${id}/approvals`,
  applicationTimeline: (id: string) => `/api/membership-applications/${id}/timeline`,
};

export const applicationApi = {
  /**
   * Fetch application by ID
   */
  async getApplicationById(id: string): Promise<MembershipApplication | null> {
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
