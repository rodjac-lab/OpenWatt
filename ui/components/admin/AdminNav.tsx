import type { AdminSection } from "../../app/admin/types";

interface AdminNavProps {
  sections: AdminSection[];
  healthStatus: string | null | undefined;
  onRefresh: () => void;
}

export function AdminNav({ sections, healthStatus, onRefresh }: AdminNavProps) {
  return (
    <nav className="admin-nav">
      <div className="admin-nav__brand">
        <span className="brand-icon">⚡</span>
        <strong>OpenWatt</strong>
      </div>
      <div className="admin-nav__tabs">
        {sections.map((section) => (
          <a key={section.id} href={`#${section.id}`}>
            {section.label}
          </a>
        ))}
      </div>
      <div className="admin-nav__actions">
        <span className="pill">{healthStatus === "ok" ? "API OK" : "API ?"}</span>
        <button className="btn btn--ghost" onClick={onRefresh}>
          Rafraîchir
        </button>
      </div>
    </nav>
  );
}
