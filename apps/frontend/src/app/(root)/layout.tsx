import ChatWindow from "@/components/chat/ChatWindow";
import BackToTop from "@/components/shared/BackToTop";
import Footer from "@/components/shared/Footer";
import NavigationMenu from "@/components/shared/NavigationMenu";

export default function Layout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <main>
      <div className="max-w-[1440px] mx-auto">
        <NavigationMenu />
        <div className="pt-20">{children}</div>
        <ChatWindow />
        <BackToTop />
        <Footer />
      </div>
    </main>
  );
}
