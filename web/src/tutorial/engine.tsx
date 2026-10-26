// The guided tutorial: a card that walks through the app step by step, highlights the part of
// the screen each step is about, and ticks off "your turn" steps once DCP's event log shows the
// user did them. Steps are defined in steps.tsx; this file is the machinery.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useLocation, useNavigate } from "react-router";

import { ApiError, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { useSession } from "../session";

export type Vars = Record<string, string | undefined>;

export interface Ctx {
  vars: Vars;
  /** When the user reached this step (a little earlier, to allow for clock differences). */
  since: string;
  pathname: string;
  session: ReturnType<typeof useSession>;
}

/** True or some vars to remember once the step is done; false while waiting. */
export type Check = (ctx: Ctx) => Promise<boolean | Vars> | boolean | Vars;

export interface Step {
  id: string;
  chapter: string;
  title: string;
  body: ReactNode | ((vars: Vars) => ReactNode);
  /** Go here when the step starts. */
  go?: (vars: Vars) => string | null;
  /** Offer "Take me there" when the user isn't here. */
  path?: (vars: Vars) => string | null;
  /** CSS selector(s) of what to highlight; the first match on the page wins. */
  target?: string;
  /** For "your turn" steps: what to do, and how to tell it's done. */
  task?: string;
  done?: Check;
  /** A button that does something for the user (e.g. simulates a vendor's system). */
  action?: { label: string | ((vars: Vars) => string); run: (ctx: Ctx) => Promise<Vars | void> };
}

interface State {
  active: boolean;
  index: number;
  vars: Vars;
  done: string[];
  started: Record<string, string>;
  minimized: boolean;
}

const STORAGE = "dcp.tutorial";
const POLL_MS = 1500;
const CLOCK_MARGIN_MS = 5_000;

const EMPTY: State = { active: false, index: 0, vars: {}, done: [], started: {}, minimized: false };

function load(): State {
  try {
    const saved = localStorage.getItem(STORAGE);
    return saved ? { ...EMPTY, ...(JSON.parse(saved) as Partial<State>) } : EMPTY;
  } catch {
    return EMPTY;
  }
}

function save(state: State): void {
  try {
    localStorage.setItem(STORAGE, JSON.stringify(state));
  } catch {
    /* not remembered; that's fine */
  }
}

/** The newest event of `type` since `since` (optionally matching), or undefined. */
export async function eventSince(
  type: string,
  since: string,
  options: { projectId?: string; match?: (e: Schemas["Event"]) => boolean } = {},
): Promise<Schemas["Event"] | undefined> {
  const events = await listAll<Schemas["Event"]>("/v1/events", { type, project_id: options.projectId });
  const from = Date.parse(since);
  return events.filter((e) => Date.parse(e.created_at) >= from && (!options.match || options.match(e))).pop();
}

interface Tutorial {
  steps: Step[];
  state: State;
  start: (fromStepId?: string) => void;
  stop: () => void;
  goTo: (index: number) => void;
}

const TutorialContext = createContext<Tutorial | null>(null);

export function useTutorial(): Tutorial {
  const tutorial = useContext(TutorialContext);
  if (!tutorial) throw new Error("useTutorial must be used inside TutorialProvider");
  return tutorial;
}

export function TutorialProvider({ steps, children }: { steps: Step[]; children: ReactNode }) {
  const [state, setState] = useState<State>(load);
  const navigate = useNavigate();
  useEffect(() => save(state), [state]);

  const goTo = useCallback(
    (index: number) => {
      const step = steps[Math.max(0, Math.min(index, steps.length - 1))];
      setState((s) => {
        const vars = s.vars;
        const target = step.go?.(vars);
        if (target) setTimeout(() => navigate(target), 0);
        const started = s.started[step.id] ? s.started : { ...s.started, [step.id]: new Date().toISOString() };
        return { ...s, active: true, minimized: false, index: steps.indexOf(step), started };
      });
    },
    [steps, navigate],
  );

  const value = useMemo<Tutorial>(
    () => ({
      steps,
      state,
      start: (fromStepId) => {
        const at = fromStepId ? steps.findIndex((s) => s.id === fromStepId) : state.index;
        goTo(at < 0 ? 0 : at);
      },
      stop: () => setState((s) => ({ ...s, active: false })),
      goTo,
    }),
    [steps, state, goTo],
  );

  return (
    <TutorialContext.Provider value={value}>
      {children}
      {state.active && <TutorialCard state={state} setState={setState} steps={steps} goTo={goTo} />}
    </TutorialContext.Provider>
  );
}

function useSpotlight(selector: string | undefined, stepId: string, enabled: boolean) {
  const scrolledFor = useRef<string | null>(null);
  useEffect(() => {
    if (!selector || !enabled) return;
    let current: Element | null = null;
    const apply = () => {
      const found = document.querySelector(selector);
      if (found === current) return;
      current?.classList.remove("tour-on");
      current = found;
      if (!found) return;
      found.classList.add("tour-on");
      if (scrolledFor.current !== stepId) {
        scrolledFor.current = stepId;
        found.scrollIntoView?.({ block: "center", behavior: matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      }
    };
    apply();
    const timer = setInterval(apply, 400); // pages load their data after they appear
    return () => {
      clearInterval(timer);
      current?.classList.remove("tour-on");
    };
  }, [selector, stepId, enabled]);
}

function TutorialCard({
  state,
  setState,
  steps,
  goTo,
}: {
  state: State;
  setState: (update: (s: State) => State) => void;
  steps: Step[];
  goTo: (index: number) => void;
}) {
  const session = useSession();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [showChapters, setShowChapters] = useState(false);
  const [running, setRunning] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const step = steps[state.index];
  const isDone = state.done.includes(step.id);
  const since = new Date(Date.parse(state.started[step.id] ?? new Date().toISOString()) - CLOCK_MARGIN_MS).toISOString();
  const ctx: Ctx = { vars: state.vars, since, pathname, session };
  const ctxRef = useRef(ctx);
  ctxRef.current = ctx;

  useSpotlight(step.target, step.id, !state.minimized);
  useEffect(() => setProblem(null), [step.id]);

  const markDone = useCallback(
    (found: boolean | Vars | void) => {
      if (!found) return;
      setState((s) => ({
        ...s,
        vars: typeof found === "object" ? { ...s.vars, ...found } : s.vars,
        done: s.done.includes(step.id) ? s.done : [...s.done, step.id],
      }));
    },
    [setState, step.id],
  );

  // Watch for "your turn" steps being done.
  useEffect(() => {
    if (!step.done || isDone) return;
    let stopped = false;
    const check = async () => {
      try {
        const found = await step.done!(ctxRef.current);
        if (!stopped) markDone(found);
      } catch {
        /* try again on the next tick */
      }
    };
    void check();
    const timer = setInterval(check, POLL_MS);
    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [step, isDone, pathname, markDone]);

  const runAction = async () => {
    if (!step.action) return;
    setRunning(true);
    setProblem(null);
    try {
      const vars = await step.action.run(ctxRef.current);
      markDone(vars ?? true);
    } catch (e) {
      setProblem(e instanceof ApiError ? (e.problem.detail ?? e.message) : (e as Error).message);
    } finally {
      setRunning(false);
    }
  };

  const chapters = [...new Set(steps.map((s) => s.chapter))];
  const chapterIndex = chapters.indexOf(step.chapter);
  const there = step.path?.(state.vars);
  const last = state.index === steps.length - 1;
  const waiting = Boolean(step.done || step.action) && !isDone;
  const body = typeof step.body === "function" ? step.body(state.vars) : step.body;
  const actionLabel = step.action && (typeof step.action.label === "function" ? step.action.label(state.vars) : step.action.label);

  if (state.minimized) {
    return (
      <button
        type="button"
        className="tourpill"
        onClick={() => setState((s) => ({ ...s, minimized: false }))}
        aria-label="Show the tutorial"
      >
        Tutorial · step {state.index + 1} of {steps.length}
        {waiting ? " · your turn" : ""}
      </button>
    );
  }

  return (
    <div className="tourcard" role="dialog" aria-label="Tutorial" aria-live="polite">
      <div className="tourhead">
        <div className="step">
          {chapterIndex}. {step.chapter} · step {state.index + 1} of {steps.length}
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          <button type="button" className="x" aria-label="Minimize the tutorial" title="Minimize" onClick={() => setState((s) => ({ ...s, minimized: true }))}>
            –
          </button>
          <button type="button" className="x" aria-label="Close the tutorial" title="Close (your progress is kept)" onClick={() => setState((s) => ({ ...s, active: false }))}>
            ×
          </button>
        </div>
      </div>
      <div className="tourprogress" aria-hidden="true">
        <i style={{ width: `${((state.index + 1) / steps.length) * 100}%` }} />
      </div>
      {showChapters ? (
        <ol className="tourchapters" aria-label="Chapters">
          {chapters.map((c, i) => {
            const own = steps.filter((s) => s.chapter === c);
            const complete = own.every((s) => !(s.done || s.action) || state.done.includes(s.id));
            return (
              <li key={c}>
                <button
                  type="button"
                  aria-current={c === step.chapter}
                  onClick={() => {
                    setShowChapters(false);
                    goTo(steps.indexOf(own[0]));
                  }}
                >
                  <span>{i}. {c}</span>
                  <span className="muted">{complete && state.done.some((d) => own.some((s) => s.id === d)) ? "✓" : `${own.length} steps`}</span>
                </button>
              </li>
            );
          })}
          <li>
            <button
              type="button"
              onClick={() => {
                setShowChapters(false);
                setState(() => ({ ...EMPTY, active: true, started: { [steps[0].id]: new Date().toISOString() } }));
              }}
            >
              <span>Start over</span>
              <span className="muted">clears ticks and progress</span>
            </button>
          </li>
        </ol>
      ) : (
        <>
          <h3>{step.title}</h3>
          <div className="tourbody">{body}</div>
          {step.task && (
            <div className={`tourtask${isDone ? " done" : ""}`} role="status">
              {isDone ? "✓ Done" : `Your turn: ${step.task}`}
            </div>
          )}
          {problem && <div className="notice bad" role="alert">{problem}</div>}
        </>
      )}
      <div className="touractions">
        <button type="button" className="btn" onClick={() => setShowChapters((v) => !v)}>
          {showChapters ? "Back to the step" : "Chapters"}
        </button>
        <div className="spacer" />
        {state.index > 0 && (
          <button type="button" className="btn" onClick={() => goTo(state.index - 1)}>
            Back
          </button>
        )}
        {there && pathname !== there && !isDone && (
          <button type="button" className="btn" onClick={() => navigate(there)}>
            Take me there
          </button>
        )}
        {step.action && !isDone && (
          <button type="button" className="btn primary" disabled={running} onClick={() => void runAction()}>
            {running ? "Working…" : actionLabel}
          </button>
        )}
        <button
          type="button"
          className={`btn${waiting && step.action ? "" : " primary"}`}
          onClick={() => (last ? setState((s) => ({ ...s, active: false })) : goTo(state.index + 1))}
        >
          {last ? "Finish" : waiting ? "Skip" : "Next"}
        </button>
      </div>
    </div>
  );
}
