# Frontend Integration Guide - Resources API

## Quick Start: Update ResourcesClient.tsx

Here's how to update the frontend to consume the new Resources API.

### Current State (Static Mock)
```typescript
// app/resources/ResourcesClient.tsx (CURRENT - TO BE REPLACED)
"use client";
export default function ResourcesClient() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Training Resources</h1>
      <p className="text-muted-foreground">Coming soon...</p>
    </div>
  );
}
```

### Updated Implementation (Dynamic API)

```typescript
// app/resources/ResourcesClient.tsx (NEW IMPLEMENTATION)
"use client";

import { useState, useEffect } from 'react';
import { ResourceCard } from '@/components/ResourceCard';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth-context'; // Adjust to your auth implementation

interface Resource {
  id: string;
  title: string;
  description: string | null;
  category: string;
  tags: string[];
  file_url: string | null;
  external_url: string | null;
  visibility: string;
  status: string;
  published_at: string | null;
  is_featured: boolean;
  view_count: number;
  download_count: number;
}

interface ResourcesResponse {
  resources: Resource[];
  total: number;
  page: number;
  page_size: number;
}

export default function ResourcesClient() {
  const { accessToken } = useAuth();
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<string | null>(null);

  useEffect(() => {
    fetchResources();
  }, [page, category]);

  const fetchResources = async () => {
    try {
      setLoading(true);
      setError(null);

      // Build query params
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', '20');
      if (category) params.append('category', category);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/resources?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ResourcesResponse = await response.json();
      setResources(data.resources);
      setTotal(data.total);
    } catch (err) {
      console.error('Error fetching resources:', err);
      setError('Failed to load resources. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const trackView = async (resourceId: string) => {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/resources/${resourceId}/track-view`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
    } catch (err) {
      console.error('Error tracking view:', err);
      // Non-critical, don't show error to user
    }
  };

  const trackDownload = async (resourceId: string) => {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/resources/${resourceId}/track-download`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
    } catch (err) {
      console.error('Error tracking download:', err);
      // Non-critical, don't show error to user
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-lg bg-destructive/10 p-4 text-destructive">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Training Resources</h1>

        {/* Category Filter */}
        <select
          value={category || ''}
          onChange={(e) => {
            setCategory(e.target.value || null);
            setPage(1);
          }}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="">All Categories</option>
          <option value="video">Videos</option>
          <option value="document">Documents</option>
          <option value="pdf">PDFs</option>
          <option value="article">Articles</option>
        </select>
      </div>

      {/* Empty State */}
      {resources.length === 0 ? (
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-muted-foreground mb-2">
            No resources available
          </h2>
          <p className="text-sm text-muted-foreground">
            Check back later for new training materials.
          </p>
        </div>
      ) : (
        <>
          {/* Resources Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {resources.map((resource) => (
              <ResourceCard
                key={resource.id}
                resource={resource}
                onView={() => trackView(resource.id)}
                onDownload={() => trackDownload(resource.id)}
              />
            ))}
          </div>

          {/* Pagination */}
          {total > 20 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border rounded-lg disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-4 py-2">
                Page {page} of {Math.ceil(total / 20)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(total / 20)}
                className="px-4 py-2 border rounded-lg disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}

          {/* Total Count */}
          <p className="text-center text-sm text-muted-foreground mt-4">
            Showing {resources.length} of {total} resources
          </p>
        </>
      )}
    </div>
  );
}
```

### Create ResourceCard Component

```typescript
// components/ResourceCard.tsx (NEW FILE)
import { ExternalLink, Download, Eye } from 'lucide-react';

interface ResourceCardProps {
  resource: {
    id: string;
    title: string;
    description: string | null;
    category: string;
    tags: string[];
    file_url: string | null;
    external_url: string | null;
    is_featured: boolean;
    view_count: number;
    download_count: number;
  };
  onView: () => void;
  onDownload: () => void;
}

export function ResourceCard({ resource, onView, onDownload }: ResourceCardProps) {
  const handleOpen = () => {
    onView();
    const url = resource.external_url || resource.file_url;
    if (url) {
      window.open(url, '_blank');
    }
  };

  const handleDownload = () => {
    onDownload();
    if (resource.file_url) {
      window.open(resource.file_url, '_blank');
    }
  };

  return (
    <div className="border rounded-lg p-6 hover:shadow-lg transition-shadow">
      {/* Featured Badge */}
      {resource.is_featured && (
        <span className="inline-block bg-primary text-primary-foreground text-xs px-2 py-1 rounded mb-2">
          Featured
        </span>
      )}

      {/* Title */}
      <h3 className="text-xl font-semibold mb-2">{resource.title}</h3>

      {/* Category Badge */}
      <span className="inline-block bg-secondary text-secondary-foreground text-xs px-2 py-1 rounded mb-3">
        {resource.category}
      </span>

      {/* Description */}
      {resource.description && (
        <p className="text-muted-foreground text-sm mb-4 line-clamp-3">
          {resource.description}
        </p>
      )}

      {/* Tags */}
      {resource.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {resource.tags.map((tag) => (
            <span
              key={tag}
              className="text-xs bg-muted px-2 py-1 rounded"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleOpen}
          className="flex items-center gap-2 text-primary hover:underline"
        >
          <ExternalLink className="h-4 w-4" />
          View
        </button>

        {resource.file_url && (
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 text-primary hover:underline"
          >
            <Download className="h-4 w-4" />
            Download
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 mt-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <Eye className="h-3 w-3" />
          {resource.view_count} views
        </span>
        <span className="flex items-center gap-1">
          <Download className="h-3 w-3" />
          {resource.download_count} downloads
        </span>
      </div>
    </div>
  );
}
```

---

## API Usage Examples

### 1. Fetch All Resources
```typescript
const response = await fetch('/api/resources', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const data = await response.json();
// { resources: [...], total: 10, page: 1, page_size: 20 }
```

### 2. Filter by Category
```typescript
const response = await fetch('/api/resources?category=video', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

### 3. Featured Resources Only
```typescript
const response = await fetch('/api/resources?featured_only=true', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

### 4. Pagination
```typescript
const response = await fetch('/api/resources?page=2&page_size=10', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

### 5. Track View
```typescript
await fetch(`/api/resources/${resourceId}/track-view`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

### 6. Track Download
```typescript
await fetch(`/api/resources/${resourceId}/track-download`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

---

## Error Handling

```typescript
try {
  const response = await fetch('/api/resources', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Redirect to login
      router.push('/login');
    } else if (response.status === 403) {
      // Show permission error
      setError('You do not have permission to view these resources');
    } else {
      // Generic error
      setError('Failed to load resources');
    }
    return;
  }

  const data = await response.json();
  setResources(data.resources);
} catch (err) {
  console.error('Error fetching resources:', err);
  setError('Network error. Please check your connection.');
}
```

---

## Environment Variables

Ensure these are set in your `.env.local` (frontend):

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
# or in production:
# NEXT_PUBLIC_API_URL=https://api.wwmaa.com
```

---

## Testing

### Manual Testing Steps

1. **Login** as a student/member
2. **Navigate** to `/resources`
3. **Verify**:
   - Resources load correctly (or empty state shows)
   - Filtering by category works
   - Pagination works (if >20 resources)
   - View tracking increments when clicking "View"
   - Download tracking increments when clicking "Download"
4. **Login** as instructor/admin
5. **Verify**:
   - Can see draft resources (if any)
   - Can see all resource categories

### Integration Test

```typescript
// __tests__/resources.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResourcesClient from '@/app/resources/ResourcesClient';

// Mock fetch
global.fetch = jest.fn();

describe('ResourcesClient', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('displays resources when API returns data', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        resources: [
          {
            id: '1',
            title: 'BJJ Fundamentals',
            description: 'Learn the basics',
            category: 'video',
            tags: ['bjj', 'beginner'],
            is_featured: true,
            view_count: 100,
            download_count: 50
          }
        ],
        total: 1,
        page: 1,
        page_size: 20
      })
    });

    render(<ResourcesClient />);

    await waitFor(() => {
      expect(screen.getByText('BJJ Fundamentals')).toBeInTheDocument();
    });
  });

  it('displays empty state when no resources', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        resources: [],
        total: 0,
        page: 1,
        page_size: 20
      })
    });

    render(<ResourcesClient />);

    await waitFor(() => {
      expect(screen.getByText('No resources available')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<ResourcesClient />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load resources/i)).toBeInTheDocument();
    });
  });
});
```

---

## Next Steps

1. **Update ResourcesClient.tsx** with the new implementation
2. **Create ResourceCard.tsx** component
3. **Add environment variable** for API URL
4. **Test locally** to ensure resources display correctly
5. **Deploy** to staging/production

---

## Support

If you encounter any issues:
1. Check browser console for errors
2. Verify authentication token is valid
3. Check API endpoint is accessible
4. Review network tab in DevTools
5. Ensure CORS is configured correctly on backend

The backend API is fully functional and ready for integration!
