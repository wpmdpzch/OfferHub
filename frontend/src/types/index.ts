export interface Author {
  id: string;
  username: string;
  avatar_url: string | null;
}

export interface Tag {
  id: number;
  name: string;
}

export interface ArticleListItem {
  id: string;
  title: string;
  summary: string | null;
  category: string | null;
  sub_category: string | null;
  tags: Tag[];
  author: Author;
  source_url: string | null;
  source_type: string;
  status: string;
  view_count: number;
  like_count: number;
  collect_count: number;
  comment_count: number;
  published_at: string | null;
  created_at: string;
}

export interface ArticleDetail extends ArticleListItem {
  content: string | null;
  source_license: string | null;
  updated_at: string;
  viewer_liked: boolean | null;
  viewer_collected: boolean | null;
}

export interface ArticleListOut {
  total: number;
  page: number;
  page_size: number;
  items: ArticleListItem[];
}

export interface User {
  id: string;
  username: string;
  email: string;
  avatar_url: string | null;
  role: string;
  points: number;
  created_at: string;
}
