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
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Notebook } from "lucide-react";
import { Button } from "./components/ui/button.tsx";

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
        <div>
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

const routeTree = rootRoute.addChildren([
  indexRoute,
  chartsRoute,
  budgetRoute,
  analysisRoute,
]);

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Create a QueryClient instance
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="App h-screen max-w-6xl mx-auto flex flex-col overflow-hidden">
        <RouterProvider router={router} />
      </div>
    </QueryClientProvider>
  );
}

export default App;
