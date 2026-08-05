"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import KioskFrame from "@/components/KioskFrame";
import { fetchEchoIdProfile, normalizeProfile } from "@/lib/echoid";
import { RESULT_AUTO_RETURN_MS, ERROR_AUTO_RETURN_MS, MIN_SCANNING_MS } from "@/lib/constants";

const IDLE_STATE = { kind: "idle" };

// Static example payloads for `?preview=<key>` -- lets the kiosk UI be
// reviewed in a browser without Python, a PN532 reader, or network access.
const PREVIEW_STATES = {
  idle: IDLE_STATE,
  scanning: { kind: "scanning", address: "stake_test1urexq2pxpa98x6vhrl54d3pq25jauh89n4geyvc87gvklqcrkfs6s" },
  ok: {
    kind: "result",
    profile: {
      display_name: "Charles",
      stake_address:
        "stake_test1urexq2pxpa98x6vhrl54d3pq25jauh89n4geyvc87gvklqcrkfs6s",
      tier_name: "Mirror",
      tier_cn: "镜",
      role: "Active Member",
      days_since_joined: 67,
      tagline: "Resolve forged through market cycles.",
      narrative:
        "1,000 ADA across the cycles. When others sold, you held. When the ecosystem needed capital, you gave it.",
    },
  },
  unbound: { kind: "error", status: "unbound" },
  no_profile: {
    kind: "error",
    status: "no_profile",
    address: "stake_test1qnoprofileexampleaddress0000000000000000",
  },
  error: {
    kind: "error",
    status: "error",
    address: "stake_test1qerrorexampleaddress00000000000000000000",
  },
};

function KioskPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const previewKey = searchParams.get("preview");
  const address = searchParams.get("address");
  // Pi-side signal for "card read, but no local binding" -- carries no UID and
  // says nothing about the binding table, so the decoupling contract holds.
  const status = searchParams.get("status");
  const preview = previewKey ? PREVIEW_STATES[previewKey] : null;

  // Start in the state the URL already implies. Initializing to idle and
  // correcting inside the effect renders IdleView for one frame first, which
  // AnimatePresence turns into a visible flash before "Verifying" appears —
  // the first of the three jumps a tap used to produce.
  const [viewState, setViewState] = useState(() =>
    address || status === "unbound" ? { kind: "scanning", address } : IDLE_STATE
  );
  const timerRef = useRef(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (preview) return;
    clearTimeout(timerRef.current);

    const returnToIdle = () => router.replace("/");

    // No parameters at all — this is idle, including the auto-return that
    // clears them. Bump the request id so a lookup still in flight from the
    // previous tap can't paint over the idle screen when it lands.
    if (!address && status !== "unbound") {
      requestIdRef.current += 1;
      setViewState(IDLE_STATE);
      return;
    }

    const requestId = ++requestIdRef.current;
    const isStale = () => requestIdRef.current !== requestId;
    const scanningSince = Date.now();

    setViewState({ kind: "scanning", address });

    // Hold "Verifying" for MIN_SCANNING_MS even when the answer is already in
    // hand, so every tap has the same rhythm regardless of how fast (or
    // whether) the EchoID request resolved.
    const settle = (next, autoReturnMs) => {
      if (isStale()) return;
      const remaining = Math.max(0, MIN_SCANNING_MS - (Date.now() - scanningSince));
      timerRef.current = setTimeout(() => {
        if (isStale()) return;
        setViewState(next);
        timerRef.current = setTimeout(returnToIdle, autoReturnMs);
      }, remaining);
    };

    // `status` wins over `address`: the Pi sends one or the other, never both.
    // This path makes no request, so without the floor it would snap straight
    // to "Card Not Registered" with no visible acknowledgement of the tap.
    if (status === "unbound") {
      settle({ kind: "error", status: "unbound" }, ERROR_AUTO_RETURN_MS);
      return;
    }

    fetchEchoIdProfile(address)
      .then((raw) => {
        if (!raw) {
          settle({ kind: "error", status: "no_profile", address }, ERROR_AUTO_RETURN_MS);
        } else {
          settle(
            { kind: "result", profile: normalizeProfile(address, raw) },
            RESULT_AUTO_RETURN_MS
          );
        }
      })
      .catch(() => {
        settle({ kind: "error", status: "error", address }, ERROR_AUTO_RETURN_MS);
      });
  }, [address, status, preview, router]);

  useEffect(() => () => clearTimeout(timerRef.current), []);

  return <KioskFrame viewState={preview ?? viewState} />;
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <KioskPage />
    </Suspense>
  );
}
