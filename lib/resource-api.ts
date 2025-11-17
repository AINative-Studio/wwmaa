import { Resource, ResourceListResponse, ResourceFilters, ResourceCategory } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://athletic-curiosity-production.up.railway.app";

interface GetResourcesParams extends ResourceFilters {
  page?: number;
  page_size?: number;
}

function getToken(): string | null {
  if (typeof document === 'undefined') return null;
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'access_token') {
      return value;
    }
  }
  return null;
}

export const resourceApi = {
  async getResources(params: GetResourcesParams = {}): Promise<ResourceListResponse> {
    const queryParams = new URLSearchParams();

    if (params.category) queryParams.append("category", params.category);
    if (params.status) queryParams.append("status", params.status);
    if (params.featured_only) queryParams.append("featured_only", "true");
    if (params.discipline) queryParams.append("discipline", params.discipline);

    queryParams.append("page", String(params.page ?? 1));
    queryParams.append("page_size", String(params.page_size ?? 20));

    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/api/resources?${queryParams.toString()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      },
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch resources: ${response.statusText}`);
    }

    return response.json();
  },

  async getResource(id: string): Promise<Resource | null> {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/api/resources/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      },
      credentials: "include",
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to fetch resource: ${response.statusText}`);
    }

    return response.json();
  },

  async trackView(resourceId: string): Promise<void> {
    const token = getToken();
    try {
      await fetch(`${API_BASE_URL}/api/resources/${resourceId}/track-view`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        },
        credentials: "include",
      });
    } catch (error) {
      console.error("Failed to track resource view:", error);
    }
  },

  async trackDownload(resourceId: string): Promise<void> {
    const token = getToken();
    try {
      await fetch(`${API_BASE_URL}/api/resources/${resourceId}/track-download`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        },
        credentials: "include",
      });
    } catch (error) {
      console.error("Failed to track resource download:", error);
    }
  },

  getCategoryLabel(category: ResourceCategory): string {
    const labels: Record<ResourceCategory, string> = {
      video: "Video",
      document: "Document",
      pdf: "PDF",
      slide: "Presentation",
      article: "Article",
      recording: "Recording",
      certification: "Certification",
      other: "Other",
    };
    return labels[category] || category;
  },

  getCategoryIcon(category: ResourceCategory): string {
    const icons: Record<ResourceCategory, string> = {
      video: "M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z",
      document: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
      pdf: "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z",
      slide: "M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01",
      article: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
      recording: "M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z",
      certification: "M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z",
      other: "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z",
    };
    return icons[category] || icons.other;
  },

  formatFileSize(bytes?: number): string {
    if (!bytes) return "Unknown size";
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  },

  formatDuration(seconds?: number): string {
    if (!seconds) return "";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  },
};
