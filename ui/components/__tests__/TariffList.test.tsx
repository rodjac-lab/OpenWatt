import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TariffList } from "../TariffList";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockTariffs = [
  {
    id: 1,
    supplier: "EDF",
    option: "BASE",
    puissance_kva: 6,
    abo_month_ttc: 12.5,
    price_kwh_ttc: 0.2,
    price_kwh_hp_ttc: null,
    price_kwh_hc_ttc: null,
    data_status: "fresh",
  },
  {
    id: 2,
    supplier: "ENGIE",
    option: "HPHC",
    puissance_kva: 6,
    abo_month_ttc: 15.0,
    price_kwh_ttc: null,
    price_kwh_hp_ttc: 0.25,
    price_kwh_hc_ttc: 0.18,
    data_status: "stale",
  },
  {
    id: 3,
    supplier: "TotalEnergies",
    option: "BASE",
    puissance_kva: 9,
    abo_month_ttc: 18.0,
    price_kwh_ttc: 0.22,
    price_kwh_hp_ttc: null,
    price_kwh_hc_ttc: null,
    data_status: "broken",
  },
];

const mockTrveDiff = [
  {
    supplier: "EDF",
    option: "BASE",
    puissance_kva: 6,
    delta_eur_per_mwh: 5.0,
    status: "ok",
  },
  {
    supplier: "ENGIE",
    option: "HPHC",
    puissance_kva: 6,
    delta_eur_per_mwh: -10.0,
    status: "ok",
  },
];

// Helper to mock both API calls
const mockBothApis = (tariffs = mockTariffs, trveDiff = mockTrveDiff) => {
  mockFetch.mockImplementation((url: string) => {
    if (url.includes("/v1/tariffs")) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ items: tariffs }),
      });
    }
    if (url.includes("/v1/guards/trve-diff")) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ items: trveDiff }),
      });
    }
    return Promise.reject(new Error("Unknown URL"));
  });
};

describe("TariffList", () => {
  beforeEach(() => {
    mockFetch.mockClear();
    mockBothApis();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading state initially", () => {
    mockFetch.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<TariffList />);
    expect(screen.getByText(/chargement/i)).toBeInTheDocument();
  });

  it("fetches and displays tariffs", async () => {
    render(<TariffList />);

    await waitFor(() => {
      expect(screen.queryByText(/chargement/i)).not.toBeInTheDocument();
    });

    expect(screen.getAllByText("EDF").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ENGIE").length).toBeGreaterThan(0);
    expect(screen.getAllByText("TotalEnergies").length).toBeGreaterThan(0);
  });

  it("displays error message when fetch fails", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("filters tariffs by option", async () => {
    const user = userEvent.setup();
    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
    });

    // Filter by BASE option
    const optionSelect = screen.getByLabelText(/option/i);
    await user.selectOptions(optionSelect, "BASE");

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
      expect(screen.getByText("TotalEnergies")).toBeInTheDocument();
      expect(screen.queryByText("ENGIE")).not.toBeInTheDocument();
    });
  });

  it("filters tariffs by puissance", async () => {
    const user = userEvent.setup();
    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
    });

    // Filter by 6 kVA
    const puissanceSelect = screen.getByLabelText(/puissance/i);
    await user.selectOptions(puissanceSelect, "6");

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
      expect(screen.getByText("ENGIE")).toBeInTheDocument();
      expect(screen.queryByText("TotalEnergies")).not.toBeInTheDocument();
    });
  });

  it("calculates annual cost correctly for BASE option", async () => {
    mockBothApis([
      {
        id: 1,
        supplier: "EDF",
        option: "BASE",
        puissance_kva: 6,
        abo_month_ttc: 10.0,
        price_kwh_ttc: 0.2,
        data_status: "fresh",
      },
    ]);

    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
    });

    // Annual cost = (10 * 12) + (5000 * 0.2) = 120 + 1000 = 1120 €
    expect(screen.getByText("1120 €")).toBeInTheDocument();
  });

  it("updates consumption and recalculates cost", async () => {
    mockBothApis([
      {
        id: 1,
        supplier: "EDF",
        option: "BASE",
        puissance_kva: 6,
        abo_month_ttc: 10.0,
        price_kwh_ttc: 0.2,
        data_status: "fresh",
      },
    ]);

    const user = userEvent.setup();
    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
    });

    // Change consumption to 10000 kWh
    const consumptionInput = screen.getByLabelText(/consommation/i);
    await user.clear(consumptionInput);
    await user.type(consumptionInput, "10000");

    await waitFor(() => {
      // Annual cost = (10 * 12) + (10000 * 0.2) = 120 + 2000 = 2120 €
      expect(screen.getByText("2120 €")).toBeInTheDocument();
    });
  });

  it("sorts tariffs by annual cost ascending", async () => {
    mockBothApis([
      {
        id: 1,
        supplier: "Expensive",
        option: "BASE",
        puissance_kva: 6,
        abo_month_ttc: 20.0,
        price_kwh_ttc: 0.3,
        data_status: "fresh",
      },
      {
        id: 2,
        supplier: "Cheap",
        option: "BASE",
        puissance_kva: 6,
        abo_month_ttc: 5.0,
        price_kwh_ttc: 0.1,
        data_status: "fresh",
      },
    ]);

    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("Cheap")).toBeInTheDocument();
    });

    const rows = screen.getAllByRole("row");
    const dataRows = rows.slice(1); // Skip header row

    // First data row should be "Cheap" (lower cost)
    expect(dataRows[0]).toHaveTextContent("Cheap");
    // Second data row should be "Expensive"
    expect(dataRows[1]).toHaveTextContent("Expensive");
  });

  it("renders FreshnessBadge for each tariff", async () => {
    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("Frais")).toBeInTheDocument(); // fresh
      expect(screen.getByText("Obsolète")).toBeInTheDocument(); // stale
      expect(screen.getByText("En panne")).toBeInTheDocument(); // broken
    });
  });
});
