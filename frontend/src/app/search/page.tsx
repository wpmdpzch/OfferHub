import { api } from "@/lib/api";
import type { ArticleListOut } from "@/types";
import ArticleCard from "@/components/article/ArticleCard";
import Header from "@/components/layout/Header";
import type { Metadata } from "next";
import Link from "next/link";

interface Props {
  searchParams: { q?: string; page?: string };
}

const HOT_TAGS = ["字节跳动", "腾讯", "阿里巴巴", "前端", "算法", "系统设计", "Java", "Python", "Go"];
const HOT_CATEGORIES = ["面经分享", "技术文章", "题库解析"];

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const q = searchParams.q ?? "";
  return q
    ? { title: `"${q}" 搜索结果`, description: `OfferHub 搜索「${q}」的面试题和面经` }
    : { title: "搜索面试题", description: "在 OfferHub 搜索面试题、面经和学习资料" };
}

export default async function SearchPage({ searchParams }: Props) {
  const q = searchParams.q ?? "";
  const page = Number(searchParams.page ?? 1);

  let data: ArticleListOut & { items: any[] } = { total: 0, page: 1, page_size: 20, items: [] };
  if (q) {
    try {
      data = await api.get(`/search?q=${encodeURIComponent(q)}&page=${page}`);
    } catch {}
  }

  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <>
      <Header />
      <main className="max-w-3xl mx-auto px-4 py-8">
        {/* Search Form */}
        <form className="flex gap-2 mb-8" action="/search">
          <input
            name="q"
            defaultValue={q}
            placeholder="搜索面试题、面经..."
            autoFocus
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-5 py-2.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          >
            🔍 搜索
          </button>
        </form>

        {/* Results */}
        {q ? (
          <>
            <p className="text-sm text-gray-500 mb-4">
              「{q}」共找到 <strong>{data.total.toLocaleString()}</strong> 条结果
            </p>
            <div className="space-y-3">
              {data.items.map((item) => (
                <ArticleCard key={item.id} article={item} />
              ))}
            </div>
            {data.items.length === 0 && (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">🔍</div>
                <p className="text-gray-500 mb-2">没有找到相关结果</p>
                <p className="text-sm text-gray-400">试试其他关键词，或浏览下面的热门分类</p>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-8">
                {page > 1 && (
                  <Link href={`/search?q=${encodeURIComponent(q)}&page=${page - 1}`}
                    className="px-4 py-2 border border-gray-200 rounded text-sm hover:bg-gray-50">
                    ← 上一页
                  </Link>
                )}
                <span className="px-4 py-2 text-sm text-gray-500">第 {page} / {totalPages} 页</span>
                {page < totalPages && (
                  <Link href={`/search?q=${encodeURIComponent(q)}&page=${page + 1}`}
                    className="px-4 py-2 border border-gray-200 rounded text-sm hover:bg-gray-50">
                    下一页 →
                  </Link>
                )}
              </div>
            )}
          </>
        ) : (
          /* Empty State - Search Suggestions */
          <div className="space-y-8">
            {/* Hot Tags */}
            <div>
              <h2 className="text-sm font-medium text-gray-500 mb-3">🔥 热门标签</h2>
              <div className="flex flex-wrap gap-2">
                {HOT_TAGS.map((tag) => (
                  <Link
                    key={tag}
                    href={`/search?q=${encodeURIComponent(tag)}`}
                    className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
                  >
                    {tag}
                  </Link>
                ))}
              </div>
            </div>

            {/* Categories */}
            <div>
              <h2 className="text-sm font-medium text-gray-500 mb-3">📂 热门分类</h2>
              <div className="grid grid-cols-3 gap-3">
                {HOT_CATEGORIES.map((cat) => (
                  <Link
                    key={cat}
                    href={`/category/${encodeURIComponent(cat)}`}
                    className="p-4 bg-white border border-gray-200 rounded-lg text-center text-sm text-gray-700 hover:border-blue-400 hover:text-blue-600 transition-colors"
                  >
                    {cat}
                  </Link>
                ))}
              </div>
            </div>

            {/* Quick Tips */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-800 mb-2">💡 搜索技巧</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• 输入公司名，如「字节跳动」「腾讯」</li>
                <li>• 输入技术栈，如「React」「Redis」「系统设计」</li>
                <li>• 输入职位，如「前端」「后端」「算法」</li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
