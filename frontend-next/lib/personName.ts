/**
 * Person-name handling for saved Kundlis.
 *
 * The name belongs to the PERSON WHOSE CHART IS BEING GENERATED, which is not
 * necessarily the signed-in account holder. It is never replaced with the
 * account holder's name.
 *
 * Unicode is fully supported (Hindi and other normal names), only control
 * characters are stripped, and a reasonable maximum length is enforced.
 */

export const UNNAMED_KUNDLI = 'Unnamed Kundli';
export const PERSON_NAME_MAX = 80;

/** Trim, collapse whitespace, strip control characters, cap the length. */
export function normalisePersonName(raw: unknown): string {
  if (typeof raw !== 'string') return '';
  return raw
    .replace(/[\u0000-\u001F\u007F]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, PERSON_NAME_MAX);
}

/** A name is required for a new Kundli: whitespace-only is invalid. */
export function isValidPersonName(raw: unknown): boolean {
  return normalisePersonName(raw).length > 0;
}

/** Safe display value; historical records without a name stay readable. */
export function displayPersonName(raw: unknown): string {
  return normalisePersonName(raw) || UNNAMED_KUNDLI;
}
