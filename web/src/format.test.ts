import { describe, expect, it } from "vitest";

import { amounts, count, day, kindLabel, money, percent, points, ratio, unitCosts } from "./format";

describe("format", () => {
  it("formats money from the API's text form", () => {
    expect(money("25000.00")).toBe("$25,000");
    expect(money("1.3267")).toBe("$1.33");
    expect(money(null)).toBe("—");
    expect(amounts([{ currency: "USD", amount: "13400.00" }])).toBe("$13,400");
  });
  it("formats counts, points, shares and ratios", () => {
    expect(count(10100)).toBe("10,100");
    expect(points(4.5)).toBe("+4.50");
    expect(points(-0.4)).toBe("-0.40");
    expect(percent(0.355)).toBe("36%");
    expect(ratio(15.62)).toBe("15.6×");
  });
  it("says cost per unit in plain English", () => {
    expect(unitCosts([{ unit: "images", currency: "USD", amount: "1.3267" }])).toBe("$1.33 per image");
    expect(unitCosts([])).toBe("—");
  });
  it("names source kinds in plain English", () => {
    expect(kindLabel("enterprise_workflow")).toBe("Enterprise workflows");
  });
});

describe("day", () => {
  it("shows a plain date as that calendar day, whatever the time zone", () => {
    expect(day("2026-12-15")).toBe("Dec 15, 2026");
  });
});
