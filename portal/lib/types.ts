export interface Artifact {
  id: number;
  slug: string;
  title: string;
  summary: string;
  tags: string;
  topics: string;
  html_path: string;
  md_path: string | null;
  created_at: string;
  updated_at: string;
}
