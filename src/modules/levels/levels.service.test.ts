import { afterEach, describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  flushActivity,
  recordMessage,
  setVoiceActive,
  syncVoiceSessions,
} from "./activity.service.ts";
import { levelForXp, levelProgress, rollMessageXp, XP_PER_LEVEL } from "./levels.math.ts";
import { levels } from "./levels.schema.ts";
import { getStats, levelRanking, setMessages, voiceRanking } from "./levels.service.ts";

const testDb = useTestDb();

// Gains live in memory between tests, so each test writes them into its own database.
afterEach(() => {
  flushActivity();
});

const storedRows = () => testDb().select().from(levels).all();

describe("XP maths", () => {
  it("gives 10 to 20 XP per message", () => {
    expect(rollMessageXp(() => 0)).toBe(10);
    expect(rollMessageXp(() => 0.5)).toBe(15);
    expect(rollMessageXp(() => 0.999)).toBe(20);
  });

  it("needs 3500 XP per level", () => {
    expect(levelForXp(0)).toBe(0);
    expect(levelForXp(XP_PER_LEVEL - 1)).toBe(0);
    expect(levelForXp(XP_PER_LEVEL)).toBe(1);
    expect(levelForXp(248_948)).toBe(71);
  });

  it("shows progress within the level", () => {
    expect(levelProgress(XP_PER_LEVEL + 1750)).toEqual({
      level: 1,
      current: 1750,
      needed: XP_PER_LEVEL,
      percent: 50,
    });
  });
});

describe("recordMessage", () => {
  it("counts a message and returns the level it crossed into", () => {
    setMessages("climber", 233); // 3495 XP
    expect(recordMessage("climber", 0, () => 0)).toBe(1);
    expect(recordMessage("climber", 1, () => 0)).toBeUndefined();
    expect(getStats("climber")).toMatchObject({ xp: 3515, level: 1, messages: 235 });
  });

  it("stops giving XP after 60 messages in a minute", () => {
    for (let i = 0; i < 61; i++) recordMessage("spammer", i * 100, () => 0);
    expect(getStats("spammer")).toMatchObject({ xp: 600, messages: 60 });
    recordMessage("spammer", 60_001, () => 0);
    expect(getStats("spammer").messages).toBe(61);
  });
});

describe("flushActivity", () => {
  it("keeps gains in memory until the flush", () => {
    recordMessage("buffered", 0, () => 0);
    expect(storedRows()).toEqual([]);
    expect(getStats("buffered").xp).toBe(10);
    expect(flushActivity()).toBe(1);
    expect(storedRows()).toEqual([{ userId: "buffered", xp: 10, messages: 1, voiceSeconds: 0 }]);
    recordMessage("buffered", 1, () => 0);
    flushActivity();
    expect(getStats("buffered")).toMatchObject({ xp: 20, messages: 2 });
  });

  it("credits running voice sessions on each flush", () => {
    setVoiceActive("talker", true, 0);
    setVoiceActive("talker", true, 5000); // switching channels keeps the session
    flushActivity(30_500);
    expect(storedRows()).toMatchObject([{ userId: "talker", voiceSeconds: 30 }]);
    setVoiceActive("talker", false, 61_000);
    flushActivity(90_000);
    expect(getStats("talker").voiceSeconds).toBe(61);
  });

  it("ends sessions of users who left voice unseen and starts sessions for new ones", () => {
    setVoiceActive("stale", true, 0);
    setVoiceActive("staying", true, 0);
    syncVoiceSessions(new Set(["staying", "joined"]), 10_000);
    flushActivity(20_000);
    expect(getStats("stale").voiceSeconds).toBe(10);
    expect(getStats("staying").voiceSeconds).toBe(20);
    expect(getStats("joined").voiceSeconds).toBe(10);
    syncVoiceSessions(new Set(), 20_000);
    flushActivity(60_000);
    expect(getStats("staying").voiceSeconds).toBe(20);
    expect(getStats("joined").voiceSeconds).toBe(10);
  });

  it("lets setMessages replace pending message XP", () => {
    recordMessage("reset", 0, () => 0);
    expect(setMessages("reset", 100)).toMatchObject({ xp: 1500, level: 0, messages: 100 });
    flushActivity();
    expect(getStats("reset")).toMatchObject({ xp: 1500, messages: 100 });
  });
});

describe("rankings", () => {
  it("sorts by XP and voice time and leaves out other users", () => {
    setMessages("a", 10);
    setMessages("b", 300);
    setMessages("outsider", 1000);
    setVoiceActive("a", true, 0);
    setVoiceActive("a", false, 120_000);
    expect(levelRanking(["a", "b", "nobody"])).toEqual([
      { userId: "b", level: 1, xp: 4500, messages: 300 },
      { userId: "a", level: 0, xp: 150, messages: 10 },
    ]);
    expect(voiceRanking(["a", "b"])).toEqual([{ userId: "a", seconds: 120 }]);
  });
});
