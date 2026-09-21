export const metadata = {
  title: 'Terms | KAVACH',
  description: 'The terms that apply when you use KAVACH.',
};

const SECTION = 'mt-6';
const HEADING = 'font-mono text-[10px] uppercase tracking-[0.2em] text-[#B39250]';
const BODY = 'mt-2 text-[13.5px] leading-relaxed text-[#EEE9DF]/70';

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <div className="mx-auto w-full max-w-3xl px-6 py-12">
        <div className="font-mono text-[9.5px] uppercase tracking-[0.24em] text-[#B39250]">KAVACH</div>
        <h1 className="mt-3 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0]">TERMS OF USE</h1>

        <section className={SECTION}>
          <h2 className={HEADING}>Using KAVACH</h2>
          <p className={BODY}>
            KAVACH provides astrological calculations and interpretive guidance. You may use the service
            for personal reflection and general guidance.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Nature Of The Content</h2>
          <p className={BODY}>
            Readings describe tendencies and possibilities within an astrological framework. They are
            interpretive rather than factual statements about the future, and they are not a substitute
            for medical, legal, financial or other professional advice.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>No Guarantee Of Outcomes</h2>
          <p className={BODY}>
            No result, event or outcome is guaranteed. Decisions you take remain your own responsibility.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Your Inputs</h2>
          <p className={BODY}>
            You are responsible for the accuracy of the birth details and locations you enter, since the
            calculations depend on them. Do not use the service to make decisions where professional
            advice is required.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Content And Availability</h2>
          <p className={BODY}>
            The service, its content and its presentation belong to KAVACH. Features may change, be
            limited, or be temporarily unavailable while the product is developed.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Contact</h2>
          <p className={BODY}>
            For questions about these terms, please use the contact channel published on this website.
          </p>
        </section>

        <p className="mt-8 text-[11px] text-[#EEE9DF]/35">
          These terms describe the current service and may need review before launch.
        </p>
      </div>
    </main>
  );
}
