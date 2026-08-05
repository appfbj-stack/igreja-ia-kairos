"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Users, Church, Calendar, MessageSquare, FileText,
  LayoutDashboard, Menu, X
} from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

const nav = [
  { href: "/", label: "Início", icon: LayoutDashboard },
  { href: "/membros", label: "Membros", icon: Users },
  { href: "/congregacoes", label: "Congregações", icon: Church },
  { href: "/agenda", label: "Agenda", icon: Calendar },
  { href: "/chat", label: "Chat Kairos", icon: MessageSquare },
  { href: "/documentos", label: "Documentos", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-kairos-900 text-white shadow-lg"
      >
        <Menu size={22} />
      </button>

      {open && (
        <div className="lg:hidden fixed inset-0 bg-black/40 z-40" onClick={() => setOpen(false)} />
      )}

      <aside
        className={clsx(
          "fixed lg:static inset-y-0 left-0 z-50 w-64 bg-kairos-900 text-white flex flex-col transition-transform duration-200",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Kairos</h1>
            <p className="text-xs text-kairos-200">Gestão Pastoral</p>
          </div>
          <button onClick={() => setOpen(false)} className="lg:hidden p-1">
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {nav.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  active
                    ? "bg-white/15 text-white"
                    : "text-kairos-100 hover:bg-white/10 hover:text-white"
                )}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10 text-xs text-kairos-300">
          MVP v1.0 · Local
        </div>
      </aside>
    </>
  );
}
