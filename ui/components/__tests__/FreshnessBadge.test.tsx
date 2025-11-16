import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FreshnessBadge } from "../FreshnessBadge";

describe("FreshnessBadge", () => {
  it("renders fresh status with correct label and class", () => {
    render(<FreshnessBadge status="fresh" />);

    const badge = screen.getByText("Frais");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("badge", "badge--green");
  });

  it("renders verifying status with correct label and class", () => {
    render(<FreshnessBadge status="verifying" />);

    const badge = screen.getByText("Vérification en cours");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("badge", "badge--amber");
  });

  it("renders stale status with correct label and class", () => {
    render(<FreshnessBadge status="stale" />);

    const badge = screen.getByText("Obsolète");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("badge", "badge--grey");
  });

  it("renders broken status with correct label and class", () => {
    render(<FreshnessBadge status="broken" />);

    const badge = screen.getByText("En panne");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("badge", "badge--red");
  });

  it("renders unknown status with fallback grey class and raw status text", () => {
    render(<FreshnessBadge status="unknown" />);

    const badge = screen.getByText("unknown");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("badge", "badge--grey");
  });

  it("renders empty status with fallback grey class", () => {
    const { container } = render(<FreshnessBadge status="" />);

    const badge = container.querySelector("span.badge");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("badge", "badge--grey");
    expect(badge).toHaveTextContent("");
  });
});
