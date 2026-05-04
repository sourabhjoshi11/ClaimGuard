import { Link, useNavigate } from "@tanstack/react-router";
import { Shield, LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";

export function Header() {
  const { isAuthenticated, auth, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[image:var(--gradient-primary)] shadow-[var(--shadow-elegant)]">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold tracking-tight text-foreground">ClaimGuard</span>
            <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">AI</span>
          </div>
        </Link>

        <nav className="flex items-center gap-1">
          {isAuthenticated ? (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link to="/claims">My Claims</Link>
              </Button>
              <Button asChild variant="default" size="sm">
                <Link to="/claims/new">New Claim</Link>
              </Button>
              <div className="mx-3 hidden text-sm text-muted-foreground sm:block">
                {auth?.user?.username}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  logout();
                  navigate({ to: "/login" });
                }}
                aria-label="Log out"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link to="/login">Sign in</Link>
              </Button>
              <Button asChild variant="default" size="sm">
                <Link to="/register">Get started</Link>
              </Button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
