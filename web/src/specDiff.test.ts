import { describe, expect, it } from "vitest";

import { diffContent, diffLines } from "./specDiff";
import type { Version } from "./specDiff";

const base: Version = {
  guidelines: "",
  attributes: [{ name: "package_type", values: ["box", "mailer"], description: "" }],
  coverage_targets: { package_type: { box: 0.5, mailer: 0.5 } },
  coverage_tolerance: 0.05,
  acceptance_rules: [{ metric: "agreement", operator: ">=", threshold: 0.85, applies_to: null, description: "" }],
};

describe("diffLines", () => {
  it("marks added and removed lines and keeps the rest", () => {
    expect(diffLines("a\nb\nc", "a\nB\nc\nd")).toEqual([
      { kind: "same", text: "a" },
      { kind: "added", text: "B" },
      { kind: "removed", text: "b" },
      { kind: "same", text: "c" },
      { kind: "added", text: "d" },
    ]);
  });
});

describe("diffContent", () => {
  it("lists changed targets, new values, tolerance and rules in plain words", () => {
    const after: Version = {
      ...base,
      attributes: [{ name: "package_type", values: ["box", "mailer", "shrink_wrapped"], description: "" }],
      coverage_targets: { package_type: { box: 0.3, mailer: 0.35, shrink_wrapped: 0.35 } },
      coverage_tolerance: 0.03,
      acceptance_rules: [{ metric: "duplicate_rate", operator: "<=", threshold: 0.02, applies_to: null, description: "" }],
    };
    expect(diffContent(base, after)).toEqual([
      { kind: "added", text: "package_type: new value shrink_wrapped" },
      { kind: "changed", text: "Target package_type=box: 30%", old: "Target package_type=box: 50%" },
      { kind: "changed", text: "Target package_type=mailer: 35%", old: "Target package_type=mailer: 50%" },
      { kind: "added", text: "Target package_type=shrink_wrapped: 35%" },
      { kind: "changed", text: "Tolerance: 3%", old: "Tolerance: 5%" },
      { kind: "added", text: "Rule duplicate_rate <= 0.02" },
      { kind: "removed", text: "Rule agreement >= 0.85" },
    ]);
    expect(diffContent(base, base)).toEqual([]);
  });
});
