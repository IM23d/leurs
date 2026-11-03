export interface Job {
  readonly name: string;
  readonly basePay: number;
  /** Chance from 0 to 1 that a shift also pays `bonusAmount`. */
  readonly bonusChance: number;
  readonly bonusAmount: number;
  readonly cost: number;
}

export const MAX_JOBS = 3;

const job = (
  name: string,
  basePay: number,
  bonusChance: number,
  bonusAmount: number,
  cost: number,
) => ({ name, basePay, bonusChance, bonusAmount, cost }) satisfies Job;

/** Every job on the market, in the order the market lists them. */
export const JOBS: readonly Job[] = [
  job("McDonalds-Employee", 75, 0.2, 50, 0),
  job("Artist", 300, 0.25, 250, 1000),
  job("Teacher", 350, 0.1, 100, 2000),
  job("Software-Developer", 500, 0.2, 200, 5000),
  job("Police-Officer", 450, 0.15, 150, 7500),
  job("Engineer", 550, 0.2, 250, 10_000),
  job("Doctor", 600, 0.1, 300, 15_000),
  job("Politician", 750, 0.3, 350, 25_000),
  job("Stripper", 150, 0.5, 150, 1000),
  job("Pilot", 800, 0.15, 400, 30_000),
  job("Scientist", 700, 0.25, 300, 20_000),
  job("Lawyer", 650, 0.3, 250, 18_000),
  job("Real-Estate-Agent", 400, 0.4, 300, 10_000),
  job("Stock-Trader", 600, 0.5, 400, 20_000),
  job("Youtuber", 300, 0.6, 500, 5000),
  job("Streamer", 250, 0.55, 400, 4000),
  job("Esportler", 400, 0.45, 300, 8000),
  job("Astronaut", 1000, 0.2, 500, 50_000),
  job("Flight-Attendant", 250, 0.2, 100, 3000),
  job("Delivery-Driver", 150, 0.25, 50, 0),
  job("Plumber", 300, 0.2, 100, 4000),
  job("Farmer", 220, 0.2, 80, 2000),
  job("Life-Coach", 350, 0.3, 150, 6000),
];

const normalize = (name: string) =>
  name
    .trim()
    .toLowerCase()
    .replaceAll(/[\s_]+/g, "-");

/** Finds a job by name, ignoring case and treating spaces as hyphens. */
export const findJob = (name: string): Job | undefined =>
  JOBS.find((candidate) => normalize(candidate.name) === normalize(name));
