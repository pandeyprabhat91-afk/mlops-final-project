import { motion } from "framer-motion";

const testimonials = [
  {
    quote: "DeepScan flagged a manipulated interview clip that our editorial team had already approved for broadcast. The Grad-CAM overlay pinpointed exactly which frames were synthetic.",
    author: "Arjun Mehta",
    role: "Senior Investigative Reporter · NDTV",
    initials: "AM",
  },
  {
    quote: "We run background verification on thousands of KYC video submissions daily. DeepScan's API handles the load without breaking a sweat — sub-500ms every time.",
    author: "Priya Nair",
    role: "Head of Risk & Compliance · Razorpay",
    initials: "PN",
  },
  {
    quote: "During the state elections, our fact-checking desk used DeepScan to verify 40+ viral videos in 72 hours. Accuracy held up under real pressure.",
    author: "Vikram Srinivasan",
    role: "Digital Desk Editor · The Hindu",
    initials: "VS",
  },
  {
    quote: "We integrated this into our hiring pipeline for senior roles. Caught two candidates submitting AI-generated video introductions in the first month.",
    author: "Ritu Sharma",
    role: "VP Talent Acquisition · Infosys",
    initials: "RS",
  },
  {
    quote: "As a forensic expert, I needed explainability — not just a score. The Grad-CAM saliency maps are genuinely useful in court submissions.",
    author: "Dr. Anand Kulkarni",
    role: "Digital Forensics Consultant · Bengaluru High Court",
    initials: "AK",
  },
  {
    quote: "Our OTT platform was flooded with deepfake content during a controversy. DeepScan's batch API let us screen 600 clips in one night.",
    author: "Sneha Joshi",
    role: "Content Trust Lead · ZEE5",
    initials: "SJ",
  },
  {
    quote: "The MLflow integration is what sold us. We can retrain on new deepfake datasets and deploy within the same pipeline — no disruption.",
    author: "Rahul Gupta",
    role: "ML Platform Engineer · Juspay",
    initials: "RG",
  },
  {
    quote: "I pitched this to our board as a trust-and-safety investment after a deepfake attack on our CEO's video statement went viral. Best decision we made.",
    author: "Kavitha Reddy",
    role: "CISO · Wipro",
    initials: "KR",
  },
  {
    quote: "Tested against FaceSwap, DeepFaceLab, and several GAN-based tools. Detection rate held above 95% across all of them in our internal benchmark.",
    author: "Nikhil Agarwal",
    role: "AI Safety Researcher · IIT Bombay",
    initials: "NA",
  },
  {
    quote: "We embedded DeepScan into our journalism training programme. Students now verify videos as a standard step before any story goes live.",
    author: "Meera Iyer",
    role: "Director, Media Studies · Symbiosis Institute",
    initials: "MI",
  },
  {
    quote: "The confidence threshold slider is underrated. Our compliance team adjusts it depending on risk appetite — high-stakes deals get a tighter threshold.",
    author: "Sanjay Pillai",
    role: "Head of Legal Tech · Tata Consultancy Services",
    initials: "SP",
  },
  {
    quote: "Political deepfakes are a real problem in India. We deployed DeepScan during election season and caught 23 synthetic videos before they spread.",
    author: "Divya Balachandran",
    role: "Research Lead · DataLEADS",
    initials: "DB",
  },
  {
    quote: "I was skeptical of another detection tool but the Grad-CAM visualisation genuinely helps me explain findings to non-technical clients. That matters.",
    author: "Aarav Menon",
    role: "Independent Digital Forensics Expert · Chennai",
    initials: "AM",
  },
  {
    quote: "Our insurance fraud team uses this to verify claim videos. It paid for itself in the first quarter by flagging four fabricated incident recordings.",
    author: "Lakshmi Chandrasekaran",
    role: "Head of Claims Analytics · HDFC Ergo",
    initials: "LC",
  },
  {
    quote: "The Docker deployment is clean — we had it running in our private cloud within an afternoon. No dependency hell, no surprises in production.",
    author: "Rohan Desai",
    role: "DevOps Lead · PhonePe",
    initials: "RD",
  },
];

export const Testimonials: React.FC = () => (
  <section className="lp-section lp-testimonials">
    <div className="lp-inner">
      <motion.div
        className="lp-section-header"
        initial={{ opacity: 0, x: -40 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true, margin: "-50px" }}
        transition={{ type: "spring", stiffness: 180, damping: 18 }}
      >
        <motion.span
          className="lp-eyebrow"
          initial={{ opacity: 0, x: -40 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ type: "spring", stiffness: 180, damping: 18, delay: 0.05 }}
        >Trusted by teams</motion.span>
        <motion.h2
          className="lp-section-title"
          initial={{ opacity: 0, x: -40 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ type: "spring", stiffness: 180, damping: 18, delay: 0.12 }}
        >Results that speak for themselves</motion.h2>
      </motion.div>
    </div>

    {/* Full-bleed infinite carousel — two rows scrolling opposite directions */}
    <div className="lp-carousel-wrap">
      {/* Row 1 — left */}
      <div className="lp-carousel-row">
        <motion.div
          className="lp-carousel-track"
          animate={{ x: ["0%", "-50%"] }}
          transition={{ duration: 76, ease: "linear", repeat: Infinity }}
        >
          {[...testimonials, ...testimonials].map((t, i) => (
            <div key={i} className="lp-testimonial-card">
              <div className="lp-testimonial-quote">"</div>
              <p className="lp-testimonial-text">{t.quote}</p>
              <div className="lp-testimonial-author">
                <div className="lp-testimonial-avatar">{t.initials}</div>
                <div>
                  <p className="lp-testimonial-name">{t.author}</p>
                  <p className="lp-testimonial-role">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Row 2 — right (offset start, opposite direction) */}
      <div className="lp-carousel-row">
        <motion.div
          className="lp-carousel-track"
          animate={{ x: ["-50%", "0%"] }}
          transition={{ duration: 88, ease: "linear", repeat: Infinity }}
        >
          {[...testimonials.slice(7), ...testimonials.slice(0, 7), ...testimonials.slice(7), ...testimonials.slice(0, 7)].map((t, i) => (
            <div key={i} className="lp-testimonial-card">
              <div className="lp-testimonial-quote">"</div>
              <p className="lp-testimonial-text">{t.quote}</p>
              <div className="lp-testimonial-author">
                <div className="lp-testimonial-avatar">{t.initials}</div>
                <div>
                  <p className="lp-testimonial-name">{t.author}</p>
                  <p className="lp-testimonial-role">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  </section>
);
