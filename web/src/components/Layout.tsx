import { NavLink, Outlet } from "react-router";

import { useSession } from "../session";
import { useTutorial } from "../tutorial/engine";

const SECTIONS = [
  {
    label: "Work",
    links: [
      ["/board", "Program board"],
      ["/requests", "Requests"],
      ["/specs", "Specs"],
    ],
  },
  {
    label: "Data",
    links: [
      ["/sources", "Sources & vendors"],
      ["/lineage", "Lineage & spend"],
    ],
  },
  {
    label: "Results",
    links: [["/portfolio", "Portfolio"]],
  },
  {
    label: "Admin",
    links: [["/settings", "Settings"]],
  },
] as const;

export function Layout() {
  const { me, projects, projectId, chooseProject, signOut } = useSession();
  const isAdmin = me?.role === "admin";
  const tutorial = useTutorial();
  return (
    <>
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden="true" />
          Data Control Plane
        </div>
        {isAdmin ? (
          <select
            aria-label="Project"
            value={projectId ?? ""}
            onChange={(e) => chooseProject(e.target.value || null)}
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        ) : (
          <span className="who">{projects.find((p) => p.id === projectId)?.name ?? ""}</span>
        )}
        <div className="spacer" />
        <button className="btn" type="button" data-tour="tutorial" onClick={() => tutorial.start()}>
          Tutorial
        </button>
        {me && (
          <span className="who" title={me.id}>
            {me.name} · {me.access === "write" ? "can edit" : "read only"}
          </span>
        )}
        <button className="btn" type="button" onClick={signOut}>
          Sign out
        </button>
      </header>
      <div className="shell">
        <nav className="side" aria-label="Main">
          {SECTIONS.map((section) => (
            <div key={section.label} style={{ display: "contents" }}>
              <div className="label">{section.label}</div>
              {section.links.map(([to, label]) => (
                <NavLink key={to} to={to} className={({ isActive }) => `nav${isActive ? " active" : ""}`}>
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <main>
          <Outlet />
        </main>
      </div>
    </>
  );
}
