"use client";

import clsx from "clsx";

const STATUS_CLASSES: Record<string, string> = {
  fresh: "badge badge--green",
  verifying: "badge badge--amber",
  stale: "badge badge--grey",
  broken: "badge badge--red",
  trve: "badge badge--blue",
};

const STATUS_LABELS: Record<string, string> = {
  fresh: "Frais",
  verifying: "Vérification en cours",
  stale: "Obsolète",
  broken: "En panne",
  trve: "📋 Tarif Réglementé",
};

interface FreshnessBadgeProps {
  status: string;
  isTrve?: boolean;
}

export function FreshnessBadge({ status, isTrve = false }: FreshnessBadgeProps) {
  const displayStatus = isTrve ? "trve" : status;

  return (
    <span className={clsx("badge", STATUS_CLASSES[displayStatus] || "badge--grey")}>
      {STATUS_LABELS[displayStatus] || status}
    </span>
  );
}
