import { useEffect } from "react";
import type { ReactNode } from "react";

/** A panel that slides over the right side of the page. Escape or the backdrop closes it. */
export function Drawer({
  label,
  title,
  kicker,
  onClose,
  children,
}: {
  label: string;
  title: ReactNode;
  kicker?: ReactNode;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <>
      <button type="button" className="scrim" aria-label="Close" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label={label}>
        <div className="drawer-head">
          <div>
            {kicker && <div className="mono muted">{kicker}</div>}
            <h2 style={{ margin: "4px 0 0" }}>{title}</h2>
          </div>
          <button type="button" className="x" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </div>
        {children}
      </aside>
    </>
  );
}
