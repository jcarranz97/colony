import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const AUTH_PAGES = ["/login", "/register"];
const PROTECTED = [
  "/payment-methods",
  "/expense-templates",
  "/cycles",
  "/settings",
];

export function proxy(request: NextRequest) {
  const token = request.cookies.get("colony-token");
  const { pathname } = request.nextUrl;

  const isAuthPage = AUTH_PAGES.some((p) => pathname.startsWith(p));
  const isProtected =
    PROTECTED.some((p) => pathname.startsWith(p)) || pathname === "/";

  if (isAuthPage && token)
    return NextResponse.redirect(new URL("/cycles", request.url));
  if (isProtected && !token)
    return NextResponse.redirect(new URL("/login", request.url));
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/login",
    "/register",
    "/payment-methods/:path*",
    "/expense-templates/:path*",
    "/cycles/:path*",
    "/settings/:path*",
  ],
};
