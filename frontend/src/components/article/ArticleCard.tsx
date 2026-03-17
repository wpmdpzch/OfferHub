import Link from "next/link";
import type { ArticleListItem } from "@/types";

function formatDate(iso: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}

export default function ArticleCard({ article }: { article: ArticleListItem }) {
  return (
    <article className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
        {article.category && (
          <Link href={`/category/${encodeURIComponent(article.category)}`} className="text-blue-500 hover:underline">
            {article.category}
          </Link>
        )}
        <span>·</span>
        <span>{article.author.username}</span>
        <span>·</span>
        <span>{formatDate(article.published_at)}</span>
      </div>

      <Link href={`/articles/${article.id}`}>
        <h2 className="text-base font-semibold text-gray-900 hover:text-blue-600 line-clamp-2 mb-2">
          {article.title}
        </h2>
      </Link>

      {article.summary && (
        <p className="text-sm text-gray-500 line-clamp-2 mb-3">{article.summary}</p>
      )}

      <div className="flex items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          {article.tags.slice(0, 4).map((tag) => (
            <Link
              key={tag.id}
              href={`/tag/${encodeURIComponent(tag.name)}`}
              className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded hover:bg-blue-50 hover:text-blue-600"
            >
              {tag.name}
            </Link>
          ))}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-400 shrink-0">
          <span>👁 {article.view_count}</span>
          <span>👍 {article.like_count}</span>
          <span>💬 {article.comment_count}</span>
        </div>
      </div>
    </article>
  );
}
