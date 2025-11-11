'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { SearchResult } from './types';
import { VideoEmbed } from './video-embed';
import { ImageGallery } from './image-gallery';
import { SearchFeedback } from './search-feedback';

interface SearchResultsProps {
  result: SearchResult;
}

export function SearchResults({ result }: SearchResultsProps) {
  const [isAnswerExpanded, setIsAnswerExpanded] = useState(true);

  return (
    <div className="space-y-6">
      {/* AI-Generated Answer */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-2xl">AI Answer</CardTitle>
              <CardDescription>
                Generated response based on our knowledge base
              </CardDescription>
            </div>
            <Collapsible open={isAnswerExpanded} onOpenChange={setIsAnswerExpanded}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm">
                  {isAnswerExpanded ? (
                    <>
                      <ChevronUp className="h-4 w-4 mr-2" />
                      Collapse
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-4 w-4 mr-2" />
                      Expand
                    </>
                  )}
                </Button>
              </CollapsibleTrigger>
            </Collapsible>
          </div>
        </CardHeader>
        <Collapsible open={isAnswerExpanded} onOpenChange={setIsAnswerExpanded}>
          <CollapsibleContent>
            <CardContent>
              <div className="prose prose-slate dark:prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ node, className, children, ...props }: any) {
                      const match = /language-(\w+)/.exec(className || '');
                      const isInline = !props['data-inline'];
                      return !isInline && match ? (
                        <SyntaxHighlighter
                          style={oneDark as any}
                          language={match[1]}
                          PreTag="div"
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                    a({ node, children, href, ...props }: any) {
                      return (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-primary hover:underline"
                          {...props}
                        >
                          {children}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      );
                    },
                  }}
                >
                  {result.answer}
                </ReactMarkdown>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      {/* Video Embed */}
      {result.videoUrl && (
        <Card>
          <CardHeader>
            <CardTitle>Related Video</CardTitle>
          </CardHeader>
          <CardContent>
            <VideoEmbed videoUrl={result.videoUrl} />
          </CardContent>
        </Card>
      )}

      {/* Image Gallery */}
      {result.images && result.images.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Related Images</CardTitle>
          </CardHeader>
          <CardContent>
            <ImageGallery images={result.images} />
          </CardContent>
        </Card>
      )}

      {/* Source Citations */}
      {result.sources && result.sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sources</CardTitle>
            <CardDescription>
              Information gathered from the following sources
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {result.sources.map((source) => (
                <a
                  key={source.id}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group"
                >
                  <Card className="h-full transition-all hover:shadow-md hover:border-primary">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-sm mb-1 line-clamp-2 group-hover:text-primary">
                            {source.title}
                          </h3>
                          {source.snippet && (
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {source.snippet}
                            </p>
                          )}
                        </div>
                        <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-primary flex-shrink-0" />
                      </div>
                    </CardContent>
                  </Card>
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Related Queries */}
      {result.relatedQueries && result.relatedQueries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Related Searches</CardTitle>
            <CardDescription>
              You might also be interested in
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {result.relatedQueries.map((query, index) => (
                <a key={index} href={`/search?q=${encodeURIComponent(query)}`}>
                  <Badge
                    variant="secondary"
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                  >
                    {query}
                  </Badge>
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Separator className="my-6" />

      {/* Feedback Section */}
      <SearchFeedback resultId={result.id} />
    </div>
  );
}
