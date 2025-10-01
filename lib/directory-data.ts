export interface DirectoryMember {
  id: string;
  name: string;
  type: 'student' | 'instructor' | 'dojo';
  state: string;
  city: string;
  beltRank?: string;
  specialties?: string[];
  dojoName?: string;
  yearsExperience?: number;
  disciplines: string[];
  bio?: string;
  avatar: string;
}

export const directoryMembers: DirectoryMember[] = [
  // California - Students
  {
    id: "ca-s-1",
    name: "Sarah Chen",
    type: "student",
    state: "California",
    city: "San Francisco",
    beltRank: "Brown Belt",
    disciplines: ["Judo", "Jiu-Jitsu"],
    dojoName: "Golden Gate Martial Arts",
    bio: "Passionate practitioner focused on competition and personal growth",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah"
  },
  {
    id: "ca-s-2",
    name: "Marcus Rodriguez",
    type: "student",
    state: "California",
    city: "Los Angeles",
    beltRank: "Blue Belt",
    disciplines: ["Karate"],
    dojoName: "LA Karate Academy",
    bio: "Training in traditional Shotokan karate with focus on kata excellence",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Marcus"
  },

  // California - Instructors
  {
    id: "ca-i-1",
    name: "Master Robert Kim",
    type: "instructor",
    state: "California",
    city: "San Diego",
    beltRank: "5th Dan Black Belt",
    specialties: ["Competition Training", "Youth Programs"],
    disciplines: ["Judo", "Jiu-Jitsu"],
    yearsExperience: 25,
    bio: "Elite competition coach specializing in Olympic-style judo and youth development",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Robert"
  },
  {
    id: "ca-d-1",
    name: "Pacific Warriors Dojo",
    type: "dojo",
    state: "California",
    city: "Sacramento",
    disciplines: ["Karate", "Kendo", "Self-Defense"],
    yearsExperience: 15,
    bio: "Family-friendly dojo offering traditional martial arts training for all ages",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=PacificWarriors"
  },

  // Texas - Students
  {
    id: "tx-s-1",
    name: "Emily Johnson",
    type: "student",
    state: "Texas",
    city: "Austin",
    beltRank: "Green Belt",
    disciplines: ["Karate", "Self-Defense"],
    dojoName: "Texas Martial Arts Center",
    bio: "Adult beginner discovering the transformative power of martial arts training",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Emily"
  },
  {
    id: "tx-s-2",
    name: "Daniel Park",
    type: "student",
    state: "Texas",
    city: "Dallas",
    beltRank: "Black Belt (1st Dan)",
    disciplines: ["Judo"],
    dojoName: "Dallas Judo Club",
    bio: "Competitive judoka training for national tournaments and belt advancement",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Daniel"
  },

  // Texas - Instructors
  {
    id: "tx-i-1",
    name: "Sensei Maria Gonzales",
    type: "instructor",
    state: "Texas",
    city: "Houston",
    beltRank: "4th Dan Black Belt",
    specialties: ["Women's Self-Defense", "Traditional Karate"],
    disciplines: ["Karate", "Self-Defense"],
    yearsExperience: 18,
    bio: "Women's self-defense specialist and traditional Shotokan karate instructor",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Maria"
  },
  {
    id: "tx-d-1",
    name: "Lone Star Martial Arts Academy",
    type: "dojo",
    state: "Texas",
    city: "San Antonio",
    disciplines: ["Judo", "Jiu-Jitsu", "Karate"],
    yearsExperience: 22,
    bio: "Premier martial arts academy with programs for children, teens, and adults",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=LoneStar"
  },

  // New York - Students
  {
    id: "ny-s-1",
    name: "James Wilson",
    type: "student",
    state: "New York",
    city: "New York City",
    beltRank: "Purple Belt",
    disciplines: ["Jiu-Jitsu"],
    dojoName: "NYC Brazilian Jiu-Jitsu",
    bio: "Wall Street professional training BJJ for stress relief and fitness",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=James"
  },
  {
    id: "ny-s-2",
    name: "Aisha Mohammed",
    type: "student",
    state: "New York",
    city: "Brooklyn",
    beltRank: "Orange Belt",
    disciplines: ["Karate"],
    dojoName: "Brooklyn Karate Dojo",
    bio: "Young professional learning discipline and self-confidence through karate",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Aisha"
  },

  // New York - Instructors
  {
    id: "ny-i-1",
    name: "Shihan David Chen",
    type: "instructor",
    state: "New York",
    city: "Buffalo",
    beltRank: "6th Dan Black Belt",
    specialties: ["Traditional Forms", "Tournament Preparation"],
    disciplines: ["Karate", "Kendo"],
    yearsExperience: 30,
    bio: "Master instructor specializing in traditional Japanese martial arts and kata",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=DavidC"
  },
  {
    id: "ny-d-1",
    name: "Empire State Judo Club",
    type: "dojo",
    state: "New York",
    city: "Albany",
    disciplines: ["Judo"],
    yearsExperience: 28,
    bio: "Olympic-level judo training with nationally ranked competitive team",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=EmpireState"
  },

  // Florida - Students
  {
    id: "fl-s-1",
    name: "Michael Brown",
    type: "student",
    state: "Florida",
    city: "Miami",
    beltRank: "Yellow Belt",
    disciplines: ["Karate"],
    dojoName: "Miami Beach Martial Arts",
    bio: "Retired veteran finding purpose and community through martial arts training",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Michael"
  },
  {
    id: "fl-s-2",
    name: "Lisa Martinez",
    type: "student",
    state: "Florida",
    city: "Orlando",
    beltRank: "Green Belt",
    disciplines: ["Judo", "Self-Defense"],
    dojoName: "Central Florida Judo",
    bio: "Mother of two balancing family life with personal martial arts goals",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Lisa"
  },

  // Florida - Instructors
  {
    id: "fl-i-1",
    name: "Master Carlos Silva",
    type: "instructor",
    state: "Florida",
    city: "Tampa",
    beltRank: "7th Dan Black Belt",
    specialties: ["Brazilian Jiu-Jitsu", "MMA Integration"],
    disciplines: ["Jiu-Jitsu", "Self-Defense"],
    yearsExperience: 35,
    bio: "Legendary BJJ instructor with lineage to Brazilian martial arts masters",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Carlos"
  },
  {
    id: "fl-d-1",
    name: "Sunshine State Karate Academy",
    type: "dojo",
    state: "Florida",
    city: "Jacksonville",
    disciplines: ["Karate", "Self-Defense"],
    yearsExperience: 12,
    bio: "Modern facility focusing on practical self-defense and traditional values",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=Sunshine"
  },

  // Illinois - Students
  {
    id: "il-s-1",
    name: "Jennifer Lee",
    type: "student",
    state: "Illinois",
    city: "Chicago",
    beltRank: "Blue Belt",
    disciplines: ["Judo"],
    dojoName: "Chicago Judo Institute",
    bio: "Software engineer applying systematic thinking to judo technique mastery",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Jennifer"
  },
  {
    id: "il-s-2",
    name: "Robert Taylor",
    type: "student",
    state: "Illinois",
    city: "Springfield",
    beltRank: "Brown Belt",
    disciplines: ["Karate", "Kendo"],
    dojoName: "Illinois Traditional Martial Arts",
    bio: "High school teacher inspiring students through martial arts discipline",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=RobertT"
  },

  // Illinois - Instructors
  {
    id: "il-i-1",
    name: "Sensei Patricia O'Brien",
    type: "instructor",
    state: "Illinois",
    city: "Naperville",
    beltRank: "5th Dan Black Belt",
    specialties: ["Children's Programs", "Character Development"],
    disciplines: ["Karate"],
    yearsExperience: 20,
    bio: "Youth development specialist using martial arts to build confidence and respect",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Patricia"
  },
  {
    id: "il-d-1",
    name: "Windy City Martial Arts Center",
    type: "dojo",
    state: "Illinois",
    city: "Chicago",
    disciplines: ["Judo", "Karate", "Jiu-Jitsu"],
    yearsExperience: 18,
    bio: "Urban martial arts center serving diverse Chicago community since 2007",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=WindyCity"
  },

  // Pennsylvania - Students
  {
    id: "pa-s-1",
    name: "Thomas Anderson",
    type: "student",
    state: "Pennsylvania",
    city: "Philadelphia",
    beltRank: "Green Belt",
    disciplines: ["Jiu-Jitsu"],
    dojoName: "Philly Jiu-Jitsu Academy",
    bio: "Former college athlete transitioning martial arts skills to real-world application",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Thomas"
  },
  {
    id: "pa-s-2",
    name: "Amanda White",
    type: "student",
    state: "Pennsylvania",
    city: "Pittsburgh",
    beltRank: "Yellow Belt",
    disciplines: ["Karate", "Self-Defense"],
    dojoName: "Steel City Karate",
    bio: "Nurse practitioner training for personal safety and physical wellness",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Amanda"
  },

  // Pennsylvania - Instructors
  {
    id: "pa-i-1",
    name: "Master John Kowalski",
    type: "instructor",
    state: "Pennsylvania",
    city: "Harrisburg",
    beltRank: "6th Dan Black Belt",
    specialties: ["Sport Judo", "Referee Training"],
    disciplines: ["Judo"],
    yearsExperience: 28,
    bio: "International judo referee and coach with Olympic team experience",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=JohnK"
  },
  {
    id: "pa-d-1",
    name: "Liberty Bell Martial Arts",
    type: "dojo",
    state: "Pennsylvania",
    city: "Philadelphia",
    disciplines: ["Karate", "Kendo"],
    yearsExperience: 25,
    bio: "Historic Philadelphia dojo preserving traditional martial arts heritage",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=LibertyBell"
  },

  // Ohio - Students
  {
    id: "oh-s-1",
    name: "Kevin Harris",
    type: "student",
    state: "Ohio",
    city: "Columbus",
    beltRank: "Orange Belt",
    disciplines: ["Karate"],
    dojoName: "Columbus Karate Center",
    bio: "College student balancing academics with martial arts excellence",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Kevin"
  },
  {
    id: "oh-s-2",
    name: "Rachel Green",
    type: "student",
    state: "Ohio",
    city: "Cleveland",
    beltRank: "Purple Belt",
    disciplines: ["Jiu-Jitsu", "Self-Defense"],
    dojoName: "Cleveland Combat Arts",
    bio: "Entrepreneur applying martial arts principles to business and life",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Rachel"
  },

  // Ohio - Instructors
  {
    id: "oh-i-1",
    name: "Sensei Michelle Davis",
    type: "instructor",
    state: "Ohio",
    city: "Cincinnati",
    beltRank: "4th Dan Black Belt",
    specialties: ["Adult Beginners", "Fitness Integration"],
    disciplines: ["Karate", "Self-Defense"],
    yearsExperience: 15,
    bio: "Fitness professional integrating martial arts with modern wellness practices",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Michelle"
  },
  {
    id: "oh-d-1",
    name: "Buckeye State Judo Club",
    type: "dojo",
    state: "Ohio",
    city: "Dayton",
    disciplines: ["Judo"],
    yearsExperience: 20,
    bio: "Community-focused judo club producing regional and national champions",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=Buckeye"
  },

  // Georgia - Students
  {
    id: "ga-s-1",
    name: "Brandon Lewis",
    type: "student",
    state: "Georgia",
    city: "Atlanta",
    beltRank: "Blue Belt",
    disciplines: ["Judo", "Jiu-Jitsu"],
    dojoName: "Atlanta Martial Arts Collective",
    bio: "Tech professional finding balance through martial arts training and meditation",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Brandon"
  },
  {
    id: "ga-s-2",
    name: "Sophia Williams",
    type: "student",
    state: "Georgia",
    city: "Savannah",
    beltRank: "Green Belt",
    disciplines: ["Karate"],
    dojoName: "Savannah Karate Academy",
    bio: "Teacher by day, karateka by night, inspiring others through dedication",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sophia"
  },

  // Georgia - Instructors
  {
    id: "ga-i-1",
    name: "Master James Patterson",
    type: "instructor",
    state: "Georgia",
    city: "Augusta",
    beltRank: "5th Dan Black Belt",
    specialties: ["Competition Coaching", "Belt Testing"],
    disciplines: ["Karate", "Kendo"],
    yearsExperience: 22,
    bio: "Competition coach producing state and regional martial arts champions",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=JamesP"
  },
  {
    id: "ga-d-1",
    name: "Peach State Martial Arts",
    type: "dojo",
    state: "Georgia",
    city: "Atlanta",
    disciplines: ["Judo", "Jiu-Jitsu", "Self-Defense"],
    yearsExperience: 16,
    bio: "Modern training facility with traditional values and family atmosphere",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=PeachState"
  },

  // Washington - Students
  {
    id: "wa-s-1",
    name: "Christopher Young",
    type: "student",
    state: "Washington",
    city: "Seattle",
    beltRank: "Brown Belt",
    disciplines: ["Judo"],
    dojoName: "Seattle Judo Dojo",
    bio: "Amazon engineer applying problem-solving skills to judo techniques",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Christopher"
  },
  {
    id: "wa-s-2",
    name: "Nicole Thompson",
    type: "student",
    state: "Washington",
    city: "Spokane",
    beltRank: "Purple Belt",
    disciplines: ["Karate", "Self-Defense"],
    dojoName: "Spokane Martial Arts Center",
    bio: "Healthcare worker training for mental resilience and physical strength",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Nicole"
  },

  // Washington - Instructors
  {
    id: "wa-i-1",
    name: "Sensei Angela Liu",
    type: "instructor",
    state: "Washington",
    city: "Tacoma",
    beltRank: "6th Dan Black Belt",
    specialties: ["Traditional Forms", "Mindfulness Training"],
    disciplines: ["Karate", "Kendo"],
    yearsExperience: 26,
    bio: "Mindfulness instructor integrating meditation with traditional martial arts",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Angela"
  },
  {
    id: "wa-d-1",
    name: "Evergreen Martial Arts Academy",
    type: "dojo",
    state: "Washington",
    city: "Seattle",
    disciplines: ["Judo", "Jiu-Jitsu", "Karate"],
    yearsExperience: 14,
    bio: "Pacific Northwest's premier martial arts school with eco-conscious values",
    avatar: "https://api.dicebear.com/7.x/shapes/svg?seed=Evergreen"
  }
];

export const states = [
  "All States",
  "California",
  "Texas",
  "New York",
  "Florida",
  "Illinois",
  "Pennsylvania",
  "Ohio",
  "Georgia",
  "Washington"
];

export const memberTypes = [
  { value: "all", label: "All Members" },
  { value: "student", label: "Students" },
  { value: "instructor", label: "Instructors" },
  { value: "dojo", label: "Dojos" }
];
