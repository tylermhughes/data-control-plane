import { useSession } from "../session";

/** For admins viewing "All projects": choose which project a new thing goes in. Otherwise nothing. */
export function ProjectField({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  const { projectId, projects } = useSession();
  if (projectId) return null;
  return (
    <label className="field">
      <span>Project</span>
      <select className="input" value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Choose a project…</option>
        {projects.map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
    </label>
  );
}
