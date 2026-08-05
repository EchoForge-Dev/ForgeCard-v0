export const RESULT_AUTO_RETURN_MS = 8000;
export const ERROR_AUTO_RETURN_MS = 6000;

// Floor on how long "Verifying Identity..." stays up before the result replaces
// it. Without one, a fast EchoID response — or the unbound path, which makes no
// request at all — swaps views within a few hundred milliseconds, and the kiosk
// reads as a flicker instead of a sequence. AnimatePresence spends ~0.5s
// animating out and ~0.5s animating in, so anything under ~1s never even
// finishes. This is the one number to turn if the pacing feels off.
export const MIN_SCANNING_MS = 1600;
