'use client';

import React from 'react';
import Link from "next/link";

export function FooterContent() {
  return (
    <>
      <a
        className="hover:underline hover:underline-offset-4"
        href="https://nextjs.org/learn"
        target="_blank"
        rel="noopener noreferrer"
      >
        Learn
      </a>
      <a
        className="hover:underline hover:underline-offset-4"
        href="https://vercel.com/templates"
        target="_blank"
        rel="noopener noreferrer"
      >
        Examples
      </a>
      <a
        className="hover:underline hover:underline-offset-4"
        href="https://nextjs.org"
        target="_blank"
        rel="noopener noreferrer"
      >
        Go to nextjs.org →
      </a>
      <Link
        href="/admin"
        className="hover:underline hover:underline-offset-4"
      >
        Admin
      </Link>
    </>
  );
} 