import { describe, expect, it } from "vitest";

import { createSnipeStore, formatSize, isImage } from "./snipe.service.ts";

const HOUR = 3_600_000;

describe("snipe store", () => {
  it("keeps the last deleted message per channel", () => {
    const store = createSnipeStore<string>(2 * HOUR);
    store.remember("a", "first", 0);
    store.remember("a", "second", 1000);
    store.remember("b", "other", 1000);
    expect(store.latest("a", 2000)).toEqual({ message: "second", deletedAt: new Date(1000) });
    expect(store.latest("b", 2000)?.message).toBe("other");
    expect(store.latest("c", 2000)).toBeUndefined();
  });

  it("forgets messages after the time limit", () => {
    const store = createSnipeStore<string>(2 * HOUR);
    store.remember("a", "old", 0);
    expect(store.latest("a", 2 * HOUR - 1)?.message).toBe("old");
    expect(store.latest("a", 2 * HOUR)).toBeUndefined();
  });

  it("clears one channel", () => {
    const store = createSnipeStore<string>(HOUR);
    store.remember("a", "x", 0);
    store.remember("b", "y", 0);
    store.clear("a");
    expect(store.latest("a", 1)).toBeUndefined();
    expect(store.latest("b", 1)?.message).toBe("y");
  });
});

describe("attachments", () => {
  const file = (name: string, contentType?: string) => ({ url: "u", name, contentType, size: 0 });

  it("detects images by type or extension", () => {
    expect(isImage(file("a.bin", "image/png"))).toBe(true);
    expect(isImage(file("photo.JPG"))).toBe(true);
    expect(isImage(file("notes.txt", "text/plain"))).toBe(false);
  });

  it("formats sizes in megabytes", () => {
    expect(formatSize(1_572_864)).toBe("1.50 MB");
  });
});
