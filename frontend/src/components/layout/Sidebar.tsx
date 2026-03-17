import Link from "next/link";
import type { ArticleListItem } from "@/types";

const CATEGORIES = ["面经分享", "技术文章", "学习路径", "面试技巧", "行业资讯", "题库解析"];

interface Props {
  activeCategory?: string;
}

export default function Sidebar({ activeCategory }: Props) {
  return (
    <aside className="w-48 shrink-0">
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h2 className="text-sm font-semibold text-gray-500 mb-3">分类</h2>
        <ul className="space-y-1">
          <li>
            <Link
              href="/"
              className={`block px-2 py-1.5 rounded text-sm ${!activeCategory ? "bg-blue-50 text-blue-600 font-medium" : "text-gray-700 hover:bg-gray-50"}`}
            >
              全部
            </Link>
          </li>
          {CATEGORIES.map((cat) => (
            <li key={cat}>
              <Link
                href={`/category/${encodeURIComponent(cat)}`}
                className={`block px-2 py-1.5 rounded text-sm ${activeCategory === cat ? "bg-blue-50 text-blue-600 font-medium" : "text-gray-700 hover:bg-gray-50"}`}
              >
                {cat}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
