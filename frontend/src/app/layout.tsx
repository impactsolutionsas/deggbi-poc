import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import Link from "next/link";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "DeggBi AI — Dashboard",
  description: "Détection de deepfakes et vérification de contenus — La Vérité en Wolof",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className={`${geistSans.variable} font-sans antialiased bg-[var(--background)] text-[var(--foreground)]`}>
        <nav className="bg-[var(--nav-bg)] border-b border-[var(--card-border)] sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-5 sm:px-8">
            <div className="flex items-center justify-between h-14">
              <Link href="/" className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                  <span className="text-white text-sm font-bold">D</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-base font-semibold text-[var(--foreground)] tracking-tight">DeggBi</span>
                  <span className="text-[11px] text-[var(--muted-light)] font-medium">La Vérité</span>
                </div>
              </Link>
              <div className="flex gap-1">
                <Link href="/" className="text-sm text-[var(--muted)] hover:text-[var(--foreground)] px-3 py-1.5 rounded-md hover:bg-[var(--surface)] transition-all">
                  Dashboard
                </Link>
                <Link href="/analyses" className="text-sm text-[var(--muted)] hover:text-[var(--foreground)] px-3 py-1.5 rounded-md hover:bg-[var(--surface)] transition-all">
                  Analyses
                </Link>
                <Link href="/analyze" className="text-sm text-white bg-gradient-to-r from-emerald-500 to-teal-600 px-3 py-1.5 rounded-md hover:from-emerald-600 hover:to-teal-700 transition-all">
                  Analyser
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
