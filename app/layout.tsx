import './globals.css';
import type { Metadata, Viewport } from 'next';
import { Manrope } from 'next/font/google';
import { getUser } from '@/lib/db/queries';
import { SWRConfig } from 'swr';
import Header from '@/components/header';
import { ThemeProvider } from '@/contexts/theme-context';
import { siteConfig } from '@/lib/config';

export const metadata: Metadata = {
  title: siteConfig.title,
  description: siteConfig.description
};

export const viewport: Viewport = {
  maximumScale: 1
};

const manrope = Manrope({ subsets: ['latin'], display: 'swap' });

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${manrope.className}`}
    >
      <body className="min-h-[100dvh] bg-background text-foreground">
        <ThemeProvider>
          <SWRConfig
            value={{
              fallback: {
                '/api/user': getUser()
              }
            }}
          >
            <div className="flex flex-col min-h-screen">
              <Header />
              {children}
            </div>
          </SWRConfig>
        </ThemeProvider>
      </body>
    </html>
  );
}
