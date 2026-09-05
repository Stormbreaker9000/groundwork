/**
 * The groundwork plumb-bob mark: plumb line, bob, and the ground line it
 * hangs over.
 *
 * Every path paints in `currentColor`, so the mark inherits whatever colour
 * the navbar text has and needs no separate light and dark variant. Sized in
 * `em` so it tracks the wordmark beside it instead of a fixed pixel size.
 *
 * The markup is assets/groundwork-mark.svg inlined. Inlined rather than
 * imported because `currentColor` only resolves against the surrounding
 * document — an <img> would render it black in both themes.
 */
export function GroundworkMark() {
  return (
    // The wordmark next to it already names the site, so the mark is
    // decorative to a screen reader rather than a second "Groundwork".
    <svg viewBox="0 0 32 32" width="1.5em" height="1.5em" fill="none" aria-hidden="true">
      <path d="M16 .5V7" stroke="currentColor" strokeWidth="2" />
      <path d="M16 7 22.5 14.5 16 29.4 9.5 14.5Z" fill="currentColor" />
      <path d="M2 31H30" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}
