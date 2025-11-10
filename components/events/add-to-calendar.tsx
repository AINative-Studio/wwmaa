"use client";

import { useState } from "react";
import { Calendar, Download, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface AddToCalendarProps {
  title: string;
  description?: string;
  startDatetime: string;
  endDatetime: string;
  location?: string;
  locationName?: string;
  city?: string;
  state?: string;
  isVirtual: boolean;
  virtualUrl?: string;
}

export function AddToCalendar({
  title,
  description,
  startDatetime,
  endDatetime,
  location,
  locationName,
  city,
  state,
  isVirtual,
  virtualUrl,
}: AddToCalendarProps) {
  const [isGenerating, setIsGenerating] = useState(false);

  // Format date for ICS format (YYYYMMDDTHHMMSSZ)
  const formatICSDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date
      .toISOString()
      .replace(/[-:]/g, "")
      .replace(/\.\d{3}/, "");
  };

  // Clean text for ICS format
  const cleanICSText = (text: string): string => {
    return text
      .replace(/\n/g, "\\n")
      .replace(/,/g, "\\,")
      .replace(/;/g, "\\;");
  };

  // Build location string
  const getLocationString = (): string => {
    if (isVirtual) {
      return virtualUrl || "Virtual Event";
    }
    const parts = [locationName, location, city, state].filter(Boolean);
    return parts.join(", ");
  };

  // Strip HTML from description
  const stripHTML = (html: string): string => {
    const tmp = document.createElement("DIV");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || "";
  };

  // Generate ICS file content
  const generateICS = (): string => {
    const locationStr = getLocationString();
    const descriptionText = description ? stripHTML(description) : "";

    const icsContent = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//WWMAA//Event Calendar//EN",
      "CALSCALE:GREGORIAN",
      "METHOD:PUBLISH",
      "BEGIN:VEVENT",
      `DTSTART:${formatICSDate(startDatetime)}`,
      `DTEND:${formatICSDate(endDatetime)}`,
      `DTSTAMP:${formatICSDate(new Date().toISOString())}`,
      `SUMMARY:${cleanICSText(title)}`,
      `DESCRIPTION:${cleanICSText(descriptionText)}`,
      `LOCATION:${cleanICSText(locationStr)}`,
      `STATUS:CONFIRMED`,
      `SEQUENCE:0`,
      "BEGIN:VALARM",
      "TRIGGER:-PT1H",
      "ACTION:DISPLAY",
      "DESCRIPTION:Reminder: Event starts in 1 hour",
      "END:VALARM",
      "END:VEVENT",
      "END:VCALENDAR",
    ].join("\r\n");

    return icsContent;
  };

  // Download ICS file
  const downloadICS = () => {
    setIsGenerating(true);
    try {
      const icsContent = generateICS();
      const blob = new Blob([icsContent], {
        type: "text/calendar;charset=utf-8",
      });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}.ics`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    } finally {
      setIsGenerating(false);
    }
  };

  // Generate Google Calendar URL
  const getGoogleCalendarUrl = (): string => {
    const params = new URLSearchParams({
      action: "TEMPLATE",
      text: title,
      details: description ? stripHTML(description) : "",
      location: getLocationString(),
      dates: `${formatICSDate(startDatetime)}/${formatICSDate(endDatetime)}`,
    });
    return `https://calendar.google.com/calendar/render?${params.toString()}`;
  };

  // Generate Outlook Calendar URL
  const getOutlookCalendarUrl = (): string => {
    const params = new URLSearchParams({
      subject: title,
      body: description ? stripHTML(description) : "",
      location: getLocationString(),
      startdt: new Date(startDatetime).toISOString(),
      enddt: new Date(endDatetime).toISOString(),
      path: "/calendar/action/compose",
      rru: "addevent",
    });
    return `https://outlook.live.com/calendar/0/deeplink/compose?${params.toString()}`;
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="gap-2"
          disabled={isGenerating}
        >
          <Calendar className="h-4 w-4" />
          Add to Calendar
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem
          onClick={() =>
            window.open(getGoogleCalendarUrl(), "_blank", "noopener,noreferrer")
          }
        >
          <svg
            className="mr-2 h-4 w-4"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2z" />
          </svg>
          Google Calendar
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() =>
            window.open(
              getOutlookCalendarUrl(),
              "_blank",
              "noopener,noreferrer"
            )
          }
        >
          <svg
            className="mr-2 h-4 w-4"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M7 22h10c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2H7c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2zM7 4h10v16H7V4z" />
          </svg>
          Outlook Calendar
        </DropdownMenuItem>
        <DropdownMenuItem onClick={downloadICS}>
          <Download className="mr-2 h-4 w-4" />
          Download ICS File
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
