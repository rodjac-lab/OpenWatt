import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenWatt UI",
  description: "Comparator for French electricity tariffs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
