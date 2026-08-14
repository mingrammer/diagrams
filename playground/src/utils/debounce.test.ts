import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { debounce } from "./debounce";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("debounce", () => {
  it("fires once with the latest args after the wait", () => {
    const spy = vi.fn();
    const fn = debounce(spy, 500);
    fn("a");
    fn("b");
    vi.advanceTimersByTime(499);
    expect(spy).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(spy).toHaveBeenCalledOnce();
    expect(spy).toHaveBeenCalledWith("b");
  });

  it("restarts the wait on each call", () => {
    const spy = vi.fn();
    const fn = debounce(spy, 500);
    fn("a");
    vi.advanceTimersByTime(400);
    fn("b");
    vi.advanceTimersByTime(400);
    expect(spy).not.toHaveBeenCalled();
    vi.advanceTimersByTime(100);
    expect(spy).toHaveBeenCalledWith("b");
  });
});
