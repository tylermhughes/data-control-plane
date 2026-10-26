// The tutorial's journey through every part of DCP, in the order of the core loop:
// results → work → specs → requests → sources → deliveries → datasets → evals → results again.
import type { Schemas } from "../api/client";
import { eventSince } from "./engine";
import type { Ctx, Step, Vars } from "./engine";
import { registerDelivery, sendSignedDelivery } from "./simulate";

const DEMO = "North-star demo";

/** Done when an event of `type` happened since the step started, in the tutorial's project. */
export function event(
  type: string,
  options: { match?: (e: Schemas["Event"], vars: Vars) => boolean; save?: (e: Schemas["Event"]) => Vars; anyProject?: boolean } = {},
) {
  return async (ctx: Ctx) => {
    const found = await eventSince(type, ctx.since, {
      projectId: options.anyProject ? undefined : ctx.vars.projectId,
      match: options.match && ((e) => options.match!(e, ctx.vars)),
    });
    return found ? (options.save?.(found) ?? true) : false;
  };
}

const onPath = (pattern: RegExp) => (ctx: Ctx) => pattern.test(ctx.pathname);
const seen = (selector: string) => () => document.querySelector(selector) !== null;
const field = (e: Schemas["Event"], name: string) => (e.data as Record<string, unknown>)[name];

export function newestDemo(projects: Schemas["Project"][]): Schemas["Project"] | undefined {
  return projects.filter((p) => p.name.startsWith(DEMO)).sort((a, b) => b.created_at.localeCompare(a.created_at))[0];
}

export const STEPS: Step[] = [
  // --- Welcome ---------------------------------------------------------------------------------
  {
    id: "welcome",
    chapter: "Welcome",
    title: "Welcome to Data Control Plane",
    body: (
      <>
        <p>
          DCP decides what training data to get and from where, checks what arrives, controls what reaches training, and
          shows which data spend actually improved your models.
        </p>
        <p>
          This tutorial follows one complete journey: <b>results → a new data request → a spec → splitting it across sources
          → deliveries arriving → accept or reject → a frozen dataset → an eval result → results again</b>, then the admin
          tools.
        </p>
        <p>
          Highlighted areas show where to look. <b>"Your turn"</b> steps tick themselves off when you've done them. You can
          skip, go back, minimize (–) or close (×) any time; your place is kept.
        </p>
      </>
    ),
    target: "[data-tour='tutorial']",
  },
  {
    id: "demo-project",
    chapter: "Welcome",
    title: "Use the demo project",
    body: (
      <>
        <p>
          The tutorial runs in the <b>{DEMO}</b> project: a fictional fulfillment team improving a model that spots damaged
          packages. It already has three vendors' deliveries, quality checks, dataset versions and eval results, so there's
          something real to explore, and you'll add your own work on top.
        </p>
        <p>
          Not in the list? With DCP running, paste this in a Terminal (with your admin key), then reload this page:
          <br />
          <code className="mono">DCP_API_KEY=… python3 scripts/demo.py --diagnosis</code>
        </p>
      </>
    ),
    target: "select[aria-label='Project']",
    task: "pick the newest “North-star demo” project at the top (or use the button)",
    done: (ctx) => {
      const current = ctx.session.projects.find((p) => p.id === ctx.session.projectId);
      return current?.name.startsWith(DEMO) ? { projectId: current.id } : false;
    },
    action: {
      label: "Switch to the demo project",
      run: async (ctx) => {
        const demo = newestDemo(ctx.session.projects);
        if (!demo) throw new Error("There's no North-star demo project yet. Run scripts/demo.py --diagnosis first (see above).");
        ctx.session.chooseProject(demo.id);
        return { projectId: demo.id };
      },
    },
  },

  // --- 1. Results ------------------------------------------------------------------------------
  {
    id: "portfolio-totals",
    chapter: "Start with the results",
    title: "The portfolio: what the data spend bought",
    body: (
      <p>
        Everything in DCP leads here. The top line shows total <b>data spend</b>, the <b>usable units</b> it bought (items
        that passed checks), the business <b>value of the eval gains</b>, and the <b>return</b> on the spend that has been
        scored by an eval.
      </p>
    ),
    go: () => "/portfolio",
    target: "[aria-label='Totals']",
  },
  {
    id: "portfolio-capability",
    chapter: "Start with the results",
    title: "Per capability: cost, eval change, points per $10K",
    body: (
      <>
        <p>
          A <b>capability</b> is something a model should get better at, with one eval metric. For each one: the cost per
          usable unit, how many points the eval moved, and the key efficiency figure: <b>points per $10K</b> of data spend.
          Value = points × what a point is worth; ROI = value ÷ spend.
        </p>
        <p>Every number comes with the IDs of the batches, dataset versions and eval results behind it (in the API).</p>
      </>
    ),
    target: "[data-tour='by-capability']",
  },
  {
    id: "portfolio-kinds",
    chapter: "Start with the results",
    title: "Per source type, honestly labelled",
    body: (
      <p>
        Which kinds of source pulled their weight: vendors, internal workflows, synthetic data and so on. When several
        sources fed one dataset version, the eval change is split by each one's share of the new items, so it's marked as
        an <b>estimate</b>.
      </p>
    ),
    target: "[data-tour='by-source-kind']",
  },
  {
    id: "portfolio-diagnosis",
    chapter: "Start with the results",
    title: "The diagnosis: is the spend still paying off?",
    body: (
      <>
        <p>
          DCP looks at each new dataset version's points per $10K. Here returns are <b>flattening</b>, and the cause is the
          data mix: too few shrink-wrapped packages against the spec's target. So the advice is to <b>refine the spec</b>,
          not just buy more, with suggested new targets.
        </p>
        <p>
          <b>Draft the refined spec</b> turns the suggestion into a draft spec version for a person to review. (If a draft
          already exists, you'll review it in the Specs chapter.)
        </p>
      </>
    ),
    target: "[data-testid='diagnosis']",
  },

  // --- 2. Board --------------------------------------------------------------------------------
  {
    id: "board-open",
    chapter: "See all the work",
    title: "The Program board",
    body: <p>The board shows every request and every piece of allocated work, from every source, from intake to delivery.</p>,
    target: "a.nav[href='/board']",
    task: "open Program board in the menu",
    done: onPath(/^\/board/),
  },
  {
    id: "board-columns",
    chapter: "See all the work",
    title: "From request to delivered",
    body: (
      <p>
        <b>Requests</b> not yet split across sources, then each source's share of the work: <b>Planned</b>, <b>In
        production</b>, <b>In QA</b> (a delivery is waiting for a decision) and <b>Delivered</b>. The coloured edge is the
        source type; the bar shows accepted units against what was ordered. Red and amber notes flag failed checks, waiting
        decisions, vendor overrides and overdue work.
      </p>
    ),
    go: () => "/board",
    target: ".board",
  },
  {
    id: "board-filter",
    chapter: "See all the work",
    title: "Filter by source type",
    body: <p>One registry, many kinds of source. Narrow the board to one kind to compare like with like.</p>,
    target: "[aria-label='Filter by source type']",
    task: "click a source type, e.g. Human vendors",
    done: seen("[aria-label='Filter by source type'] button[aria-pressed='true']:not(:first-child)"),
  },
  {
    id: "board-card",
    chapter: "See all the work",
    title: "Open a card",
    body: <p>Each card opens its details: the quote, what's been delivered and accepted, spend so far, and every delivery.</p>,
    target: "[aria-label='In production'], .board",
    task: "click All sources, then any card in In production",
    done: seen("[role='dialog'][aria-label='Details']"),
  },
  {
    id: "delivery-open",
    chapter: "See all the work",
    title: "Open a delivery",
    body: <p>A delivery (a "batch") is one shipment of data against an allocation. Let's look inside one.</p>,
    target: "[role='dialog'][aria-label='Details']",
    task: "click a delivery under Deliveries",
    done: onPath(/^\/batches\//),
  },

  // --- 3. A delivery ---------------------------------------------------------------------------
  {
    id: "batch-checks",
    chapter: "Inside a delivery",
    title: "Automated quality checks",
    body: (
      <p>
        When a delivery arrives with files, DCP checks it automatically: can the files be read, the record format, the
        spec's schema, duplicates (also against earlier deliveries), statistics, attribute counts, and the spec's acceptance
        rules. DCP stores pointers and results, never the data itself. <b>Run checks again</b> re-checks a fixed file.
      </p>
    ),
    target: "[aria-label='Quality checks']",
  },
  {
    id: "batch-coverage",
    chapter: "Inside a delivery",
    title: "Coverage against the spec's targets",
    body: (
      <p>
        The spec says what mix of data it wants (e.g. 35% shrink-wrapped). Each bar is this delivery's share, the tick is
        the target, and amber means too far below it. Gaps like this are exactly what the portfolio's diagnosis picked up.
      </p>
    ),
    target: "[aria-label='Coverage']",
  },
  {
    id: "batch-decision",
    chapter: "Inside a delivery",
    title: "The decision, and who made it",
    body: (
      <p>
        Someone accepts a delivery (keeping some or all of it) or rejects it with a reason. Accepting one that failed its
        checks needs a written reason. Decisions made in a vendor's own QA can be imported, and are marked as such.
      </p>
    ),
    target: "[aria-label='Decision']",
  },
  {
    id: "batch-history",
    chapter: "Inside a delivery",
    title: "Every change is recorded",
    body: (
      <p>
        Each change in DCP is saved as an event: an audit trail you can read here or through the API, and can have sent to
        your other tools as signed webhooks (set up in Settings).
      </p>
    ),
    target: "[aria-label='History']",
  },

  // --- 4. Specs --------------------------------------------------------------------------------
  {
    id: "specs-open",
    chapter: "Specs: say exactly what you want",
    title: "Specs are versioned",
    body: (
      <p>
        A spec holds the guidelines, the attributes recorded on every item, coverage targets and acceptance rules. Approved
        versions never change, and every request and delivery points to the exact version it used.
      </p>
    ),
    target: "a.nav[href='/specs']",
    task: "open Specs in the menu, then Package damage",
    done: onPath(/^\/specs\/spc_/),
  },
  {
    id: "specs-changes",
    chapter: "Specs: say exactly what you want",
    title: "See what changed between versions",
    body: (
      <p>
        <b>Show changes</b> highlights what's new (green) and removed (red) since the previous version: guidelines line by
        line, plus targets, attribute values and rules in plain words. Pick any version in the history to see it.
      </p>
    ),
    target: "[aria-label='Changes'], [aria-label='Version history']",
  },
  {
    id: "specs-approve",
    chapter: "Specs: say exactly what you want",
    title: "Review and approve a version",
    body: (
      <>
        <p>
          If there's a <b>draft</b> (the diagnosis drafted one), review it, optionally <b>Edit draft</b>, then type your name
          and approve it.
        </p>
        <p>
          No draft? Click <b>Start</b> the next version, <b>Edit draft</b> (e.g. raise shrink-wrapped to 40% and lower box),
          save, then approve.
        </p>
      </>
    ),
    target: "[aria-label='Draft'], [aria-label='Change this spec']",
    task: "approve a new spec version",
    done: event("spec_version.approved"),
  },

  // --- 5. Request ------------------------------------------------------------------------------
  {
    id: "request-new",
    chapter: "Ask for data",
    title: "Create a data request",
    body: (
      <p>
        A request says what data a team needs and why: which capability it should improve, how much, by when, and under
        which approved spec. Try: capability <b>Package damage detection</b>, “Cold-chain packages with condensation”,
        <b> 2,000</b> images, spec <b>Package damage</b> (newest version).
      </p>
    ),
    go: () => "/requests",
    target: "[data-tour='new-request']",
    task: "click New request, fill it in and click Create request",
    done: event("request.created", { save: (e) => ({ requestId: e.subject_id }) }),
  },
  {
    id: "request-open",
    chapter: "Ask for data",
    title: "Open the request",
    body: (
      <p>
        Requests start as drafts. Opening one says the work can begin. It needs an approved spec version; if you didn't pick
        one, use <b>Edit</b> first.
      </p>
    ),
    path: (v) => (v.requestId ? `/requests/${v.requestId}` : null),
    go: (v) => (v.requestId ? `/requests/${v.requestId}` : null),
    target: "[aria-label='Status']",
    task: "click Open request",
    done: event("request.opened", { match: (e, v) => e.subject_id === v.requestId }),
  },

  // --- 6. Split --------------------------------------------------------------------------------
  {
    id: "split-plan",
    chapter: "Split it across sources",
    title: "DCP suggests a split",
    body: (
      <p>
        From each source's last 90 days (cost per usable unit, accept rate, throughput, rights expiry, what they already
        owe), DCP suggests who should do how much, orders extra to cover expected rejects, and gives untested sources a
        small pilot. It explains anything it left out.
      </p>
    ),
    path: (v) => (v.requestId ? `/requests/${v.requestId}` : null),
    target: "[aria-label='Suggested split']",
    task: "click Add all as planned allocations (or Add on one source)",
    done: event("allocation.created", { match: (e, v) => field(e, "request_id") === v.requestId }),
  },
  {
    id: "split-manual",
    chapter: "Split it across sources",
    title: "Or allocate by hand",
    body: <p>You can always add an allocation yourself: pick a source, quantity and the quoted price, and DCP shows the quoted cost.</p>,
    path: (v) => (v.requestId ? `/requests/${v.requestId}` : null),
    target: "[aria-label='Add an allocation']",
  },
  {
    id: "split-start",
    chapter: "Split it across sources",
    title: "Start the work",
    body: (
      <p>
        Allocations start as <b>planned</b>. Starting one tells the source to go ahead. Start a human vendor's (e.g. Surge
        or Mercor): next, that vendor will deliver.
      </p>
    ),
    path: (v) => (v.requestId ? `/requests/${v.requestId}` : null),
    target: "[aria-label='Allocations']",
    task: "click Start on one allocation",
    done: event("allocation.activated", {
      match: (e, v) => field(e, "request_id") === v.requestId,
      save: (e) => ({ allocationId: e.subject_id, sourceId: String(field(e, "data_source_id")) }),
    }),
  },

  // --- 7. Intake -------------------------------------------------------------------------------
  {
    id: "intake-source",
    chapter: "Deliveries arrive by themselves",
    title: "The source's page",
    body: (
      <p>
        Every source has a page with its track record, its rights (what contributors agreed to, when usage rights end, how
        personal data is handled) and how its deliveries reach DCP automatically.
      </p>
    ),
    path: (v) => (v.sourceId ? `/sources/${v.sourceId}` : "/sources"),
    target: "a.nav[href='/sources']",
    task: "open the source you just started (Take me there)",
    done: (ctx) => Boolean(ctx.vars.sourceId) && ctx.pathname === `/sources/${ctx.vars.sourceId}`,
  },
  {
    id: "intake-webhook",
    chapter: "Deliveries arrive by themselves",
    title: "Give the source a webhook address",
    body: (
      <p>
        The source's own system can tell DCP when it delivers by posting a signed message to this address. The signing
        secret proves the message is genuine; it's shown once, for you to hand to the source.
      </p>
    ),
    path: (v) => (v.sourceId ? `/sources/${v.sourceId}` : null),
    target: "[aria-label='Inbound webhooks']",
    task: "click Add a webhook URL",
    done: event("inbound_webhook.created", {
      match: (e, v) => field(e, "data_source_id") === v.sourceId,
      save: (e) => ({ inboundId: e.subject_id }),
    }),
  },
  {
    id: "intake-simulate",
    chapter: "Deliveries arrive by themselves",
    title: "The source delivers",
    body: (
      <p>
        Now play the vendor: the button sends a properly signed “1,200 images delivered” message to that address, exactly
        as the vendor's system would. DCP verifies the signature, registers the delivery against your allocation, and logs
        the message under the webhook.
      </p>
    ),
    path: (v) => (v.sourceId ? `/sources/${v.sourceId}` : null),
    target: "[aria-label='Inbound webhooks']",
    action: {
      label: "Simulate: the vendor's system sends a delivery",
      run: async (ctx) => {
        if (!ctx.vars.inboundId || !ctx.vars.allocationId) throw new Error("Do the two steps before this one first.");
        return { batchId: await sendSignedDelivery(ctx.vars.inboundId, ctx.vars.allocationId) };
      },
    },
  },
  {
    id: "intake-bucket",
    chapter: "Deliveries arrive by themselves",
    title: "Or watch a storage bucket",
    body: (
      <p>
        Many vendors just drop files in a bucket. DCP can watch an S3 (or S3-compatible) folder: each new file becomes a
        delivery and is checked automatically. Access keys are stored encrypted and never shown again.
      </p>
    ),
    path: (v) => (v.sourceId ? `/sources/${v.sourceId}` : null),
    target: "[aria-label='Bucket watchers']",
  },
  {
    id: "intake-api",
    chapter: "Deliveries arrive by themselves",
    title: "Or through the API",
    body: (
      <p>
        Scripts and integrations can register deliveries through the REST API. This one sends a second, smaller delivery
        for the same allocation, where the vendor reports rater agreement of only 0.74 (the spec asks for 0.85).
      </p>
    ),
    action: {
      label: "Simulate: register a delivery through the API",
      run: async (ctx) => {
        if (!ctx.vars.allocationId) throw new Error("Start an allocation first (chapter 6).");
        return { batch2Id: await registerDelivery(ctx.vars.allocationId) };
      },
    },
  },

  // --- 8. Decide -------------------------------------------------------------------------------
  {
    id: "decide-accept",
    chapter: "Decide what's good enough",
    title: "Accept the good delivery",
    body: (
      <p>
        Here's the 1,200-image delivery from the webhook, now on the board <b>In QA</b>. Accept it, keeping what passed your
        review: say <b>1,150</b>. Only accepted items count as usable and can go into training data.
      </p>
    ),
    go: (v) => (v.batchId ? `/batches/${v.batchId}` : null),
    target: "[aria-label='Decision']",
    task: "accept it (e.g. keep 1,150) with your name",
    done: event("batch.accepted", { match: (e, v) => e.subject_id === v.batchId }),
  },
  {
    id: "decide-reject",
    chapter: "Decide what's good enough",
    title: "Reject the weak one",
    body: (
      <p>
        The API delivery reported agreement 0.74, under the spec's 0.85. Reject it with a reason. You won't train on it,
        and it counts against the source's accept rate.
      </p>
    ),
    go: (v) => (v.batch2Id ? `/batches/${v.batch2Id}` : null),
    target: "[aria-label='Decision']",
    task: "choose Reject, give a reason and reject it",
    done: event("batch.rejected", { match: (e, v) => e.subject_id === v.batch2Id }),
  },
  {
    id: "decide-scorecard",
    chapter: "Decide what's good enough",
    title: "The source's track record updates",
    body: (
      <p>
        Accept rate and cost per usable unit now include your decisions. These figures feed the suggested split for the
        next request, so reliable, cheaper sources get more work.
      </p>
    ),
    go: (v) => (v.sourceId ? `/sources/${v.sourceId}` : "/sources"),
    target: "[aria-label='Track record']",
  },

  // --- 9. Dataset & eval -----------------------------------------------------------------------
  {
    id: "lineage-chain",
    chapter: "Freeze a dataset and measure it",
    title: "Lineage: from request to eval",
    body: (
      <p>
        A dataset version is a frozen set of accepted deliveries, what training actually uses. Here you can trace it back
        to the requests, spec versions and deliveries in it, through the QA gate, forward to the eval it moved, and see
        spend and yield per delivery.
      </p>
    ),
    go: () => "/lineage",
    target: "[aria-label='Lineage']",
  },
  {
    id: "lineage-freeze",
    chapter: "Freeze a dataset and measure it",
    title: "Freeze the next version",
    body: (
      <p>
        Add your accepted delivery to a new version of <b>damage-det</b>. It starts from the latest version, which becomes
        the baseline its eval change is measured against, so the spend behind the change is just the new deliveries.
      </p>
    ),
    go: () => "/lineage",
    target: "[data-tour='new-version']",
    task: "click New version, tick your delivery and freeze it",
    done: event("dataset_version.created", { save: (e) => ({ datasetVersionId: e.subject_id }) }),
  },
  {
    id: "lineage-eval",
    chapter: "Freeze a dataset and measure it",
    title: "Record the eval result",
    body: (
      <p>
        After training on the new version, record its score (DCP doesn't train models; your pipeline or a script reports
        the result, often with a link to the run). Try <b>0.872</b> for recall@0.5.
      </p>
    ),
    target: "[aria-label='Record an eval result']",
    task: "enter a value and click Record result",
    done: event("eval_result.recorded", { match: (e, v) => field(e, "dataset_version_id") === v.datasetVersionId }),
  },
  {
    id: "lineage-impact",
    chapter: "Freeze a dataset and measure it",
    title: "The eval moved",
    body: <p>Eval impact compares each metric with the baseline version, so you can see what this data bought.</p>,
    target: "[aria-label='Eval impact']",
  },

  // --- 10. Close the loop ----------------------------------------------------------------------
  {
    id: "loop-portfolio",
    chapter: "Close the loop",
    title: "Back to the results",
    body: (
      <p>
        The portfolio now includes your new version: spend, usable units, eval change and points per $10K moved, and the
        diagnosis re-ran with the new data point. That's the full loop: results drove a request; the request turned into
        work, deliveries, a dataset and an eval; and the eval feeds back into the results.
      </p>
    ),
    go: () => "/portfolio",
    target: "[data-tour='by-capability']",
  },
  {
    id: "loop-complete",
    chapter: "Close the loop",
    title: "Complete the work",
    body: <p>When a source has delivered all it will, mark its allocation complete.</p>,
    go: (v) => (v.requestId ? `/requests/${v.requestId}` : null),
    target: "[aria-label='Allocations']",
    task: "click Complete on the active allocation",
    done: event("allocation.completed", { match: (e, v) => field(e, "request_id") === v.requestId }),
  },
  {
    id: "loop-close",
    chapter: "Close the loop",
    title: "Close the request",
    body: <p>Closing the request cancels any allocations still only planned, and takes it off the board.</p>,
    path: (v) => (v.requestId ? `/requests/${v.requestId}` : null),
    target: "[aria-label='Status']",
    task: "click Close request",
    done: event("request.closed", { match: (e, v) => e.subject_id === v.requestId }),
  },

  // --- 11. Admin -------------------------------------------------------------------------------
  {
    id: "admin-capability",
    chapter: "Set up and administer",
    title: "Add a capability",
    body: (
      <p>
        Capabilities are where everything starts. Try “Shipping label legibility”, metric “read error rate”, <b>lower</b> is
        better, one point worth <b>41000</b>.
      </p>
    ),
    go: () => "/settings/capabilities",
    target: "[aria-label='Capabilities']",
    task: "click New capability, fill it in and create it",
    done: event("capability.created"),
  },
  {
    id: "admin-source",
    chapter: "Set up and administer",
    title: "Register a new source",
    body: (
      <p>
        Every way you get data goes in one registry with its rights basis and expiry. Try “Northgate SimLab”, type
        <b> Synthetic data</b>.
      </p>
    ),
    go: () => "/sources",
    target: "[data-tour='new-source']",
    task: "click New source, fill it in and create it",
    done: event("data_source.created"),
  },
  {
    id: "admin-key",
    chapter: "Set up and administer",
    title: "Give a teammate access",
    body: (
      <p>
        People and tools sign in with API keys. Admin keys see everything; project keys see one project; read keys can only
        look. Create a read-only key for this project. Its secret is shown once.
      </p>
    ),
    go: () => "/settings/keys",
    target: "[aria-label='API keys']",
    task: "create a read-only key for one project",
    done: event("api_key.created", { anyProject: true, save: (e) => ({ keyId: e.subject_id }) }),
  },
  {
    id: "admin-revoke",
    chapter: "Set up and administer",
    title: "Take access away",
    body: <p>Revoking a key stops it working immediately. The record stays, so you can see who had access and when.</p>,
    go: () => "/settings/keys",
    target: "[aria-label='API keys']",
    task: "revoke the key you just made",
    done: event("api_key.revoked", { anyProject: true, match: (e, v) => e.subject_id === v.keyId }),
  },
  {
    id: "admin-webhooks",
    chapter: "Set up and administer",
    title: "Send updates to your other tools",
    body: (
      <p>
        DCP can post a signed message to any address when things change (deliveries accepted, requests opened…), retrying
        for about a day if the receiver is down, with a log of every attempt. Add one, e.g. https://example.com/hook.
      </p>
    ),
    go: () => "/settings/webhooks",
    target: "[aria-label='Webhooks']",
    task: "add an address",
    done: event("webhook_endpoint.created", { anyProject: true }),
  },

  // --- 12. API ---------------------------------------------------------------------------------
  {
    id: "api",
    chapter: "Everything is an API",
    title: "Everything you did is in the API",
    body: (
      <>
        <p>
          This interface only uses DCP's public REST API, so everything you just did can be scripted, automated or managed
          from other tools: a generated Python client and command-line tool, Idempotency-Key support for safe retries, and
          an OpenAPI contract.
        </p>
        <p>
          Explore it at{" "}
          <a href="/docs" target="_blank" rel="noreferrer">
            /docs
          </a>{" "}
          (“Try it out” with your key).
        </p>
      </>
    ),
  },
  {
    id: "finish",
    chapter: "Everything is an API",
    title: "That's the whole loop",
    body: (
      <>
        <p>
          You read the results, approved a spec, requested data, split it across sources, had deliveries arrive by webhook
          and API, accepted and rejected them, froze a dataset version, recorded its eval, watched the portfolio update, and
          set up capabilities, sources, access and webhooks.
        </p>
        <p>Restart any chapter from the Tutorial button whenever you like.</p>
      </>
    ),
    target: "[data-tour='tutorial']",
  },
];
