export interface Personification {
  id: string;
  name: string;
  content: string; // Combined description, style, and prompts
  quotes: string[];
  profilePic?: string; // URL or base64 image
  elevenLabsId?: string; // ElevenLabs voice ID
  status: "active" | "inactive" | "training";
  createdAt: string;
  updatedAt: string;
}
