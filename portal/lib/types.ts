export interface Artifact {
  id: number;
  slug: string;
  title: string;
  summary: string | null;
  tags: string;
  topics: string;
  html_path: string | null;
  md_path: string | null;
  created_at: string;
  updated_at: string;
}
