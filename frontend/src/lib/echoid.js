/**
 * Client-side EchoID profile lookup by stake address.
 *
 * Mirrors the already-verified `echoid_client.py` (same base URL, same
 * endpoint, same response shape: data.profile / data.tierMeta) but runs
 * in the browser. The Python side only ever hands the kiosk a stake
 * address via `?address=` -- deciding *how* to resolve that address
 * (which accountType to query) is the frontend's job, not Python's.
 */

const BASE_URL = process.env.NEXT_PUBLIC_ECHOID_API_URL || "https://api-id.echoforgeef.com";

async function fetchProfileAs(address, accountType) {
  const url = `${BASE_URL}/api/echoid/profile/${encodeURIComponent(address)}?accountType=${accountType}`;
  const res = await fetch(url);

  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`EchoID API error: ${res.status}`);
  return res.json();
}

/**
 * Resolves a profile for a stake address. Tries `individual` first, then
 * `institutional` -- we're only ever handed the address, not the account
 * type, so this is the frontend deciding how to resolve it.
 * Returns null if neither account type has a profile.
 */
export async function fetchEchoIdProfile(address) {
  const individual = await fetchProfileAs(address, "individual");
  if (individual) return individual;
  return fetchProfileAs(address, "institutional");
}

/** Flattens the raw EchoID API response into the shape the kiosk views render. */
export function normalizeProfile(stakeAddress, rawProfile) {
  const data = rawProfile.data;
  const profileInfo = data.profile;
  const tier = data.tierMeta;

  return {
    display_name: profileInfo.display_name || "Unnamed",
    stake_address: stakeAddress,
    tier_name: tier.name,
    tier_cn: tier.cn,
    role: tier.role,
    days_since_joined: data.daysSinceJoined,
    tagline: tier.forgeTagline,
    narrative: tier.narrative,
  };
}
