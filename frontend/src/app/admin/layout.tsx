import React from 'react';
import Link from 'next/link';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-900 text-white py-4">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <Link href="/admin" className="text-xl font-bold">A.Educação Admin</Link>
          <nav>
            <ul className="flex space-x-6">
              <li>
                <Link href="/admin/content" className="hover:text-blue-300 transition">
                  Conteúdo
                </Link>
              </li>
              <li>
                <Link href="/admin/performance" className="hover:text-blue-300 transition">
                  Performance
                </Link>
              </li>
              <li>
                <Link href="/admin/learning" className="hover:text-blue-300 transition">
                  Aprendizagem
                </Link>
              </li>
              <li>
                <Link href="/learning" className="hover:text-blue-300 transition">
                  Avaliação Adaptativa
                </Link>
              </li>
              <li>
                <Link href="/" className="hover:text-blue-300 transition">
                  Voltar ao Site
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>
      
      <main className="flex-1 bg-gray-50">
        {children}
      </main>
      
      <footer className="bg-gray-900 text-gray-400 py-4 text-center text-sm">
        <div className="container mx-auto">
          &copy; {new Date().getFullYear()} A.Educação - Painel Administrativo
        </div>
      </footer>
    </div>
  );
} 