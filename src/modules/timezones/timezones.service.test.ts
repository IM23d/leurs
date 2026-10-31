import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import { getTimezoneSettings, setUse24Hour, setZone, zoneFor } from "./timezones.service.ts";

describe("timezone settings", () => {
  useTestDb();

  it("defaults to no zone and 12-hour time", () => {
    expect(getTimezoneSettings("1")).toEqual({ zone: undefined, use24Hour: false });
    expect(zoneFor("1")).toBe("UTC");
  });

  it("keeps the zone and the format apart", () => {
    setUse24Hour("1", true);
    expect(getTimezoneSettings("1")).toEqual({ zone: undefined, use24Hour: true });
    setZone("1", "Europe/Berlin");
    setZone("1", "Europe/Zurich");
    expect(getTimezoneSettings("1")).toEqual({ zone: "Europe/Zurich", use24Hour: true });
    expect(zoneFor("1")).toBe("Europe/Zurich");
    expect(zoneFor("2")).toBe("UTC");
  });
});
