"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowUpDown } from "lucide-react";

interface EventSortProps {
  sortBy: "date" | "price";
  sortOrder: "asc" | "desc";
  onSortChange: (sortBy: "date" | "price", sortOrder: "asc" | "desc") => void;
}

/**
 * EventSort Component
 *
 * Provides a dropdown for sorting events by date or price.
 */
export function EventSort({ sortBy, sortOrder, onSortChange }: EventSortProps) {
  const currentValue = `${sortBy}_${sortOrder}`;

  const handleChange = (value: string) => {
    const [newSortBy, newSortOrder] = value.split("_") as ["date" | "price", "asc" | "desc"];
    onSortChange(newSortBy, newSortOrder);
  };

  return (
    <div className="flex items-center gap-2">
      <ArrowUpDown className="w-4 h-4 text-gray-500" />
      <Select value={currentValue} onValueChange={handleChange}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Sort by..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="date_asc">Date: Earliest First</SelectItem>
          <SelectItem value="date_desc">Date: Latest First</SelectItem>
          <SelectItem value="price_asc">Price: Low to High</SelectItem>
          <SelectItem value="price_desc">Price: High to Low</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
