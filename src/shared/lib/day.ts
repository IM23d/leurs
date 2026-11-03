/** The UTC calendar day of `now` as "YYYY-MM-DD". Daily limits roll over at UTC midnight. */
export const utcDay = (now: number): string => new Date(now).toISOString().slice(0, 10);
