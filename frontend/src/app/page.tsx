import { api } from "@/lib/api";
import type { ArticleListOut } from "@/types";
import ArticleCard from "@/components/article/ArticleCard";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import Link from "next/link";

interface Props {
  searchParams: { page?: string; sort?: string };
}

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
      <main className="max-w-6xl mx-auto px-4 py-6 flex gap-6">
        <Sidebar />
        <div className="flex-1 min-w-0">
          {/* 排序 */}
          <div className="flex gap-3 mb-4 text-sm">
            {["latest", "hot"].map((s) => (
              <Link
                key={s}
                href={`/?sort=${s}`}
                className={`px-3 py-1 rounded-full ${sort === s ? "bg-blue-600 text-white" : "bg-white border border-gray-200 text-gray-600 hover:border-blue-400"}`}
              >
                {s === "latest" ? "最新" : "最热"}
              </Link>
            ))}
          </div>

          {/* 文章列表 */}
          <div className="space-y-3">
            {data.items.length === 0 ? (
              <div className="text-center py-20 text-gray-400">暂无内容</div>
            ) : (
              data.items.map((article) => <ArticleCard key={article.id} article={article} />)
            )}
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              {page > 1 && (
                <Link href={`/?page=${page - 1}&sort=${sort}`} className="px-4 py-2 border rounded text-sm hover:bg-gray-50">
                  上一页
                </Link>
              )}
              <span className="px-4 py-2 text-sm text-gray-500">{page} / {totalPages}</span>
              {page < totalPages && (
                <Link href={`/?page=${page + 1}&sort=${sort}`} className="px-4 py-2 border rounded text-sm hover:bg-gray-50">
                  下一页
                </Link>
              )}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
