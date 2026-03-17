import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import Header from "@/components/layout/Header";
import AdminActions from "@/components/admin/AdminActions";
import type { ArticleListItem, ArticleListOut } from "@/types";

// SSR 内部调用：仅在 Docker 内网使用，不接受用户输入，无 SSRF 风险
const API_BASE = process.env.INTERNAL_API_URL ?? "http://api:8000/api/v1";

async function getPendingArticles(token: string): Promise<ArticleListOut> {
  try {
    const res = await fetch(`${API_BASE}/admin/articles/pending?page_size=50`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    const json = await res.json();
    if (json.code !== 0) return { total: 0, page: 1, page_size: 50, items: [] };
    return json.data as ArticleListOut;
  } catch {
    return { total: 0, page: 1, page_size: 50, items: [] };
  }
}

export const metadata = { title: "管理后台 | OfferHub" };

export default async function AdminPage() {
  // SSR 读 cookie 中的 token（投稿页登录后写入）
  const cookieStore = cookies();
  const token = cookieStore.get("token")?.value ?? "";

  if (!token) redirect("/");

  const data = await getPendingArticles(token);

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900">待审核文章</h1>
          <span className="text-sm text-gray-500">{data.total} 篇待审</span>
        </div>

        {data.items.length === 0 ? (
          <div className="text-center py-20 text-gray-400">暂无待审核文章 🎉</div>
        ) : (
          <div className="space-y-3">
            {data.items.map((article) => (
              <PendingCard key={article.id} article={article} token={token} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}

function PendingCard({ article, token }: { article: ArticleListItem; token: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
            {article.category && <span className="text-blue-500">{article.category}</span>}
            <span>·</span>
            <span>{article.author.username}</span>
            <span>·</span>
            <span>{article.created_at ? new Date(article.created_at).toLocaleDateString("zh-CN") : ""}</span>
          </div>
          <a
            href={`/articles/${article.id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-base font-semibold text-gray-900 hover:text-blue-600 line-clamp-1"
          >
            {article.title}
          </a>
          {article.summary && (
            <p className="text-sm text-gray-500 line-clamp-2 mt-1">{article.summary}</p>
          )}
          {article.tags.length > 0 && (
            <div className="flex gap-1 flex-wrap mt-2">
              {article.tags.map((t) => (
                <span key={t.id} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">{t.name}</span>
              ))}
            </div>
          )}
        </div>
        <AdminActions articleId={article.id} token={token} />
      </div>
    </div>
  );
}
