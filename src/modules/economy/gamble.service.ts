import { UserError } from "#core/errors.ts";
import { db } from "#db/client.ts";

import { resolveAmount, type Amount } from "./amount.ts";
import { addBalance, getBalance, takeBalance, type Random } from "./wallet.service.ts";

export interface GambleResult {
  readonly won: boolean;
  readonly stake: number;
  readonly balance: number;
}

/** Flips a coin: heads doubles the stake, tails loses it. */
export function gamble(userId: string, amount: Amount, random: Random = Math.random): GambleResult {
  return db().transaction(() => {
    const stake = resolveAmount(amount, getBalance(userId));
    if (stake <= 0) throw new UserError("That comes to 0 coins, so there is nothing to gamble.");
    const afterStake = takeBalance(userId, stake);
    if (afterStake === undefined) throw new UserError("You don't have enough coins.");
    const won = random() < 0.5;
    return { won, stake, balance: won ? addBalance(userId, stake * 2) : afterStake };
  });
}
