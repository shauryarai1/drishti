export const metadata = {
  title: 'Privacy | KAVACH',
  description: 'How KAVACH handles the information you provide when you request a reading.',
};

const SECTION = 'mt-6';
const HEADING = 'font-mono text-[10px] uppercase tracking-[0.2em] text-[#B39250]';
const BODY = 'mt-2 text-[13.5px] leading-relaxed text-[#EEE9DF]/70';

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <div className="mx-auto w-full max-w-3xl px-6 py-12">
        <div className="font-mono text-[9.5px] uppercase tracking-[0.24em] text-[#B39250]">KAVACH</div>
        <h1 className="mt-3 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0]">PRIVACY</h1>
        <p className={BODY}>
          This page explains, in plain language, how KAVACH handles information at this stage of the
          product. It describes the current implementation and is not legal advice.
        </p>

        <section className={SECTION}>
          <h2 className={HEADING}>Information You Provide</h2>
          <p className={BODY}>
            To generate a reading you enter birth details such as date, time and place of birth, and a
            location for time-sensitive features. These details are required for the calculation to run.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>How It Is Used</h2>
          <p className={BODY}>
            Birth and location details are sent to the KAVACH service so the requested reading can be
            calculated and returned to your browser. Location searches are resolved through a place
            lookup service to obtain coordinates.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>What Is Retained</h2>
          <p className={BODY}>
            When you submit a request to a KAVACH tool, the information you submitted and the result that
            was generated may be retained. This includes chart requests and the generated chart result,
            submitted Ask KAVACH questions and the responses returned, and the inputs and outputs of the
            Daily, Weekly, Life Summary, Panchang and reading tools. Retained records are used for
            operating and supporting the service, keeping records of what was generated, security, and
            improving the product.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Who Can Access It</h2>
          <p className={BODY}>
            Retained submissions and generated results are private to KAVACH and may be accessed by
            authorised KAVACH administrators for the purposes above. This means that, as well as yourself
            when you are signed in, authorised administrators can inspect the information you submitted
            and the result you received. Requests, readings and questions are not kept private from
            authorised administrators.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>What Is Not Retained</h2>
          <p className={BODY}>
            Submission records do not contain passwords, authentication tokens, session cookies,
            authorisation headers, API keys or payment information. Passwords are handled entirely by the
            authentication provider and are never part of this record. Only information you explicitly
            submit and the result generated from it are retained; text that you are still typing and
            requests you never send are not captured.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Where It Is Handled</h2>
          <p className={BODY}>
            Readings are calculated by the KAVACH application service. The conversational feature sends
            your message and recent conversation context to a third-party language model provider so a
            reply can be generated. Retained submissions are stored with our database provider. Some
            interface preferences (for example a selected city or Moon sign) are kept in your
            browser&apos;s local storage.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Retention</h2>
          <p className={BODY}>
            Retained submissions are kept for as long as the service needs them for the purposes
            described above, and in line with applicable privacy requirements. There is no fixed
            automatic deletion period in place at this stage. Individual records can be deleted on
            request, and a request to delete your information will be honoured according to those same
            requirements. Conversation context used by the assistant is held in memory for the running
            service and is not intended as permanent storage.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Accounts</h2>
          <p className={BODY}>
            Accounts are optional. If you create one, your saved charts and readings are kept private to
            your account, and remaining signed in associates your submissions with your account rather
            than with an anonymous visitor.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Updates</h2>
          <p className={BODY}>
            This policy will be updated as the product changes, including if automatic retention limits,
            payments or additional services are introduced.
          </p>
        </section>

        <section className={SECTION}>
          <h2 className={HEADING}>Contact</h2>
          <p className={BODY}>
            For privacy questions or to request deletion, please use the contact channel published on
            this website.
          </p>
        </section>

        <p className="mt-8 text-[11px] text-[#EEE9DF]/35">
          This page describes the current implementation and may need review before launch.
        </p>
      </div>
    </main>
  );
}
