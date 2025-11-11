'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { SearchResults } from '@/components/search/search-results';
import { SearchResultsSkeleton } from '@/components/search/search-results-skeleton';
import { SearchError } from '@/components/search/search-error';
import { SearchResult } from '@/components/search/types';

function SearchPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 500);

    return () => clearTimeout(timer);
  }, [query]);

  // Perform search when debounced query changes
  useEffect(() => {
    if (debouncedQuery.trim()) {
      performSearch(debouncedQuery);
    } else {
      setSearchResult(null);
    }
  }, [debouncedQuery]);

  // Update query from URL params
  useEffect(() => {
    const urlQuery = searchParams.get('q');
    if (urlQuery && urlQuery !== query) {
      setQuery(urlQuery);
    }
  }, [searchParams]);

  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      // Update URL with search query
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`, {
        scroll: false,
      });

      // Call search API
      const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`);

      if (!response.ok) {
        if (response.status === 408) {
          throw new Error('Search timed out. Please try again.');
        } else if (response.status >= 500) {
          throw new Error('Server error. Please try again later.');
        } else {
          throw new Error('Failed to perform search. Please try again.');
        }
      }

      const data = await response.json();
      setSearchResult(data);
    } catch (err) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      performSearch(query);
    }
  };

  const handleRetry = () => {
    if (query.trim()) {
      performSearch(query);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Search Header */}
      <div className="max-w-4xl mx-auto mb-8">
        <h1 className="text-4xl font-bold mb-6 text-center">Search WWMAA</h1>

        {/* Search Input */}
        <form onSubmit={handleSearch} className="relative">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Ask anything about martial arts..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-10 pr-4 h-12 text-lg"
                autoFocus
              />
            </div>
            <Button type="submit" size="lg" disabled={!query.trim() || isLoading}>
              Search
            </Button>
          </div>
        </form>
      </div>

      {/* Search Results */}
      <div className="max-w-4xl mx-auto">
        {isLoading && <SearchResultsSkeleton />}

        {error && !isLoading && (
          <SearchError message={error} onRetry={handleRetry} />
        )}

        {searchResult && !isLoading && !error && (
          <SearchResults result={searchResult} />
        )}

        {!query.trim() && !isLoading && !error && !searchResult && (
          <div className="text-center py-12">
            <Search className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
            <p className="text-xl text-muted-foreground">
              Start typing to search our knowledge base
            </p>
          </div>
        )}

        {query.trim() && !isLoading && !error && !searchResult && debouncedQuery === query && (
          <div className="text-center py-12">
            <p className="text-xl text-muted-foreground">
              No results found for "{query}"
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Try different keywords or check your spelling
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchResultsSkeleton />}>
      <SearchPageContent />
    </Suspense>
  );
}
