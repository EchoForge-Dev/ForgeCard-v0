"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import KioskFrame from "@/components/KioskFrame";
import { fetchEchoIdProfile, normalizeProfile } from "@/lib/echoid";
import { RESULT_AUTO_RETURN_MS, ERROR_AUTO_RETURN_MS } from "@/lib/constants";

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

  const [viewState, setViewState] = useState(IDLE_STATE);
  const timerRef = useRef(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (preview) return;
    clearTimeout(timerRef.current);

    const returnToIdle = () => router.replace("/");

    // `status` wins over `address`: the Pi sends one or the other, never both.
    if (status === "unbound") {
      // Invalidate any in-flight lookup so its late response can't overwrite this.
      requestIdRef.current += 1;
      setViewState({ kind: "error", status: "unbound" });
      timerRef.current = setTimeout(returnToIdle, ERROR_AUTO_RETURN_MS);
      return;
    }

    if (!address) {
      setViewState(IDLE_STATE);
      return;
    }

    const requestId = ++requestIdRef.current;
    const isStale = () => requestIdRef.current !== requestId;

    setViewState({ kind: "scanning", address });

    fetchEchoIdProfile(address)
      .then((raw) => {
        if (isStale()) return;
        if (!raw) {
          setViewState({ kind: "error", status: "no_profile", address });
        } else {
          setViewState({ kind: "result", profile: normalizeProfile(address, raw) });
        }
        timerRef.current = setTimeout(
          returnToIdle,
          raw ? RESULT_AUTO_RETURN_MS : ERROR_AUTO_RETURN_MS
        );
      })
      .catch(() => {
        if (isStale()) return;
        setViewState({ kind: "error", status: "error", address });
        timerRef.current = setTimeout(returnToIdle, ERROR_AUTO_RETURN_MS);
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
