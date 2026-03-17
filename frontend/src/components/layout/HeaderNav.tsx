"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function HeaderNav() {
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(!!localStorage.getItem("token"));
  }, []);

  function logout() {
    localStorage.removeItem("token");
    document.cookie = "token=; path=/; max-age=0";
    setLoggedIn(false);
    router.push("/");
  }

  if (!loggedIn) {
    return (
      <nav className="flex items-center gap-3 text-sm">
        <Link href="/login" className="text-gray-600 hover:text-blue-600">登录</Link>
        <Link href="/register" className="px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700">注册</Link>
      </nav>
    );
  }

  return (
    <nav className="flex items-center gap-4 text-sm">
      <Link href="/write" className="text-gray-600 hover:text-blue-600">投稿</Link>
      <Link href="/admin" className="text-gray-600 hover:text-blue-600">管理</Link>
      <button onClick={logout} className="text-gray-400 hover:text-gray-600">退出</button>
    </nav>
  );
}
