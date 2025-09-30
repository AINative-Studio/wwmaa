import type { Metadata } from "next";
import { FAQContent } from "./faq-content";

export const metadata: Metadata = {
  title: "Frequently Asked Questions | WWMAA",
  description: "Get answers to common questions about WWMAA membership, martial arts training, belt rankings, and tournaments.",
  keywords: ["martial arts association", "membership FAQ", "belt ranking", "tournaments", "martial arts training", "WWMAA"],
  openGraph: {
    title: "Frequently Asked Questions | WWMAA",
    description: "Get answers to common questions about WWMAA membership, martial arts training, belt rankings, and tournaments.",
    type: "website",
    url: "https://wwmaa.ainative.studio/faq"
  },
  twitter: {
    card: "summary_large_image",
    title: "Frequently Asked Questions | WWMAA",
    description: "Get answers to common questions about WWMAA membership, martial arts training, belt rankings, and tournaments.",
  }
};

const faqs = [
  {
    category: "Membership",
    questions: [
      {
        question: "What martial arts disciplines does WWMAA teach?",
        answer: "WWMAA offers comprehensive training in multiple martial arts disciplines including Judo, Karate, Jiu-Jitsu, Kendo, and various self-defense techniques. Our diverse curriculum allows practitioners to explore different styles and find the martial art that best suits their goals, whether that's competitive sport, self-defense, or personal development. Learn more about our programs on the [training programs page](/programs)."
      },
      {
        question: "How much does WWMAA membership cost?",
        answer: "We offer three membership tiers to accommodate different needs and experience levels: Basic membership is $99 per year and includes access to training resources and member directory; Premium membership is $199 per year with unlimited tournament entries, exclusive training materials, and priority event registration; Instructor membership is $299 per year and includes certification programs, teaching resources, and instructor networking opportunities. Visit our [membership page](/membership) to compare all benefits and choose the plan that's right for you."
      },
      {
        question: "Can beginners join WWMAA?",
        answer: "Absolutely! WWMAA welcomes martial artists of all skill levels, from complete beginners to seasoned masters. Our Basic membership tier is perfect for those just starting their martial arts journey, with no prior experience required. You'll gain access to beginner-friendly training resources, a supportive community of practitioners, and guidance on finding local dojos and instructors. Many of our members started with zero martial arts background and have gone on to achieve black belts and even become certified instructors. Your martial arts journey starts here - join us on the [membership page](/membership)."
      },
      {
        question: "How do I find a local dojo affiliated with WWMAA?",
        answer: "Finding a WWMAA-affiliated dojo near you is easy through your member dashboard. Once you join, you'll have access to our comprehensive dojo directory, which allows you to search by location, martial arts discipline (Judo, Karate, Jiu-Jitsu, etc.), instructor credentials, and class schedules. The directory includes detailed profiles of each dojo, instructor bios, student reviews, and contact information. Many dojos also offer trial classes for new members. If there isn't a WWMAA dojo in your area, you can still benefit from our online training resources and connect with instructors virtually."
      }
    ]
  },
  {
    category: "Belt Ranking & Advancement",
    questions: [
      {
        question: "What are the belt rank requirements?",
        answer: "WWMAA follows traditional belt ranking systems that vary by discipline. Generally, practitioners progress from white belt (beginner) through colored belts (yellow, orange, green, blue, brown) to black belt (Dan ranks). Requirements include minimum training time (typically 3-6 months between ranks for colored belts), demonstration of technical proficiency in required techniques, knowledge of terminology and history, sparring or competition experience for advanced ranks, and instructor recommendation. Specific requirements are detailed in our belt promotion guidelines available to members in the [training resources](/resources) section."
      },
      {
        question: "How long does it take to earn a black belt?",
        answer: "The journey to black belt typically takes 4-6 years of consistent training, though this varies based on individual dedication, training frequency, natural aptitude, and the specific martial arts discipline. At WWMAA, we emphasize quality over speed - earning a black belt represents true mastery of fundamentals, not just time served. Some dedicated practitioners training 4-5 times per week may progress faster, while those training 1-2 times weekly may take longer. Remember, the black belt is not the end goal but the beginning of deeper mastery."
      },
      {
        question: "Do you recognize belt ranks from other martial arts organizations?",
        answer: "Yes, WWMAA recognizes legitimate belt ranks and certifications from established martial arts organizations worldwide. When joining, you can submit documentation of your current rank (certificate, instructor letter, or verifiable training history) for review. Our board will assess your credentials and may request a demonstration of skills to ensure proper placement. We honor the tradition and hard work represented by your existing rank while ensuring standards align with WWMAA requirements."
      },
      {
        question: "What is the belt promotion process?",
        answer: "Belt promotions at WWMAA are earned through demonstrated skill, knowledge, and dedication. The promotion process typically includes a formal testing session where students demonstrate required techniques, kata (forms), and sparring ability appropriate for their rank level. Your instructor will recommend you for testing when they believe you're ready, usually after meeting minimum training time requirements and showing consistent proficiency. Testing is conducted by certified WWMAA examiners and may include written examinations on martial arts history and philosophy for advanced ranks. After successfully passing your test, you'll receive your new belt certificate and have your promotion recorded in your member profile. Some belt tests occur at our [regional events](/events) and tournaments, providing opportunities to test in front of senior masters."
      }
    ]
  },
  {
    category: "Programs & Training",
    questions: [
      {
        question: "What is included in the summer camp?",
        answer: "The WWMAA Summer Camp is an intensive 3-day immersive training experience designed for martial artists of all levels. The camp features training under master instructors with decades of experience, specialized workshops covering techniques, kata, and self-defense, belt testing opportunities for eligible students, networking with practitioners from around the world, and both indoor and outdoor training sessions. The camp is held annually and includes meals and training materials. It's an excellent opportunity for accelerated skill development and community building. Learn more about this program and register on our [summer camp page](/programs/camp)."
      },
      {
        question: "Are there online training options available?",
        answer: "Yes, WWMAA offers comprehensive online training resources for members who cannot attend in-person classes regularly. Premium and Instructor members receive access to video libraries featuring technique demonstrations from master instructors, live-streamed training sessions and seminars, belt rank progression tutorials with detailed explanations, virtual workshops on specialized topics, and access to our online training community for questions and feedback. While in-person training remains ideal for martial arts development, our online resources provide valuable supplemental instruction. Explore all our [training programs](/programs) to find the format that works best for you."
      },
      {
        question: "Are there age requirements for joining WWMAA?",
        answer: "WWMAA welcomes members of all ages, from children to seniors. While there are no strict age restrictions for membership itself, specific programs and activities may have age guidelines for safety and developmental appropriateness. Our youth programs typically start at age 5-6 for basic martial arts fundamentals, with age-appropriate curriculum designed for different developmental stages. Adult programs welcome students from teens through seniors, with modifications available for different fitness levels and physical capabilities. Competition divisions at tournaments are organized by age groups to ensure fair and safe competition. Check individual program descriptions or contact us for specific age-related questions about your family's participation."
      }
    ]
  },
  {
    category: "Tournaments & Competition",
    questions: [
      {
        question: "How do I register for a tournament?",
        answer: "WWMAA members can register for tournaments through our [tournaments page](/programs/tournaments) on the website. Browse upcoming competitions by date, location, and discipline, select your event and choose your division (based on age, belt rank, and weight class), complete the registration form and pay the entry fee (waived for Premium members with unlimited tournament access), and receive confirmation with event details, rules, and preparation guidelines. Registration typically closes 2 weeks before each tournament to allow for bracket creation and logistics planning. First-time competitors should review our tournament preparation resources available in the member dashboard."
      },
      {
        question: "What should I expect at my first martial arts tournament?",
        answer: "Your first tournament is an exciting milestone in your martial arts journey. Arrive early for check-in and weigh-ins (usually 1-2 hours before competition), bring proper competition uniform (gi) and protective gear as required for your division, warm up thoroughly and review techniques with your instructor or teammates, compete in your assigned bracket (elimination or round-robin format depending on division size), and show respect to opponents, officials, and spectators throughout. Win or lose, tournaments are learning experiences that build character, test skills under pressure, and connect you with the broader martial arts community. WWMAA tournaments emphasize sportsmanship and personal growth alongside competitive excellence."
      }
    ]
  },
  {
    category: "Instructor Certification",
    questions: [
      {
        question: "How does instructor certification work?",
        answer: "WWMAA instructor certification requires meeting several key criteria: minimum 2nd Dan (2nd degree black belt) in your primary discipline, at least 5 years of consistent training experience, completion of the WWMAA Instructor Training Program (6 months, covering teaching methodology, safety, curriculum development, and business practices), demonstrated teaching ability through practical examination, CPR and first aid certification, and background check clearance for student safety. Instructor members receive ongoing professional development, teaching resources, liability insurance guidance, and access to our instructor network for mentorship and collaboration. Learn more about our [instructor membership benefits](/membership)."
      }
    ]
  }
];

// Generate FAQPage Schema
const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": faqs.flatMap(category =>
    category.questions.map(faq => ({
      "@type": "Question",
      "name": faq.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.answer.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Strip markdown links for schema
      }
    }))
  )
};

export default function FAQPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <FAQContent faqs={faqs} />
    </>
  );
}
