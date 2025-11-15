"use client";

import clsx from "clsx";

const STATUS_CLASSES: Record<string, string> = {
  fresh: "badge badge--green",
  verifying: "badge badge--amber",
  stale: "badge badge--grey",
  broken: "badge badge--red",
};

const STATUS_LABELS: Record<string, string> = {
  fresh: "Frais",
  verifying: "Vérification en cours",
  stale: "Obsolète",
  broken: "En panne",
};

export function FreshnessBadge({ status }: { status: string }) {
  return <span className={clsx("badge", STATUS_CLASSES[status] || "badge--grey")}>{STATUS_LABELS[status] || status}</span>;
}
