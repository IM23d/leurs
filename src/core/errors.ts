/**
 * An expected failure caused by the user, such as bad input or a missing requirement.
 * The dispatcher shows the message to the user as is. Anything else is logged as a bug.
 */
export class UserError extends Error {
  override name = "UserError";
}
