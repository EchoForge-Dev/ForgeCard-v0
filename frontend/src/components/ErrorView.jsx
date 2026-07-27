import { motion } from "framer-motion";
import CornerMarkers from "./CornerMarkers";
import StatusDot from "./StatusDot";
import AutoReturnBar from "./AutoReturnBar";
import { truncateMiddle } from "@/lib/format";

const COPY = {
  unbound: {
    title: "Card Not Registered",
    body: "This card isn't bound to an EchoID yet. Ask an organizer to register it.",
  },
  no_profile: {
    title: "No EchoID Profile",
    body: "This stake address hasn't created an EchoID profile yet.",
  },
  error: {
    title: "Lookup Failed",
    body: "Something went wrong resolving this address. Please try again.",
  },
};

export default function ErrorView({ address, status, autoReturnMs }) {
  const copy = COPY[status] ?? COPY.error;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: 16 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96, y: -16 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="relative mx-auto flex w-[560px] max-w-full flex-col gap-5 rounded-2xl glass-panel p-8"
    >
      <CornerMarkers />

      <div className="flex items-center gap-2">
        <StatusDot variant="warning" />
        <p className="label-tech">Status</p>
      </div>

      <h1
        className="text-2xl font-bold uppercase tracking-[0.1em]"
        style={{ color: "var(--text-primary)" }}
      >
        {copy.title}
      </h1>

      <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
        {copy.body}
      </p>

      <div className="h-px w-full" style={{ background: "var(--border-color)" }} />

      {address ? <p className="label-tech">{truncateMiddle(address)}</p> : null}

      <AutoReturnBar durationMs={autoReturnMs} />
    </motion.div>
  );
}
