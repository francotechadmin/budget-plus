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
import { useUpsertUserMutation } from "./hooks/api/useUserUpsert.ts";

const rootRoute = createRootRoute({
  component: () => (
    <>
      <div className="py-2 px-4 flex gap-2 justify-between items-center">
        <div className="flex ">
          {/* logo Budget+ */}
          <div className="flex items-center px-2">
            <Notebook className="h-6 w-6" />
            <span className="font-bold text-2xl px-1">Budget+</span>
          </div>

          <NavigationMenu>
            <NavigationMenuList>
              <NavigationMenuItem>
                <NavigationMenuLink
                  asChild
                  className={navigationMenuTriggerStyle()}
                >
                  <Link to="/">Transactions</Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuLink
                  asChild
                  className={navigationMenuTriggerStyle()}
                >
                  <Link to="/charts">Expenses</Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuLink
                  asChild
                  className={navigationMenuTriggerStyle()}
                >
                  <Link to="/budget">Budget</Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuLink
                  asChild
                  className={navigationMenuTriggerStyle()}
                >
                  <Link to="/analysis">History</Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        </div>
        <div className="flex gap-2">
          {/* dark mode */}
          <Button
            variant="outline"
            className="h-8"
            onClick={() => {
              // toggle dark mode
              document.body.classList.toggle("dark");
            }}
          >
            Toggle Mode
          </Button>
          {/* logout */}
          <Button
            variant="outline"
            className="h-8"
            onClick={() => {
              window.location.href = "/logout";
            }}
          >
            Logout
          </Button>
        </div>
      </div>
      <hr />
      {/* toggle */}
      <Outlet />
    </>
  ),
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
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
  path: "/charts",
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
  path: "/budget",
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
  path: "/analysis",
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
