import { beforeEach, describe, expect, it, vi } from "vitest";
import type { RunResult } from "../types";
import { PyClient, SupersededError, TimeoutError } from "./client";

const OK: RunResult = { dots: [{ name: "D", source: "digraph {}" }], stdout: "", error: null };

/** Fake Worker that intercepts postMessage; tests drive its responses. */
class FakeWorker {
  static instances: FakeWorker[] = [];
  onmessage: ((e: MessageEvent) => void) | null = null;
  posted: unknown[] = [];
  terminated = false;
  constructor() {
    FakeWorker.instances.push(this);
  }
  postMessage(msg: { type: string; id?: number }) {
    this.posted.push(msg);
    if (msg.type === "init") this.emit({ type: "ready" });
  }
  terminate() {
    this.terminated = true;
  }
  emit(data: unknown) {
    this.onmessage?.({ data } as MessageEvent);
  }
  lastRun() {
    return this.posted.filter((m) => (m as { type: string }).type === "run").at(-1) as
      | { type: "run"; id: number; code: string }
      | undefined;
  }
}

function makeClient() {
  return new PyClient(() => new FakeWorker() as unknown as Worker, { fetchWheelUrl: async () => "wheels/x.whl" });
}

beforeEach(() => {
  FakeWorker.instances = [];
  vi.useRealTimers();
});

describe("PyClient", () => {
  it("init resolves when worker reports ready", async () => {
    const client = makeClient();
    await expect(client.init()).resolves.toBeUndefined();
  });

  it("run resolves with the worker result", async () => {
    const client = makeClient();
    await client.init();
    const worker = FakeWorker.instances[0];
    const promise = client.run("code");
    const run = worker.lastRun()!;
    worker.emit({ type: "result", id: run.id, result: OK });
    await expect(promise).resolves.toEqual(OK);
  });

  it("supersedes a queued run when a newer one arrives", async () => {
    const client = makeClient();
    await client.init();
    const worker = FakeWorker.instances[0];
    const first = client.run("first"); // in flight
    const second = client.run("second"); // queued
    const third = client.run("third"); // replaces second
    await expect(second).rejects.toBeInstanceOf(SupersededError);
    worker.emit({ type: "result", id: worker.lastRun()!.id, result: OK });
    await first;
    // after `first` resolves, the third run dispatches automatically
    const thirdRun = worker.lastRun()!;
    expect(thirdRun.code).toBe("third");
    worker.emit({ type: "result", id: thirdRun.id, result: OK });
    await expect(third).resolves.toEqual(OK);
  });

  it("rejects with TimeoutError and restarts the worker on timeout", async () => {
    vi.useFakeTimers();
    const client = makeClient();
    await client.init();
    const first = FakeWorker.instances[0];
    const promise = client.run("while True: pass");
    const rejection = expect(promise).rejects.toBeInstanceOf(TimeoutError);
    await vi.advanceTimersByTimeAsync(10_000);
    await rejection;
    expect(first.terminated).toBe(true);
    expect(FakeWorker.instances.length).toBe(2); // a fresh worker was spawned
  });

  it("rejects queued and future runs when respawn fails", async () => {
    vi.useFakeTimers();
    let calls = 0;
    const client = new PyClient(() => new FakeWorker() as unknown as Worker, {
      fetchWheelUrl: async () => {
        calls += 1;
        if (calls > 1) throw new Error("manifest gone");
        return "wheels/x.whl";
      },
    });
    await client.init();
    const first = client.run("while True: pass");
    const firstRejection = expect(first).rejects.toBeInstanceOf(TimeoutError);
    const queued = client.run("queued");
    const queuedRejection = expect(queued).rejects.toThrow("manifest gone");
    await vi.advanceTimersByTimeAsync(10_000);
    await firstRejection;
    await queuedRejection;
    await expect(client.run("later")).rejects.toThrow("manifest gone");
  });

  it("dispose rejects in-flight and future runs and terminates the worker", async () => {
    const client = makeClient();
    await client.init();
    const worker = FakeWorker.instances[0];
    const inFlight = client.run("code");
    const rejection = expect(inFlight).rejects.toThrow("disposed");
    client.dispose();
    await rejection;
    expect(worker.terminated).toBe(true);
    await expect(client.run("later")).rejects.toThrow("disposed");
  });
});
