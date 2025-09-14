import { Personification } from "@/types/personification";

export interface PersonificationsResponse {
  personifications: Personification[];
  activeChoice: string | null;
}

export async function getPersonifications(): Promise<PersonificationsResponse> {
  const response = await fetch("/api/personifications");

  if (!response.ok) {
    throw new Error("Failed to fetch personifications");
  }

  return response.json();
}

export async function setActivePersonification(
  personificationId: string | null
): Promise<void> {
  const response = await fetch("/api/personifications/active", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ personificationId }),
  });

  if (!response.ok) {
    throw new Error("Failed to update active personification");
  }
}
