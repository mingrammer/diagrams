// Maps a catalog module's provider segment (e.g. "aws", "k8s") to the
// display name shown as a tree row in the sidebar. Known providers use their
// canonical casing; anything else falls back to a simple capitalize.
const KNOWN_LABELS: Record<string, string> = {
  aws: "AWS",
  gcp: "GCP",
  k8s: "K8s",
  onprem: "OnPrem",
  alibabacloud: "AlibabaCloud",
  digitalocean: "DigitalOcean",
  ibm: "IBM",
  oci: "OCI",
  openstack: "OpenStack",
  saas: "SaaS",
  elastic: "Elastic",
  firebase: "Firebase",
  azure: "Azure",
  generic: "Generic",
  programming: "Programming",
  outscale: "Outscale",
  gis: "GIS",
  c4: "C4",
};

function capitalize(value: string): string {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

export function providerLabel(provider: string): string {
  return KNOWN_LABELS[provider.toLowerCase()] ?? capitalize(provider);
}
