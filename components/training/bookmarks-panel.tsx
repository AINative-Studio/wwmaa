"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Bookmark, Plus, Edit2, Trash2, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/use-toast";

interface BookmarksPanelProps {
  sessionId: string;
  userId: string;
}

interface Bookmark {
  id: string;
  sessionId: string;
  userId: string;
  timestamp: number;
  note: string;
  createdAt: string;
  updatedAt: string;
}

export function BookmarksPanel({ sessionId, userId }: BookmarksPanelProps) {
  const { toast } = useToast();
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editingBookmark, setEditingBookmark] = useState<Bookmark | null>(null);
  const [deletingBookmark, setDeletingBookmark] = useState<Bookmark | null>(null);
  const [bookmarkNote, setBookmarkNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) {
      return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    }
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  // Load bookmarks
  const loadBookmarks = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/training/${sessionId}/bookmarks?userId=${userId}`
      );

      if (!response.ok) {
        throw new Error("Failed to load bookmarks");
      }

      const data = await response.json();
      setBookmarks(data.bookmarks || []);
    } catch (error) {
      console.error("Error loading bookmarks:", error);
      toast({
        title: "Error",
        description: "Failed to load bookmarks",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId, userId, toast]);

  // Load bookmarks on mount
  useEffect(() => {
    loadBookmarks();
  }, [loadBookmarks]);

  // Listen for video time updates
  useEffect(() => {
    const handleTimeUpdate = (e: CustomEvent<{ currentTime: number }>) => {
      setCurrentTime(e.detail.currentTime);
    };

    window.addEventListener(
      "vod-time-update" as any,
      handleTimeUpdate as EventListener
    );
    return () =>
      window.removeEventListener(
        "vod-time-update" as any,
        handleTimeUpdate as EventListener
      );
  }, []);

  // Create bookmark
  const createBookmark = async () => {
    setSubmitting(true);
    try {
      const response = await fetch(`/api/training/${sessionId}/bookmarks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          userId,
          timestamp: Math.floor(currentTime),
          note: bookmarkNote.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create bookmark");
      }

      const data = await response.json();
      setBookmarks((prev) => [...prev, data.bookmark].sort((a, b) => a.timestamp - b.timestamp));
      setBookmarkNote("");
      setIsAddDialogOpen(false);

      toast({
        title: "Bookmark Added",
        description: `Bookmark created at ${formatTime(currentTime)}`,
      });
    } catch (error) {
      console.error("Error creating bookmark:", error);
      toast({
        title: "Error",
        description: "Failed to create bookmark",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Update bookmark
  const updateBookmark = async () => {
    if (!editingBookmark) return;

    setSubmitting(true);
    try {
      const response = await fetch(
        `/api/training/${sessionId}/bookmarks/${editingBookmark.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            userId,
            note: bookmarkNote.trim(),
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update bookmark");
      }

      const data = await response.json();
      setBookmarks((prev) =>
        prev.map((b) => (b.id === editingBookmark.id ? data.bookmark : b))
      );
      setBookmarkNote("");
      setEditingBookmark(null);

      toast({
        title: "Bookmark Updated",
        description: "Your bookmark has been updated",
      });
    } catch (error) {
      console.error("Error updating bookmark:", error);
      toast({
        title: "Error",
        description: "Failed to update bookmark",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Delete bookmark
  const deleteBookmark = async () => {
    if (!deletingBookmark) return;

    setSubmitting(true);
    try {
      const response = await fetch(
        `/api/training/${sessionId}/bookmarks/${deletingBookmark.id}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ userId }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete bookmark");
      }

      setBookmarks((prev) => prev.filter((b) => b.id !== deletingBookmark.id));
      setDeletingBookmark(null);

      toast({
        title: "Bookmark Deleted",
        description: "Your bookmark has been removed",
      });
    } catch (error) {
      console.error("Error deleting bookmark:", error);
      toast({
        title: "Error",
        description: "Failed to delete bookmark",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Seek to bookmark
  const seekToBookmark = (timestamp: number) => {
    window.dispatchEvent(
      new CustomEvent("vod-seek-to", { detail: { time: timestamp } })
    );
  };

  // Open edit dialog
  const openEditDialog = (bookmark: Bookmark) => {
    setEditingBookmark(bookmark);
    setBookmarkNote(bookmark.note);
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Bookmark className="h-5 w-5" />
                Bookmarks
              </CardTitle>
              <CardDescription>
                Save important moments with notes
              </CardDescription>
            </div>
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Bookmark</DialogTitle>
                  <DialogDescription>
                    Create a bookmark at {formatTime(currentTime)}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Timestamp
                    </label>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                      <Clock className="h-4 w-4" />
                      {formatTime(currentTime)}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Note
                    </label>
                    <Textarea
                      placeholder="Add a note about this moment..."
                      value={bookmarkNote}
                      onChange={(e) => setBookmarkNote(e.target.value)}
                      rows={4}
                      className="resize-none"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setIsAddDialogOpen(false);
                      setBookmarkNote("");
                    }}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button onClick={createBookmark} disabled={submitting}>
                    {submitting ? "Adding..." : "Add Bookmark"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500 text-sm">Loading bookmarks...</div>
            </div>
          ) : bookmarks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Bookmark className="h-12 w-12 text-gray-300 dark:text-gray-600 mb-3" />
              <div className="text-gray-500 text-sm">
                No bookmarks yet
              </div>
              <div className="text-gray-400 text-xs mt-1">
                Click "Add" to save important moments
              </div>
            </div>
          ) : (
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {bookmarks.map((bookmark) => (
                  <div
                    key={bookmark.id}
                    className="p-3 rounded-lg border bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <button
                        onClick={() => seekToBookmark(bookmark.timestamp)}
                        className="flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        <Clock className="h-4 w-4" />
                        {formatTime(bookmark.timestamp)}
                      </button>
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 w-7 p-0"
                          onClick={() => openEditDialog(bookmark)}
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                          onClick={() => setDeletingBookmark(bookmark)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>
                    {bookmark.note && (
                      <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                        {bookmark.note}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog
        open={!!editingBookmark}
        onOpenChange={(open) => {
          if (!open) {
            setEditingBookmark(null);
            setBookmarkNote("");
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Bookmark</DialogTitle>
            <DialogDescription>
              Update your bookmark note
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Timestamp
              </label>
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                <Clock className="h-4 w-4" />
                {editingBookmark && formatTime(editingBookmark.timestamp)}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Note</label>
              <Textarea
                placeholder="Add a note about this moment..."
                value={bookmarkNote}
                onChange={(e) => setBookmarkNote(e.target.value)}
                rows={4}
                className="resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setEditingBookmark(null);
                setBookmarkNote("");
              }}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button onClick={updateBookmark} disabled={submitting}>
              {submitting ? "Updating..." : "Update Bookmark"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={!!deletingBookmark}
        onOpenChange={(open) => {
          if (!open) setDeletingBookmark(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Bookmark?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete your
              bookmark at{" "}
              {deletingBookmark && formatTime(deletingBookmark.timestamp)}.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={submitting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={deleteBookmark}
              disabled={submitting}
              className="bg-red-600 hover:bg-red-700"
            >
              {submitting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
