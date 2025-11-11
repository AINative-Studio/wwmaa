'use client';

import { useState } from 'react';
import Image from 'next/image';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { Dialog, DialogContent, DialogClose } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { SearchImage } from './types';
import { cn } from '@/lib/utils';

interface ImageGalleryProps {
  images: SearchImage[];
}

export function ImageGallery({ images }: ImageGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [imageLoadStates, setImageLoadStates] = useState<Record<string, boolean>>({});

  const handleImageLoad = (imageId: string) => {
    setImageLoadStates((prev) => ({ ...prev, [imageId]: true }));
  };

  const openLightbox = (index: number) => {
    setSelectedIndex(index);
  };

  const closeLightbox = () => {
    setSelectedIndex(null);
  };

  const navigatePrevious = () => {
    if (selectedIndex !== null && selectedIndex > 0) {
      setSelectedIndex(selectedIndex - 1);
    }
  };

  const navigateNext = () => {
    if (selectedIndex !== null && selectedIndex < images.length - 1) {
      setSelectedIndex(selectedIndex + 1);
    }
  };

  const selectedImage = selectedIndex !== null ? images[selectedIndex] : null;

  return (
    <>
      {/* Image Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {images.map((image, index) => (
          <button
            key={image.id}
            onClick={() => openLightbox(index)}
            className="group relative aspect-square overflow-hidden rounded-lg bg-muted hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <Image
              src={image.thumbnail || image.url}
              alt={image.alt}
              fill
              sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
              className={cn(
                'object-cover transition-transform group-hover:scale-105',
                !imageLoadStates[image.id] && 'opacity-0'
              )}
              onLoad={() => handleImageLoad(image.id)}
            />
            {!imageLoadStates[image.id] && (
              <div className="absolute inset-0 animate-pulse bg-muted" />
            )}
            {image.caption && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <p className="text-xs text-white line-clamp-2">{image.caption}</p>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Lightbox */}
      <Dialog open={selectedIndex !== null} onOpenChange={closeLightbox}>
        <DialogContent className="max-w-7xl w-full h-[90vh] p-0">
          <div className="relative w-full h-full flex items-center justify-center bg-black/95">
            {/* Close Button */}
            <DialogClose className="absolute top-4 right-4 z-50 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
              <X className="h-6 w-6 text-white" />
              <span className="sr-only">Close</span>
            </DialogClose>

            {/* Previous Button */}
            {selectedIndex !== null && selectedIndex > 0 && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute left-4 top-1/2 -translate-y-1/2 z-50 h-12 w-12 rounded-full bg-black/50 hover:bg-black/70 text-white"
                onClick={navigatePrevious}
              >
                <ChevronLeft className="h-8 w-8" />
                <span className="sr-only">Previous image</span>
              </Button>
            )}

            {/* Next Button */}
            {selectedIndex !== null && selectedIndex < images.length - 1 && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-4 top-1/2 -translate-y-1/2 z-50 h-12 w-12 rounded-full bg-black/50 hover:bg-black/70 text-white"
                onClick={navigateNext}
              >
                <ChevronRight className="h-8 w-8" />
                <span className="sr-only">Next image</span>
              </Button>
            )}

            {/* Image */}
            {selectedImage && (
              <div className="relative w-full h-full flex flex-col items-center justify-center p-16">
                <div className="relative w-full h-full">
                  <Image
                    src={selectedImage.url}
                    alt={selectedImage.alt}
                    fill
                    sizes="90vw"
                    className="object-contain"
                    priority
                  />
                </div>
                {selectedImage.caption && (
                  <div className="absolute bottom-8 left-1/2 -translate-x-1/2 max-w-2xl">
                    <p className="text-white text-center px-4 py-2 bg-black/60 rounded-lg">
                      {selectedImage.caption}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Image Counter */}
            {selectedIndex !== null && (
              <div className="absolute top-4 left-4 z-50">
                <div className="bg-black/60 text-white px-3 py-1 rounded-full text-sm">
                  {selectedIndex + 1} / {images.length}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
