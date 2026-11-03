export type Amount =
  | { readonly kind: "all" }
  | { readonly kind: "percent"; readonly percent: number }
  | { readonly kind: "coins"; readonly coins: number };

/** Reads "250", "1,000", "50%" or "all". Returns undefined for anything else, including 0. */
export function parseAmount(text: string): Amount | undefined {
  const value = text.trim().toLowerCase().replaceAll(/[,_']/g, "");
  if (value === "all") return { kind: "all" };
  const percent = /^(\d+)%$/.exec(value)?.[1];
  if (percent !== undefined) {
    const number = Number(percent);
    return number >= 1 && number <= 100 ? { kind: "percent", percent: number } : undefined;
  }
  if (!/^\d+$/.test(value)) return undefined;
  const coins = Number(value);
  return coins > 0 && Number.isSafeInteger(coins) ? { kind: "coins", coins } : undefined;
}

/** The number of coins an amount stands for, given the balance. Percentages round down. */
export function resolveAmount(amount: Amount, balance: number): number {
  switch (amount.kind) {
    case "all":
      return balance;
    case "percent":
      return Math.floor((balance * amount.percent) / 100);
    case "coins":
      return amount.coins;
  }
}
