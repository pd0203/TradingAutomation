import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Trading Dashboard",
  description: "View live prices and start automated trading",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-black text-yellow-400`}>
        {children}
      </body>
    </html>
  );
}
