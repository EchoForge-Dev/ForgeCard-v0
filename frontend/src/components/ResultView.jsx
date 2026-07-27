import { motion } from "framer-motion";
import CornerMarkers from "./CornerMarkers";
import StatusDot from "./StatusDot";
import AutoReturnBar from "./AutoReturnBar";
import { truncateMiddle } from "@/lib/format";

function Field({ label, value }) {
  return (
    <div>
      <p className="label-tech">{label}</p>
      <p className="value-tech mt-1">{value}</p>
    </div>
  );
}

export default function ResultView({ profile, autoReturnMs }) {
  const {
    display_name: displayName,
    tier_name: tierName,
    tier_cn: tierCn,
    role,
    days_since_joined: days,
    tagline,
    narrative,
    stake_address: stakeAddress,
  } = profile;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: 16 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96, y: -16 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="relative mx-auto flex w-[680px] max-w-full flex-col gap-5 rounded-2xl glass-panel-strong p-8"
    >
      <CornerMarkers />

      <div className="flex items-center justify-between">
        <p className="label-tech">EchoID Profile</p>
        <div className="flex items-center gap-2">
          <StatusDot variant="success" />
          <p className="label-tech">Verified</p>
        </div>
      </div>

      <h1
        className="text-3xl font-black uppercase tracking-[0.05em]"
        style={{ color: "var(--text-primary)" }}
      >
        {displayName}
      </h1>

      <div className="h-px w-full" style={{ background: "var(--border-color)" }} />

      <div className="grid grid-cols-3 gap-6">
        <Field label="Tier" value={tierCn ? `${tierName} (${tierCn})` : tierName} />
        <Field label="Role" value={role} />
        <Field label="Days Since Joined" value={days} />
      </div>

      <Field label="Stake Address" value={truncateMiddle(stakeAddress)} />

      {tagline ? (
        <p
          className="mt-1 text-center text-sm italic"
          style={{ color: "var(--text-secondary)" }}
        >
          &ldquo;{tagline}&rdquo;
        </p>
      ) : null}

      {narrative ? (
        <p
          className="text-center text-[11px] leading-relaxed"
          style={{
            color: "var(--text-secondary)",
            opacity: 0.7,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {narrative}
        </p>
      ) : null}

      <AutoReturnBar durationMs={autoReturnMs} />
    </motion.div>
  );
}
