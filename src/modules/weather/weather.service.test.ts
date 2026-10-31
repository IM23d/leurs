import { describe, expect, it } from "vitest";

import { weatherEmoji } from "./weather.codes.ts";
import { parsePlace, toReport, type Place } from "./weather.service.ts";

describe("weatherEmoji", () => {
  it.each([
    [0, "☀️"],
    [3, "☁️"],
    [45, "🌫️"],
    [65, "🌧️"],
    [75, "❄️"],
    [99, "⛈️"],
    [42, "🌡️"],
  ])("maps code %d", (code, emoji) => {
    expect(weatherEmoji(code)).toBe(emoji);
  });
});

describe("parsePlace", () => {
  it("takes the first result", () => {
    const place = parsePlace({
      results: [{ latitude: 47.37, longitude: 8.55, name: "Zurich", country: "Switzerland" }],
    });
    expect(place?.name).toBe("Zurich");
  });

  it("returns undefined when nothing matched", () => {
    expect(parsePlace({ generationtime_ms: 0.5 })).toBeUndefined();
  });
});

const forecast = {
  current: {
    temperature_2m: 12.6,
    apparent_temperature: 10.2,
    relative_humidity_2m: 81,
    wind_speed_10m: 7.4,
    weather_code: 3,
  },
  daily: {
    time: ["2026-10-31", "2026-11-01", "2026-11-02"],
    temperature_2m_min: [4.4, 3.6, 1.2],
    temperature_2m_max: [13.1, 9.5, 8.8],
    weather_code: [3, 61, 71],
  },
};

describe("toReport", () => {
  const place: Place = { latitude: 0, longitude: 0, name: "Zurich", country: "Switzerland" };

  it("maps current conditions and today's range", () => {
    expect(toReport(place, forecast)).toMatchObject({
      location: "Zurich, Switzerland",
      emoji: "☁️",
      temperature: 13,
      feelsLike: 10,
      todayMin: 4,
      todayMax: 13,
      humidity: 81,
      windSpeed: 7.4,
    });
  });

  it("forecasts the following days by weekday", () => {
    expect(toReport(place, forecast).days).toEqual([
      { day: "Sunday", emoji: "🌦️", min: 4, max: 10 },
      { day: "Monday", emoji: "🌨️", min: 1, max: 9 },
    ]);
  });

  it("leaves the country out when there is none", () => {
    expect(toReport({ ...place, country: undefined }, forecast).location).toBe("Zurich");
  });
});
