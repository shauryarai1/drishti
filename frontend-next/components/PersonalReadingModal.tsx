import React, { useState } from 'react';
import { X, CheckCircle2, Calendar, Clock, User, Mail, Sparkles } from 'lucide-react';
import { Button } from './Button';

interface PersonalReadingModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultPlace?: string;
}

export function PersonalReadingModal({
  isOpen,
  onClose,
  defaultPlace = 'New Delhi, India',
}: PersonalReadingModalProps) {
  const [submitted, setSubmitted] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [topic, setTopic] = useState('Career & Long-range Strategy');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-[#090909]/85 backdrop-blur-xl">
      <div className="relative w-full max-w-lg rounded-xl bg-gradient-to-b from-[#160A0C] to-[#090909] border border-[#A62A34]/40 shadow-[0_24px_80px_rgba(0,0,0,0.9)] p-6 sm:p-8 text-[#EEE9DF]">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-[#EEE9DF]/60 hover:text-[#F7F5F0] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {!submitted ? (
          <div className="space-y-6">
            <div className="space-y-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#B39250]">
                PRIVATE DIALOGUE
              </span>
              <h3 className="text-2xl font-bold text-[#F7F5F0] tracking-tight">
                Request a 1-on-1 Discourse
              </h3>
              <p className="text-xs sm:text-sm text-[#EEE9DF]/70 leading-relaxed">
                Direct consultation with a senior Vedic scholar to examine your specific dasha transitions and long-range timing.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-mono uppercase text-[#EEE9DF]/70">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-[#A62A34] absolute left-3.5 top-3" />
                  <input
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your name"
                    className="w-full pl-10 pr-4 py-2.5 bg-[#090909] border border-[#A62A34]/30 rounded-md text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono uppercase text-[#EEE9DF]/70">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-[#A62A34] absolute left-3.5 top-3" />
                  <input
                    required
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@domain.com"
                    className="w-full pl-10 pr-4 py-2.5 bg-[#090909] border border-[#A62A34]/30 rounded-md text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono uppercase text-[#EEE9DF]/70">Primary Area of Inquiry</label>
                <select
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="w-full px-3 py-2.5 bg-[#090909] border border-[#A62A34]/30 rounded-md text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]"
                >
                  <option value="Career & Long-range Strategy">Career &amp; Long-range Strategy</option>
                  <option value="Interpersonal Alliances & Marriage">Interpersonal Alliances &amp; Marriage</option>
                  <option value="Capital Preservation & Asset Timing">Capital Preservation &amp; Asset Timing</option>
                  <option value="Health & Vital Energy Reserves">Health &amp; Vital Energy Reserves</option>
                </select>
              </div>

              <div className="pt-2">
                <Button variant="primary" size="md" className="w-full" type="submit">
                  Submit Consultation Request
                </Button>
              </div>

              <p className="text-[10px] font-mono text-center text-[#EEE9DF]/40">
                You will receive available scheduling slots within 24 hours.
              </p>
            </form>
          </div>
        ) : (
          <div className="py-8 text-center space-y-4">
            <CheckCircle2 className="w-12 h-12 text-[#B39250] mx-auto" />
            <h3 className="text-xl font-bold text-[#F7F5F0]">Request Received</h3>
            <p className="text-sm text-[#EEE9DF]/75 max-w-xs mx-auto">
              Thank you, {name}. Our private advisory desk has received your request and will follow up with scheduling coordinates.
            </p>
            <div className="pt-4">
              <Button variant="secondary" size="sm" onClick={onClose}>
                Return to Reading
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
