import Link from "next/link";
import HeaderNav from "./HeaderNav";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold text-blue-600">
          OfferHub
        </Link>
        <form action="/search" className="hidden sm:flex">
          <input
            name="q"
            placeholder="搜索面试题、面经..."
            className="w-64 px-3 py-1.5 text-sm border border-gray-300 rounded-l-md focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-r-md hover:bg-blue-700"
          >
            搜索
          </button>
        </form>
        <HeaderNav />
      </div>
    </header>
  );
}
