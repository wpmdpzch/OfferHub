import { api } from "@/lib/api";
import type { ArticleListOut } from "@/types";
import ArticleCard from "@/components/article/ArticleCard";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import Link from "next/link";

interface Props {
  searchParams: { page?: string; sort?: string };
}

const STATS = [
  { label: "面试题库", value: "10,000+", icon: "📚" },
  { label: "面经分享", value: "5,000+", icon: "💬" },
  { label: "持续更新", value: "每日", icon: "⚡" },
];

export default async function HomePage({ searchParams }: Props) {
  const page = Number(searchParams.page ?? 1);
  const sort = searchParams.sort ?? "latest";

  let data: ArticleListOut = { total: 0, page: 1, page_size: 20, items: [] };
  try {
    data = await api.get<ArticleListOut>(`/articles?page=${page}&sort=${sort}`);
  } catch {}

  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <>
      <Header />
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 to-blue-800 text-white">
        <div className="max-w-6xl mx-auto px-4 py-12">
          <div className="max-w-2xl">
            <h1 className="text-3xl md:text-4xl font-bold mb-4 leading-tight">
              让每个开发者都能拿到心仪 Offer
            </h1>
            <p className="text-blue-100 text-lg mb-6">
              聚合全网优质面试题库，自动采集持续更新，开源免费，帮你消除面试焦虑。
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/search"
                className="px-5 py-2.5 bg-white text-blue-600 font-medium rounded-lg hover:bg-blue-50 transition-colors"
              >
                🔍 搜索面试题
              </Link>
              <Link
                href="/write"
                className="px-5 py-2.5 border border-blue-300 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                ✍️ 分享面经
              </Link>
            </div>
          </div>
        </div>
        {/* Stats Bar */}
        <div className="border-t border-blue-500 bg-blue-700">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <div className="flex flex-wrap justify-center md:justify-start gap-8">
              {STATS.map((stat) => (
                <div key={stat.label} className="flex items-center gap-2">
                  <span className="text-lg">{stat.icon}</span>
                  <span className="text-sm text-blue-100">{stat.label}:</span>
                  <span className="font-semibold">{stat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <main className="max-w-6xl mx-auto px-4 py-6 flex gap-6">
        <Sidebar />
        <div className="flex-1 min-w-0">
          {/* Sort & Filter Bar */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-3 text-sm">
              <Link
                href={`/?sort=latest`}
                className={`px-3 py-1.5 rounded-full transition-colors ${
                  sort === "latest"
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-200 text-gray-600 hover:border-blue-400"
                }`}
              >
                最新
              </Link>
              <Link
                href={`/?sort=hot`}
                className={`px-3 py-1.5 rounded-full transition-colors ${
                  sort === "hot"
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-200 text-gray-600 hover:border-blue-400"
                }`}
              >
                🔥 最热
              </Link>
            </div>
            <span className="text-sm text-gray-500">
              共 {data.total.toLocaleString()} 篇
            </span>
          </div>

          {/* Article List */}
          <div className="space-y-3">
            {data.items.length === 0 ? (
              <div className="text-center py-20 bg-white rounded-lg border border-gray-200">
                <div className="text-4xl mb-3">📭</div>
                <p className="text-gray-400">暂无内容</p>
                <p className="text-sm text-gray-400 mt-1">
                  成为第一个分享者！{" "}
                  <Link href="/write" className="text-blue-500 hover:underline">
                    写文章
                  </Link>
                </p>
              </div>
            ) : (
              data.items.map((article) => <ArticleCard key={article.id} article={article} />)
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              {page > 1 && (
                <Link href={`/?page=${page - 1}&sort=${sort}`} className="px-4 py-2 border border-gray-200 rounded text-sm hover:bg-gray-50 transition-colors">
                  ← 上一页
                </Link>
              )}
              <span className="px-4 py-2 text-sm text-gray-500">
                第 {page} / {totalPages} 页
              </span>
              {page < totalPages && (
                <Link href={`/?page=${page + 1}&sort=${sort}`} className="px-4 py-2 border border-gray-200 rounded text-sm hover:bg-gray-50 transition-colors">
                  下一页 →
                </Link>
              )}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
