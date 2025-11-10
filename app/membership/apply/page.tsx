"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AlertCircle, CheckCircle2, ChevronLeft, ChevronRight, Upload, X } from "lucide-react";

// Constants for martial arts disciplines
const MARTIAL_ARTS_DISCIPLINES = [
  "Taekwondo",
  "Karate",
  "Judo",
  "Brazilian Jiu-Jitsu",
  "Kung Fu",
  "Muay Thai",
  "Krav Maga",
  "Aikido",
  "Hapkido",
  "Mixed Martial Arts (MMA)",
  "Other"
];

const US_STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
];

// Zod validation schema
const formSchema = z.object({
  // Personal Information
  first_name: z.string().min(2, "First name must be at least 2 characters").max(50, "First name is too long"),
  last_name: z.string().min(2, "Last name must be at least 2 characters").max(50, "Last name is too long"),
  email: z.string().email("Invalid email address"),
  phone: z.string()
    .regex(/^[\d\s\-\(\)\+]+$/, "Invalid phone number format")
    .min(10, "Phone number must be at least 10 digits")
    .max(20, "Phone number is too long"),
  address: z.string().min(5, "Address must be at least 5 characters").max(200, "Address is too long"),
  city: z.string().min(2, "City must be at least 2 characters").max(100, "City is too long"),
  state: z.string().min(2, "Please select a state"),
  zip_code: z.string()
    .regex(/^\d{5}(-\d{4})?$/, "Invalid ZIP code format (e.g., 12345 or 12345-6789)")
    .min(5, "ZIP code must be 5 digits"),
  country: z.string().min(2, "Country must be at least 2 characters").default("United States"),

  // Martial Arts Background
  primary_discipline: z.string().min(1, "Please select your primary discipline"),
  current_rank: z.string().min(1, "Current rank is required").max(50, "Rank is too long"),
  years_of_experience: z.coerce
    .number()
    .min(0, "Years of experience cannot be negative")
    .max(100, "Years of experience must be less than 100"),
  instructor_name: z.string().min(2, "Instructor name must be at least 2 characters").max(100, "Instructor name is too long"),
  school_affiliation: z.string().min(2, "School affiliation must be at least 2 characters").max(200, "School affiliation is too long"),

  // References (3 required)
  reference1_name: z.string().min(2, "Reference name must be at least 2 characters"),
  reference1_email: z.string().email("Invalid email address"),
  reference1_relationship: z.string().min(2, "Relationship must be at least 2 characters"),

  reference2_name: z.string().min(2, "Reference name must be at least 2 characters"),
  reference2_email: z.string().email("Invalid email address"),
  reference2_relationship: z.string().min(2, "Relationship must be at least 2 characters"),

  reference3_name: z.string().min(2, "Reference name must be at least 2 characters"),
  reference3_email: z.string().email("Invalid email address"),
  reference3_relationship: z.string().min(2, "Relationship must be at least 2 characters"),

  // Additional Information
  reason_for_joining: z.string()
    .min(50, "Statement of purpose must be at least 50 characters")
    .max(500, "Statement of purpose must be no more than 500 characters"),

  // Terms and Conditions
  agree_to_terms: z.boolean().refine((val) => val === true, {
    message: "You must agree to the terms and conditions",
  }),
});

type FormData = z.infer<typeof formSchema>;

const STEPS = [
  { id: 1, name: "Personal Information", description: "Basic contact details" },
  { id: 2, name: "Martial Arts Background", description: "Your training and experience" },
  { id: 3, name: "References", description: "Three professional references" },
  { id: 4, name: "Review & Submit", description: "Review and submit your application" },
];

const LOCAL_STORAGE_KEY = "wwmaa_application_draft";

export default function MembershipApplicationPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      address: "",
      city: "",
      state: "",
      zip_code: "",
      country: "United States",
      primary_discipline: "",
      current_rank: "",
      years_of_experience: 0,
      instructor_name: "",
      school_affiliation: "",
      reference1_name: "",
      reference1_email: "",
      reference1_relationship: "",
      reference2_name: "",
      reference2_email: "",
      reference2_relationship: "",
      reference3_name: "",
      reference3_email: "",
      reference3_relationship: "",
      reason_for_joining: "",
      agree_to_terms: false,
    },
  });

  // Load draft from localStorage on mount
  useEffect(() => {
    const savedDraft = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (savedDraft) {
      try {
        const parsedDraft = JSON.parse(savedDraft);
        // Reset the form with saved values
        Object.keys(parsedDraft).forEach((key) => {
          form.setValue(key as keyof FormData, parsedDraft[key]);
        });
      } catch (error) {
        console.error("Failed to load draft:", error);
      }
    }
  }, [form]);

  // Save draft to localStorage whenever form values change
  useEffect(() => {
    const subscription = form.watch((value) => {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(value));
    });
    return () => subscription.unsubscribe();
  }, [form]);

  // Handle file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    const newFiles = Array.from(files);
    const validFiles: File[] = [];
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

    newFiles.forEach((file) => {
      if (file.size > MAX_FILE_SIZE) {
        alert(`File ${file.name} is too large. Maximum size is 5MB.`);
        return;
      }
      validFiles.push(file);
    });

    setUploadedFiles([...uploadedFiles, ...validFiles]);
  };

  const removeFile = (index: number) => {
    setUploadedFiles(uploadedFiles.filter((_, i) => i !== index));
  };

  // Validate current step before proceeding
  const validateStep = async (step: number): Promise<boolean> => {
    let fieldsToValidate: (keyof FormData)[] = [];

    switch (step) {
      case 1: // Personal Information
        fieldsToValidate = [
          "first_name",
          "last_name",
          "email",
          "phone",
          "address",
          "city",
          "state",
          "zip_code",
          "country",
        ];
        break;
      case 2: // Martial Arts Background
        fieldsToValidate = [
          "primary_discipline",
          "current_rank",
          "years_of_experience",
          "instructor_name",
          "school_affiliation",
        ];
        break;
      case 3: // References
        fieldsToValidate = [
          "reference1_name",
          "reference1_email",
          "reference1_relationship",
          "reference2_name",
          "reference2_email",
          "reference2_relationship",
          "reference3_name",
          "reference3_email",
          "reference3_relationship",
          "reason_for_joining",
        ];
        break;
      case 4: // Review & Submit
        fieldsToValidate = ["agree_to_terms"];
        break;
    }

    const result = await form.trigger(fieldsToValidate);
    return result;
  };

  const nextStep = async () => {
    const isValid = await validateStep(currentStep);
    if (isValid && currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Create FormData for file upload
      const formData = new FormData();

      // Append all form fields
      Object.entries(data).forEach(([key, value]) => {
        formData.append(key, String(value));
      });

      // Append files
      uploadedFiles.forEach((file, index) => {
        formData.append(`certificate_${index}`, file);
      });

      // Submit to backend API
      const response = await fetch("/api/applications", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to submit application");
      }

      const result = await response.json();

      // Clear localStorage draft
      localStorage.removeItem(LOCAL_STORAGE_KEY);

      // Redirect to success page with application ID
      router.push(`/membership/apply/success?id=${result.application_id}`);
    } catch (error) {
      console.error("Application submission error:", error);
      setSubmitError(
        error instanceof Error
          ? error.message
          : "An unexpected error occurred. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const progress = (currentStep / STEPS.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-dojo-navy mb-2">
            Membership Application
          </h1>
          <p className="text-gray-600">
            Join the World Wide Martial Arts Association
          </p>
        </div>

        {/* Progress Bar */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">
                  Step {currentStep} of {STEPS.length}
                </span>
                <span className="text-sm font-medium text-dojo-green">
                  {Math.round(progress)}% Complete
                </span>
              </div>
              <Progress value={progress} className="h-2" />
              <div className="flex justify-between">
                {STEPS.map((step) => (
                  <div
                    key={step.id}
                    className={`flex-1 text-center ${
                      step.id === currentStep
                        ? "text-dojo-navy font-semibold"
                        : step.id < currentStep
                        ? "text-dojo-green"
                        : "text-gray-400"
                    }`}
                  >
                    <div className="text-xs hidden sm:block">{step.name}</div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Error Alert */}
        {submitError && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Submission Error</AlertTitle>
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        )}

        {/* Form */}
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Step 1: Personal Information */}
            {currentStep === 1 && (
              <Card>
                <CardHeader>
                  <CardTitle>Personal Information</CardTitle>
                  <CardDescription>
                    Please provide your basic contact information
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="first_name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>First Name *</FormLabel>
                          <FormControl>
                            <Input placeholder="John" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="last_name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Last Name *</FormLabel>
                          <FormControl>
                            <Input placeholder="Doe" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email Address *</FormLabel>
                          <FormControl>
                            <Input
                              type="email"
                              placeholder="john.doe@example.com"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="phone"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Phone Number *</FormLabel>
                          <FormControl>
                            <Input
                              type="tel"
                              placeholder="(555) 123-4567"
                              {...field}
                            />
                          </FormControl>
                          <FormDescription>
                            US format preferred
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="address"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Street Address *</FormLabel>
                        <FormControl>
                          <Input placeholder="123 Main Street" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="city"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>City *</FormLabel>
                          <FormControl>
                            <Input placeholder="Los Angeles" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="state"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>State *</FormLabel>
                          <Select
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                          >
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select state" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {US_STATES.map((state) => (
                                <SelectItem key={state} value={state}>
                                  {state}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="zip_code"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>ZIP Code *</FormLabel>
                          <FormControl>
                            <Input placeholder="90001" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="country"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Country *</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>
            )}

            {/* Step 2: Martial Arts Background */}
            {currentStep === 2 && (
              <Card>
                <CardHeader>
                  <CardTitle>Martial Arts Background</CardTitle>
                  <CardDescription>
                    Tell us about your martial arts training and experience
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="primary_discipline"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Primary Discipline *</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          defaultValue={field.value}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select your primary discipline" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {MARTIAL_ARTS_DISCIPLINES.map((discipline) => (
                              <SelectItem key={discipline} value={discipline}>
                                {discipline}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="current_rank"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Current Rank/Belt *</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="e.g., Black Belt 2nd Dan"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="years_of_experience"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Years of Experience *</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              placeholder="5"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="instructor_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Current/Previous Instructor Name *</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Master John Smith"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="school_affiliation"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>School/Dojo Affiliation *</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Dragon Martial Arts Academy"
                            {...field}
                          />
                        </FormControl>
                        <FormDescription>
                          Current or most recent school affiliation
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* File Upload for Certificates */}
                  <div className="space-y-2">
                    <FormLabel>Martial Arts Certificates (Optional)</FormLabel>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-dojo-green transition-colors">
                      <Upload className="mx-auto h-12 w-12 text-gray-400" />
                      <div className="mt-4">
                        <label
                          htmlFor="file-upload"
                          className="cursor-pointer text-dojo-navy hover:text-dojo-green font-medium"
                        >
                          <span>Upload certificates</span>
                          <input
                            id="file-upload"
                            name="file-upload"
                            type="file"
                            className="sr-only"
                            multiple
                            accept=".pdf,.jpg,.jpeg,.png"
                            onChange={handleFileUpload}
                          />
                        </label>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        PDF, JPG, or PNG up to 5MB each
                      </p>
                    </div>

                    {/* Uploaded Files List */}
                    {uploadedFiles.length > 0 && (
                      <div className="mt-4 space-y-2">
                        {uploadedFiles.map((file, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between bg-gray-50 p-3 rounded-lg"
                          >
                            <div className="flex items-center space-x-2">
                              <CheckCircle2 className="h-4 w-4 text-dojo-green" />
                              <span className="text-sm text-gray-700">
                                {file.name}
                              </span>
                              <span className="text-xs text-gray-500">
                                ({(file.size / 1024).toFixed(1)} KB)
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() => removeFile(index)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Step 3: References */}
            {currentStep === 3 && (
              <Card>
                <CardHeader>
                  <CardTitle>References & Statement of Purpose</CardTitle>
                  <CardDescription>
                    Provide three professional references and your reason for joining
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Reference 1 */}
                  <div className="space-y-4 border-b pb-4">
                    <h4 className="font-semibold text-gray-900">Reference 1</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField
                        control={form.control}
                        name="reference1_name"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Name *</FormLabel>
                            <FormControl>
                              <Input placeholder="Jane Smith" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="reference1_email"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Email *</FormLabel>
                            <FormControl>
                              <Input
                                type="email"
                                placeholder="jane@example.com"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="reference1_relationship"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Relationship *</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="Instructor/Colleague"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>

                  {/* Reference 2 */}
                  <div className="space-y-4 border-b pb-4">
                    <h4 className="font-semibold text-gray-900">Reference 2</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField
                        control={form.control}
                        name="reference2_name"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Name *</FormLabel>
                            <FormControl>
                              <Input placeholder="Bob Johnson" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="reference2_email"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Email *</FormLabel>
                            <FormControl>
                              <Input
                                type="email"
                                placeholder="bob@example.com"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="reference2_relationship"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Relationship *</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="Instructor/Colleague"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>

                  {/* Reference 3 */}
                  <div className="space-y-4 border-b pb-4">
                    <h4 className="font-semibold text-gray-900">Reference 3</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField
                        control={form.control}
                        name="reference3_name"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Name *</FormLabel>
                            <FormControl>
                              <Input placeholder="Mary Williams" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="reference3_email"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Email *</FormLabel>
                            <FormControl>
                              <Input
                                type="email"
                                placeholder="mary@example.com"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="reference3_relationship"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Relationship *</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="Instructor/Colleague"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>

                  {/* Statement of Purpose */}
                  <FormField
                    control={form.control}
                    name="reason_for_joining"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Statement of Purpose *</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Please describe your reasons for joining WWMAA and what you hope to achieve as a member..."
                            className="min-h-[150px]"
                            maxLength={500}
                            {...field}
                          />
                        </FormControl>
                        <FormDescription>
                          {field.value.length}/500 characters (minimum 50
                          characters)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>
            )}

            {/* Step 4: Review & Submit */}
            {currentStep === 4 && (
              <Card>
                <CardHeader>
                  <CardTitle>Review & Submit</CardTitle>
                  <CardDescription>
                    Please review your application before submitting
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Personal Information Review */}
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-900">
                      Personal Information
                    </h4>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-1 text-sm">
                      <p>
                        <span className="font-medium">Name:</span>{" "}
                        {form.getValues("first_name")}{" "}
                        {form.getValues("last_name")}
                      </p>
                      <p>
                        <span className="font-medium">Email:</span>{" "}
                        {form.getValues("email")}
                      </p>
                      <p>
                        <span className="font-medium">Phone:</span>{" "}
                        {form.getValues("phone")}
                      </p>
                      <p>
                        <span className="font-medium">Address:</span>{" "}
                        {form.getValues("address")}, {form.getValues("city")},{" "}
                        {form.getValues("state")} {form.getValues("zip_code")},{" "}
                        {form.getValues("country")}
                      </p>
                    </div>
                  </div>

                  {/* Martial Arts Background Review */}
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-900">
                      Martial Arts Background
                    </h4>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-1 text-sm">
                      <p>
                        <span className="font-medium">Primary Discipline:</span>{" "}
                        {form.getValues("primary_discipline")}
                      </p>
                      <p>
                        <span className="font-medium">Current Rank:</span>{" "}
                        {form.getValues("current_rank")}
                      </p>
                      <p>
                        <span className="font-medium">
                          Years of Experience:
                        </span>{" "}
                        {form.getValues("years_of_experience")}
                      </p>
                      <p>
                        <span className="font-medium">Instructor:</span>{" "}
                        {form.getValues("instructor_name")}
                      </p>
                      <p>
                        <span className="font-medium">School:</span>{" "}
                        {form.getValues("school_affiliation")}
                      </p>
                      {uploadedFiles.length > 0 && (
                        <p>
                          <span className="font-medium">Certificates:</span>{" "}
                          {uploadedFiles.length} file(s) attached
                        </p>
                      )}
                    </div>
                  </div>

                  {/* References Review */}
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-900">References</h4>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-2 text-sm">
                      <div>
                        <p className="font-medium">Reference 1:</p>
                        <p>
                          {form.getValues("reference1_name")} (
                          {form.getValues("reference1_email")}) -{" "}
                          {form.getValues("reference1_relationship")}
                        </p>
                      </div>
                      <div>
                        <p className="font-medium">Reference 2:</p>
                        <p>
                          {form.getValues("reference2_name")} (
                          {form.getValues("reference2_email")}) -{" "}
                          {form.getValues("reference2_relationship")}
                        </p>
                      </div>
                      <div>
                        <p className="font-medium">Reference 3:</p>
                        <p>
                          {form.getValues("reference3_name")} (
                          {form.getValues("reference3_email")}) -{" "}
                          {form.getValues("reference3_relationship")}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Statement of Purpose Review */}
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-900">
                      Statement of Purpose
                    </h4>
                    <div className="bg-gray-50 p-4 rounded-lg text-sm">
                      <p>{form.getValues("reason_for_joining")}</p>
                    </div>
                  </div>

                  {/* Terms and Conditions */}
                  <FormField
                    control={form.control}
                    name="agree_to_terms"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel>
                            I agree to the terms and conditions *
                          </FormLabel>
                          <FormDescription>
                            By checking this box, I confirm that all information
                            provided is accurate and I agree to abide by the
                            WWMAA code of conduct and bylaws.
                          </FormDescription>
                          <FormMessage />
                        </div>
                      </FormItem>
                    )}
                  />

                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Before you submit</AlertTitle>
                    <AlertDescription>
                      Please review all information carefully. Once submitted,
                      your application will be reviewed by our membership
                      committee. You will receive an email confirmation and
                      updates on your application status.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between">
              <Button
                type="button"
                variant="outline"
                onClick={prevStep}
                disabled={currentStep === 1}
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Previous
              </Button>

              {currentStep < STEPS.length ? (
                <Button type="button" onClick={nextStep}>
                  Next
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              ) : (
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Submitting..." : "Submit Application"}
                </Button>
              )}
            </div>
          </form>
        </Form>
      </div>
    </div>
  );
}
