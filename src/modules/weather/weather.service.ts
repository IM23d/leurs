import { z } from "zod";

import { UserError } from "#core/errors.ts";

import { weatherEmoji } from "./weather.codes.ts";

const TIMEOUT_MS = 10_000;
const FORECAST_DAYS = 5;

const geocodeSchema = z.object({
  results: z
    .array(
      z.object({
        latitude: z.number(),
        longitude: z.number(),
        name: z.string(),
        country: z.string().optional(),
      }),
    )
    .optional(),
});

const forecastSchema = z.object({
  current: z.object({
    temperature_2m: z.number(),
    apparent_temperature: z.number(),
    relative_humidity_2m: z.number(),
    wind_speed_10m: z.number(),
    weather_code: z.number(),
  }),
  daily: z.object({
    time: z.array(z.string()),
    temperature_2m_min: z.array(z.number()),
    temperature_2m_max: z.array(z.number()),
    weather_code: z.array(z.number()),
  }),
});

export type Place = NonNullable<z.infer<typeof geocodeSchema>["results"]>[number];
type Forecast = z.infer<typeof forecastSchema>;

interface DayForecast {
  readonly day: string;
  readonly emoji: string;
  readonly min: number;
  readonly max: number;
}

export interface WeatherReport {
  readonly location: string;
  readonly emoji: string;
  readonly temperature: number;
  readonly feelsLike: number;
  readonly todayMin: number;
  readonly todayMax: number;
  readonly humidity: number;
  readonly windSpeed: number;
  readonly days: readonly DayForecast[];
}

async function getJson(url: URL): Promise<unknown> {
  const response = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS) }).catch(
    () => undefined,
  );
  if (!response?.ok) throw new UserError("The weather service isn't responding. Try again later.");
  return response.json();
}

/** Picks the first match, as the old bot did. */
export function parsePlace(json: unknown): Place | undefined {
  return geocodeSchema.parse(json).results?.[0];
}

const weekday = (date: string): string =>
  new Date(`${date}T00:00:00Z`).toLocaleDateString("en-US", { weekday: "long", timeZone: "UTC" });

/** Maps an Open-Meteo forecast to the report. Index 0 of the daily data is today. */
export function toReport(place: Place, json: unknown): WeatherReport {
  const { current, daily }: Forecast = forecastSchema.parse(json);
  const dayAt = (index: number) => ({
    emoji: weatherEmoji(daily.weather_code[index] ?? -1),
    min: Math.round(daily.temperature_2m_min[index] ?? Number.NaN),
    max: Math.round(daily.temperature_2m_max[index] ?? Number.NaN),
  });
  const today = dayAt(0);
  return {
    location: place.country ? `${place.name}, ${place.country}` : place.name,
    emoji: weatherEmoji(current.weather_code),
    temperature: Math.round(current.temperature_2m),
    feelsLike: Math.round(current.apparent_temperature),
    todayMin: today.min,
    todayMax: today.max,
    humidity: current.relative_humidity_2m,
    windSpeed: current.wind_speed_10m,
    days: daily.time
      .slice(1, FORECAST_DAYS + 1)
      .map((date, index) => ({ day: weekday(date), ...dayAt(index + 1) })),
  };
}

export async function getWeather(location: string): Promise<WeatherReport> {
  const geocodeUrl = new URL("https://geocoding-api.open-meteo.com/v1/search");
  geocodeUrl.search = new URLSearchParams({
    name: location,
    count: "1",
    language: "en",
    format: "json",
  }).toString();
  const place = parsePlace(await getJson(geocodeUrl));
  if (!place) throw new UserError(`I couldn't find ${location}.`);

  const forecastUrl = new URL("https://api.open-meteo.com/v1/forecast");
  forecastUrl.search = new URLSearchParams({
    latitude: String(place.latitude),
    longitude: String(place.longitude),
    current:
      "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
    daily: "temperature_2m_max,temperature_2m_min,weather_code",
    timezone: "auto",
  }).toString();
  return toReport(place, await getJson(forecastUrl));
}
