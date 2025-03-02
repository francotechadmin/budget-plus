import TransactionsPage from "./pages/TransactionsPage.tsx";
import ExpensesPage from "./pages/ExpensesPage.tsx";
import BudgetPage from "./pages/BudgetPage.tsx";
import HistoryPage from "./pages/HistoryPage.tsx";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import "./index.css";

import {
  Outlet,
  RouterProvider,
  Link,
  createRouter,
  createRoute,
  createRootRoute,
} from "@tanstack/react-router";
import { Notebook } from "lucide-react";
import { Button } from "./components/ui/button.tsx";
import { useAuth0 } from "@auth0/auth0-react";
import { withAuthenticationRequired } from "@auth0/auth0-react";
import Loading from "./components/ui/loading.tsx";
import { useEffect } from "react";
import { addAccessTokenInterceptor } from "./lib/axios.ts";
import { useUpsertUserMutation } from "./hooks/api/useUserUpsertMutation/index.ts";
import { useState } from "react";
import { Moon, LogOut, Menu, X } from "lucide-react";
const basePath = (import.meta.env.VITE_BASE_PATH as string) || "/";

const rootRoute = createRootRoute({
  component: function RootComponent() {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const { logout } = useAuth0();

    return (
      <>
        <div className="py-2 px-4 flex gap-2 justify-between items-center">
          <div className="flex items-center">
            {/* Logo */}
            <div className="flex items-center px-2">
              <Notebook className="h-6 w-6" />
              <span className="font-bold text-2xl px-1">Budget+</span>
            </div>

            {/* Desktop Navigation Menu */}
            <div className="hidden sm:block">
              <NavigationMenu>
                <NavigationMenuList>
                  <NavigationMenuItem>
                    <NavigationMenuLink
                      asChild
                      className={navigationMenuTriggerStyle()}
                    >
                      <Link to={`${basePath}/`}>Transactions</Link>
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                  <NavigationMenuItem>
                    <NavigationMenuLink
                      asChild
                      className={navigationMenuTriggerStyle()}
                    >
                      <Link to={`${basePath}/expenses`}>Expenses</Link>
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                  <NavigationMenuItem>
                    <NavigationMenuLink
                      asChild
                      className={navigationMenuTriggerStyle()}
                    >
                      <Link to={`${basePath}/budget`}>Budget</Link>
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                  <NavigationMenuItem>
                    <NavigationMenuLink
                      asChild
                      className={navigationMenuTriggerStyle()}
                    >
                      <Link to={`${basePath}/history`}>History</Link>
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                </NavigationMenuList>
              </NavigationMenu>
            </div>

            {/* Mobile Hamburger Menu Button */}
            <div className="sm:hidden ml-2">
              <Button
                variant="outline"
                className="h-8 w-8 p-0 flex items-center justify-center"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? (
                  <X className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            {/* Toggle Mode Button */}
            {/* Full text on desktop */}
            <Button
              variant="outline"
              className="h-8 hidden sm:flex items-center"
              onClick={() => document.body.classList.toggle("dark")}
            >
              Toggle Mode
            </Button>
            {/* Icon-only on mobile */}
            <Button
              variant="outline"
              className="h-8 sm:hidden p-2 flex items-center justify-center"
              onClick={() => document.body.classList.toggle("dark")}
            >
              <Moon className="h-4 w-4" />
            </Button>

            {/* Logout Button */}
            {/* Full text on desktop */}
            <Button
              variant="outline"
              className="h-8 hidden p-2 sm:flex items-center"
              onClick={() =>
                logout({ logoutParams: { returnTo: window.location.origin } })
              }
            >
              Logout
            </Button>
            {/* Icon-only on mobile */}
            <Button
              variant="outline"
              className="h-8 sm:hidden p-2 flex items-center justify-center"
              onClick={() =>
                logout({ logoutParams: { returnTo: window.location.origin } })
              }
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Mobile Navigation Dropdown */}
        {mobileMenuOpen && (
          <div className="sm:hidden px-8 pb-2">
            <NavigationMenu>
              <NavigationMenuList className="">
                <NavigationMenuItem>
                  <NavigationMenuLink
                    asChild
                    className={navigationMenuTriggerStyle()}
                  >
                    <Link
                      to={`${basePath}/`}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Transactions
                    </Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    asChild
                    className={navigationMenuTriggerStyle()}
                  >
                    <Link
                      to={`${basePath}/expenses`}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Expenses
                    </Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    asChild
                    className={navigationMenuTriggerStyle()}
                  >
                    <Link
                      to={`${basePath}/budget`}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Budget
                    </Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    asChild
                    className={navigationMenuTriggerStyle()}
                  >
                    <Link
                      to={`${basePath}/history`}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      History
                    </Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>
          </div>
        )}

        <hr />
        <Outlet />
      </>
    );
  },
  notFoundComponent: function NotFound() {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center">
        <h1 className="text-4xl font-bold">404 - Page Not Found</h1>
        <br />
        <div className="flex flex-col items-center">
          <p className="text-lg">
            The page you are looking for does not exist.
          </p>
          <Link to={`${basePath}`} className="text-blue-500 underline">
            Go back
          </Link>
        </div>
      </div>
    );
  },
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: `${basePath}`,
  component: function Index() {
    return (
      <div className="p-2 overflow-y-auto">
        <TransactionsPage />
      </div>
    );
  },
});

const chartsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: `${basePath}/expenses`,
  component: function Charts() {
    return (
      <div className="p-2 overflow-y-auto">
        <ExpensesPage />
      </div>
    );
  },
});

const budgetRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: `${basePath}/budget`,
  component: function Budget() {
    return (
      <div className="p-2 overflow-y-auto">
        <BudgetPage />
      </div>
    );
  },
});

const analysisRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: `${basePath}/history`,
  component: function Analysis() {
    return (
      <div className="p-2 overflow-y-auto">
        <HistoryPage />
      </div>
    );
  },
});

// logout
const logoutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/logout",
  component: function Logout() {
    const { logout } = useAuth0();
    useEffect(() => {
      const logoutWithRedirect = () =>
        logout({
          logoutParams: {
            returnTo: window.location.origin,
          },
        });

      logoutWithRedirect();
    }, [logout]);
    return <Loading />;
  },
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  chartsRoute,
  budgetRoute,
  analysisRoute,
  logoutRoute,
]);

const router = createRouter({ routeTree });

function App() {
  const { isLoading, error, getAccessTokenSilently, user } = useAuth0();
  const upsertUserMutation = useUpsertUserMutation();

  // add access token interceptor to axios
  useEffect(() => {
    addAccessTokenInterceptor(getAccessTokenSilently);
  }, [getAccessTokenSilently]);

  // upsert user on mount
  useEffect(() => {
    if (!isLoading || (!error && user)) {
      upsertUserMutation.mutate();
    }
  }, []);

  if (error) {
    return <div>Oops... {error.message}</div>;
  }

  if (isLoading) {
    return <Loading />;
  }

  return (
    <div className="App h-screen max-w-6xl mx-auto flex flex-col overflow-hidden">
      <RouterProvider router={router} />
    </div>
  );
}

const AuthenticatedApp = withAuthenticationRequired(App, {
  onRedirecting: () => <Loading />,
});

export default AuthenticatedApp;
