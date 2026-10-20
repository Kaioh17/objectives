import { siteConfig } from "@/config/site";

export function SiteFooter({ dock = false }: { dock?: boolean }) {
  return (
    <footer className={`shell site-footer${dock ? " has-dock" : ""}`}>
      <p>{siteConfig.name} is a personal project by Mubaraq.</p>
    </footer>
  );
}
