// What changed between two versions of a spec, for the "show changes" view.
import type { Schemas } from "./api/client";

// The API always sends these (they only look optional because they have defaults).
export type Version = Required<
  Pick<Schemas["SpecVersion"], "guidelines" | "attributes" | "coverage_targets" | "coverage_tolerance" | "acceptance_rules">
>;

export type LineChange = { kind: "same" | "added" | "removed"; text: string };
export type Change = { kind: "added" | "removed" | "changed"; text: string; old?: string };

const MAX_LINES = 2000; // longer guidelines are compared as a whole

/** Line-by-line differences (longest common subsequence). */
export function diffLines(before: string, after: string): LineChange[] {
  const a = before ? before.split("\n") : [];
  const b = after ? after.split("\n") : [];
  if (a.length > MAX_LINES || b.length > MAX_LINES) {
    if (before === after) return b.map((text) => ({ kind: "same", text }));
    return [...a.map((text) => ({ kind: "removed" as const, text })), ...b.map((text) => ({ kind: "added" as const, text }))];
  }
  const common: number[][] = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      common[i][j] = a[i] === b[j] ? common[i + 1][j + 1] + 1 : Math.max(common[i + 1][j], common[i][j + 1]);
    }
  }
  const out: LineChange[] = [];
  let i = 0;
  let j = 0;
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) {
      out.push({ kind: "same", text: a[i] });
      i++;
      j++;
    } else if (j < b.length && (i === a.length || common[i][j + 1] >= common[i + 1][j])) {
      out.push({ kind: "added", text: b[j++] });
    } else {
      out.push({ kind: "removed", text: a[i++] });
    }
  }
  return out;
}

const pct = (share: number) => `${Math.round(share * 1000) / 10}%`;

export function ruleText(r: Schemas["AcceptanceRule"]): string {
  const scope = r.applies_to
    ? ` (only ${Object.entries(r.applies_to).map(([k, v]) => `${k}=${v}`).join(", ")})`
    : "";
  return `${r.metric} ${r.operator} ${r.threshold}${scope}`;
}

/** Changes to attributes, coverage targets, tolerance and acceptance rules, in plain words. */
export function diffContent(before: Version, after: Version): Change[] {
  const changes: Change[] = [];

  const oldAttrs = new Map(before.attributes.map((a) => [a.name, a.values]));
  const newAttrs = new Map(after.attributes.map((a) => [a.name, a.values]));
  for (const [name, values] of newAttrs) {
    const old = oldAttrs.get(name);
    if (!old) {
      changes.push({ kind: "added", text: `Attribute ${name}: ${values.join(", ")}` });
      continue;
    }
    const added = values.filter((v) => !old.includes(v));
    const removed = old.filter((v) => !values.includes(v));
    if (added.length) changes.push({ kind: "added", text: `${name}: new value ${added.join(", ")}` });
    if (removed.length) changes.push({ kind: "removed", text: `${name}: value ${removed.join(", ")}` });
  }
  for (const [name, values] of oldAttrs) {
    if (!newAttrs.has(name)) changes.push({ kind: "removed", text: `Attribute ${name}: ${values.join(", ")}` });
  }

  const attrs = new Set([...Object.keys(before.coverage_targets), ...Object.keys(after.coverage_targets)]);
  for (const attr of attrs) {
    const old = before.coverage_targets[attr] ?? {};
    const now = after.coverage_targets[attr] ?? {};
    for (const value of new Set([...Object.keys(old), ...Object.keys(now)])) {
      const label = `Target ${attr}=${value}`;
      if (!(value in old)) changes.push({ kind: "added", text: `${label}: ${pct(now[value])}` });
      else if (!(value in now)) changes.push({ kind: "removed", text: `${label}: ${pct(old[value])}` });
      else if (Math.abs(old[value] - now[value]) > 1e-9) {
        changes.push({ kind: "changed", text: `${label}: ${pct(now[value])}`, old: `${label}: ${pct(old[value])}` });
      }
    }
  }

  if (Math.abs(before.coverage_tolerance - after.coverage_tolerance) > 1e-9) {
    changes.push({
      kind: "changed",
      text: `Tolerance: ${pct(after.coverage_tolerance)}`,
      old: `Tolerance: ${pct(before.coverage_tolerance)}`,
    });
  }

  const oldRules = before.acceptance_rules.map(ruleText);
  const newRules = after.acceptance_rules.map(ruleText);
  for (const r of newRules) if (!oldRules.includes(r)) changes.push({ kind: "added", text: `Rule ${r}` });
  for (const r of oldRules) if (!newRules.includes(r)) changes.push({ kind: "removed", text: `Rule ${r}` });

  return changes;
}
