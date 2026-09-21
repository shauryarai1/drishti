import Link from 'next/link';

export const metadata = { title: 'Page Not Found | KAVACH' };

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#090909] px-6 text-[#EEE9DF] architectural-grid">
      <div className="w-full max-w-lg rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/70 p-8 text-center">
        <div className="font-mono text-[9.5px] uppercase tracking-[0.24em] text-[#B39250]">
          KAVACH <span className="text-[#A62A34]">&bull;</span> Not Found
        </div>
        <h1 className="mt-3 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0]">PAGE NOT FOUND</h1>
        <p className="mt-2 text-[13.5px] leading-relaxed text-[#EEE9DF]/55">
          This path isn&apos;t part of KAVACH.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/"
            className="rounded bg-[#7B1D26] px-5 py-2.5 font-mono text-[10.5px] uppercase tracking-[0.16em] text-[#F7F5F0] hover:bg-[#A62A34]"
          >
            Return Home
          </Link>
          <Link
            href="/ask"
            className="rounded border border-[#A62A34]/40 px-5 py-2.5 font-mono text-[10.5px] uppercase tracking-[0.16em] text-[#EEE9DF]/70 hover:text-[#D6BE85]"
          >
            Ask KAVACH
          </Link>
        </div>
      </div>
    </main>
  );
}
