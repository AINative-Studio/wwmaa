import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface SearchErrorProps {
  message: string;
  onRetry?: () => void;
}

export function SearchError({ message, onRetry }: SearchErrorProps) {
  const getErrorTitle = (errorMessage: string): string => {
    if (errorMessage.toLowerCase().includes('timeout')) {
      return 'Search Timeout';
    }
    if (errorMessage.toLowerCase().includes('network')) {
      return 'Network Error';
    }
    if (errorMessage.toLowerCase().includes('server')) {
      return 'Server Error';
    }
    return 'Search Error';
  };

  const getSuggestions = (errorMessage: string): string[] => {
    const suggestions: string[] = [];

    if (errorMessage.toLowerCase().includes('timeout')) {
      suggestions.push('Try a simpler search query');
      suggestions.push('Check your internet connection');
    } else if (errorMessage.toLowerCase().includes('network')) {
      suggestions.push('Check your internet connection');
      suggestions.push('Try again in a moment');
    } else if (errorMessage.toLowerCase().includes('server')) {
      suggestions.push('Our servers may be experiencing issues');
      suggestions.push('Please try again later');
    } else {
      suggestions.push('Try a different search query');
      suggestions.push('Check your spelling');
    }

    return suggestions;
  };

  const title = getErrorTitle(message);
  const suggestions = getSuggestions(message);

  return (
    <div className="space-y-4">
      <Alert variant="destructive">
        <AlertTriangle className="h-5 w-5" />
        <AlertTitle className="text-lg font-semibold">{title}</AlertTitle>
        <AlertDescription className="mt-2">
          <p className="mb-3">{message}</p>
          {suggestions.length > 0 && (
            <div className="mt-3">
              <p className="font-medium mb-2">Suggestions:</p>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </AlertDescription>
      </Alert>

      {onRetry && (
        <div className="flex justify-center">
          <Button onClick={onRetry} variant="outline" size="lg">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      )}
    </div>
  );
}
