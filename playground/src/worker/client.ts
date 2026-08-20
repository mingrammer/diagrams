import type { ProgressStage, RunResult } from "../types";

export const RUN_TIMEOUT_MS = 10_000;
export const INIT_TIMEOUT_MS = 120_000;

export class TimeoutError extends Error {
  constructor() {
    super("Execution timed out");
  }
}

export class SupersededError extends Error {
  constructor() {
    super("Superseded by a newer run");
  }
}

interface PendingRun {
  code: string;
  resolve: (r: RunResult) => void;
  reject: (e: Error) => void;
}

interface ClientOptions {
  fetchWheelUrl?: () => Promise<string>;
}

async function defaultFetchWheelUrl(): Promise<string> {
  const res = await fetch("wheels/manifest.json");
  const manifest = (await res.json()) as { wheel: string };
  return `wheels/${manifest.wheel}`;
}

function defaultMakeWorker(): Worker {
  return new Worker(new URL("./py.worker.ts", import.meta.url), { type: "module" });
}

export class PyClient {
  private worker: Worker | null = null;
  private ready = false;
  private nextId = 1;
  private inFlight: (PendingRun & { id: number; timer: ReturnType<typeof setTimeout> }) | null = null;
  private queued: PendingRun | null = null;
  private onProgress?: (s: ProgressStage) => void;
  private dead: Error | null = null;

  constructor(
    private makeWorker: () => Worker = defaultMakeWorker,
    private options: ClientOptions = {}
  ) {}

  async init(onProgress?: (s: ProgressStage) => void): Promise<void> {
    this.onProgress = onProgress;
    await this.spawn();
  }

  private async spawn(): Promise<void> {
    const rawWheelUrl = await (this.options.fetchWheelUrl ?? defaultFetchWheelUrl)();
    // Resolve to an absolute URL against the *page's* location before handing it
    // to the worker: the worker script has its own module URL (e.g. under
    // /assets/ in a production build), so a relative path would otherwise
    // resolve against the worker's location instead of the page's, sending
    // micropip.install() to the wrong path (see task-14 e2e report).
    const wheelUrl = new URL(rawWheelUrl, location.href).href;
    this.worker = this.makeWorker();
    this.worker.onmessage = (e) => this.handleMessage(e.data);
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(() => reject(new TimeoutError()), INIT_TIMEOUT_MS);
      this.resolveReady = () => {
        clearTimeout(timer);
        this.ready = true;
        resolve();
      };
      this.rejectReady = (err) => {
        clearTimeout(timer);
        reject(err);
      };
      // Wire resolveReady/rejectReady before posting: some worker
      // implementations (and the FakeWorker used in tests) may respond
      // synchronously within postMessage, which would otherwise race
      // ahead of these callbacks being assigned.
      this.worker!.postMessage({ type: "init", wheelUrl });
    });
  }

  private resolveReady: (() => void) | null = null;
  private rejectReady: ((e: Error) => void) | null = null;

  private handleMessage(msg: {
    type: string;
    stage?: ProgressStage;
    id?: number;
    result?: RunResult;
    error?: string;
  }) {
    switch (msg.type) {
      case "progress":
        this.onProgress?.(msg.stage!);
        break;
      case "ready":
        this.onProgress?.("ready");
        this.resolveReady?.();
        this.dispatchQueued();
        break;
      case "init-error":
        this.rejectReady?.(new Error(msg.error));
        break;
      case "result":
      case "run-error": {
        if (!this.inFlight || this.inFlight.id !== msg.id) return;
        const { resolve, reject, timer } = this.inFlight;
        clearTimeout(timer);
        this.inFlight = null;
        if (msg.type === "result") resolve(msg.result!);
        else reject(new Error(msg.error));
        this.dispatchQueued();
        break;
      }
    }
  }

  run(code: string): Promise<RunResult> {
    return new Promise<RunResult>((resolve, reject) => {
      if (this.dead) {
        reject(this.dead);
        return;
      }
      const pending: PendingRun = { code, resolve, reject };
      if (this.inFlight || !this.ready) {
        this.queued?.reject(new SupersededError());
        this.queued = pending;
      } else {
        this.dispatch(pending);
      }
    });
  }

  private dispatchQueued() {
    if (this.queued && !this.inFlight && this.ready) {
      const next = this.queued;
      this.queued = null;
      this.dispatch(next);
    }
  }

  private dispatch(pending: PendingRun) {
    const id = this.nextId++;
    const timer = setTimeout(() => this.handleTimeout(), RUN_TIMEOUT_MS);
    this.inFlight = { ...pending, id, timer };
    this.worker!.postMessage({ type: "run", id, code: pending.code });
  }

  private handleTimeout() {
    const stalled = this.inFlight;
    this.inFlight = null;
    this.ready = false;
    this.worker?.terminate();
    stalled?.reject(new TimeoutError());
    // Re-initialize a fresh worker in the background (any queued code runs next).
    void this.spawn().catch((err) => {
      this.dead = err instanceof Error ? err : new Error(String(err));
      this.queued?.reject(this.dead);
      this.queued = null;
    });
  }

  /** Terminate the worker and reject all pending/future runs (unmount cleanup). */
  dispose(): void {
    this.dead = new Error("PyClient disposed");
    this.rejectReady?.(this.dead);
    this.queued?.reject(this.dead);
    this.queued = null;
    if (this.inFlight) {
      clearTimeout(this.inFlight.timer);
      this.inFlight.reject(this.dead);
      this.inFlight = null;
    }
    this.worker?.terminate();
    this.ready = false;
  }
}
