// Formatting for numbers the API sends (money arrives as text like "25000.00").

export function money(amount: string | number | null | undefined, currency = "USD"): string {
  if (amount === null || amount === undefined || amount === "") return "—";
  const value = typeof amount === "number" ? amount : Number(amount);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: Math.abs(value) < 10 ? 2 : 0,
    minimumFractionDigits: Math.abs(value) < 10 ? 2 : 0,
  }).format(value);
}

export function count(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : value.toLocaleString("en-US");
}

export function points(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(Math.abs(value) < 10 ? 2 : 1)}`;
}

export function percent(share: number | null | undefined, digits = 0): string {
  return share === null || share === undefined ? "—" : `${(share * 100).toFixed(digits)}%`;
}

export function ratio(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${value.toFixed(1)}×`;
}

export function day(iso: string | null | undefined): string {
  if (!iso) return "—";
  // A plain date ("2026-12-15") is a calendar day, not midnight UTC: show that same day.
  const plain = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  const date = plain ? new Date(Number(plain[1]), Number(plain[2]) - 1, Number(plain[3])) : new Date(iso);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/** Today as YYYY-MM-DD in the viewer's time zone. */
export function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** "package_type" -> "package type". */
export function words(name: string): string {
  return name.replace(/_/g, " ");
}

/** Sum money amounts given as [{currency, amount}], per currency, formatted. */
export function amounts(list: { currency: string; amount: string }[] | null | undefined): string {
  if (!list || list.length === 0) return money(0);
  return list.map((a) => money(a.amount, a.currency)).join(" + ");
}

export function kindLabel(kind: string): string {
  return (
    {
      human_vendor: "Human vendors",
      expert_network: "Expert networks",
      synthetic: "Synthetic data",
      rl_environment: "RL environments",
      enterprise_workflow: "Enterprise workflows",
      beta_users: "Testers & beta users",
      licensed_dataset: "Licensed datasets",
    }[kind] ?? kind
  );
}

/** "images" -> "image", for "$1.39 per image". */
export function singular(unit: string): string {
  return unit.endsWith("s") && unit.length > 1 ? unit.slice(0, -1) : unit;
}

export function unitCosts(list: { unit: string; currency: string; amount: string }[]): string {
  return list.map((c) => `${money(c.amount, c.currency)} per ${singular(c.unit)}`).join(", ") || "—";
}
