import { describe, expect, it } from "vitest";
import { providerLabel } from "./providerLabel";

describe("providerLabel", () => {
  it("maps known provider keys to their display names", () => {
    expect(providerLabel("aws")).toBe("AWS");
    expect(providerLabel("gcp")).toBe("GCP");
    expect(providerLabel("k8s")).toBe("K8s");
    expect(providerLabel("onprem")).toBe("OnPrem");
    expect(providerLabel("alibabacloud")).toBe("AlibabaCloud");
    expect(providerLabel("digitalocean")).toBe("DigitalOcean");
    expect(providerLabel("ibm")).toBe("IBM");
    expect(providerLabel("oci")).toBe("OCI");
    expect(providerLabel("openstack")).toBe("OpenStack");
    expect(providerLabel("saas")).toBe("SaaS");
    expect(providerLabel("elastic")).toBe("Elastic");
    expect(providerLabel("firebase")).toBe("Firebase");
    expect(providerLabel("azure")).toBe("Azure");
    expect(providerLabel("generic")).toBe("Generic");
    expect(providerLabel("programming")).toBe("Programming");
    expect(providerLabel("outscale")).toBe("Outscale");
    expect(providerLabel("gis")).toBe("GIS");
    expect(providerLabel("c4")).toBe("C4");
  });

  it("falls back to capitalizing unknown providers", () => {
    expect(providerLabel("unknownvendor")).toBe("Unknownvendor");
    expect(providerLabel("foo")).toBe("Foo");
  });

  it("capitalize fallback lowercases the remainder of the string", () => {
    expect(providerLabel("FOObar")).toBe("Foobar");
  });

  it("handles an empty string without throwing", () => {
    expect(providerLabel("")).toBe("");
  });
});
