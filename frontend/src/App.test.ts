import { describe, expect, it } from "vitest";

import { allowedNavigation } from "./App";

describe("role-aware navigation", () => {
  it("does not render privileged navigation for an employee", () => {
    const labels = allowedNavigation("EMPLOYEE").map((item) => item.label);
    expect(labels).toEqual(["Documents", "Upload", "Profile"]);
  });

  it("renders audit and anomaly destinations only for security roles", () => {
    expect(allowedNavigation("AUDITOR").map((item) => item.label)).toContain("Audit center");
    expect(allowedNavigation("AUDITOR").map((item) => item.label)).toContain("Anomalies");
    expect(allowedNavigation("MANAGER").map((item) => item.label)).not.toContain("Anomalies");
  });
});
