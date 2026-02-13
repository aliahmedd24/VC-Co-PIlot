import { render, screen } from "@testing-library/react";
import { PercentileBar } from "@/components/charts/PercentileBar";

// Mock recharts to avoid canvas issues in jsdom
jest.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  RadarChart: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  PolarGrid: () => null,
  PolarAngleAxis: () => null,
  PolarRadiusAxis: () => null,
  Radar: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Cell: () => null,
}));

describe("PercentileBar", () => {
  test("renders label and classification", () => {
    render(
      <PercentileBar
        label="MRR Growth"
        percentile={75}
        p25={10}
        median={20}
        p75={30}
        value={25}
        classification="strong"
      />
    );

    expect(screen.getByText("MRR Growth")).toBeInTheDocument();
    expect(screen.getByText(/P75/)).toBeInTheDocument();
    expect(screen.getByText(/strong/)).toBeInTheDocument();
  });

  test("renders with weak classification", () => {
    render(
      <PercentileBar
        label="Burn Rate"
        percentile={15}
        p25={50}
        median={75}
        p75={100}
        value={40}
        classification="weak"
      />
    );

    expect(screen.getByText("Burn Rate")).toBeInTheDocument();
    expect(screen.getByText(/weak/)).toBeInTheDocument();
  });

  test("renders data-testid for test discovery", () => {
    render(
      <PercentileBar
        label="Test"
        percentile={50}
        p25={25}
        median={50}
        p75={75}
        value={50}
        classification="average"
      />
    );

    expect(screen.getByTestId("percentile-bar")).toBeInTheDocument();
  });
});
