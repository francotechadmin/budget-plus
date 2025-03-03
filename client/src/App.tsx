// index.tsx
import React from "react";
import { StrictMode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Auth0Provider } from "@auth0/auth0-react";
import { getConfig } from "./lib/config";
import { useAuth0, AppState } from "@auth0/auth0-react";
import {
  RouterProvider,
  createRouter,
  createRoute,
  createRootRoute,
  Outlet,
  Navigate,
} from "@tanstack/react-router";
import Homepage from "./pages/HomePage";
import ProtectedLayout from "./pages/ProtectedLayout";
import TransactionsPage from "./pages/TransactionsPage";
import ExpensesPage from "./pages/ExpensesPage";
import BudgetPage from "./pages/BudgetPage";
import HistoryPage from "./pages/HistoryPage";
import Loading from "./components/ui/loading";
import "./index.css";
import NotFound from "./components/NotFound";
import Error from "./components/Error";

const Auth0ProviderWithRedirectCallback = ({
  children,
  ...props
}: React.ComponentProps<typeof Auth0Provider>) => {
  const onRedirectCallback = (appState?: AppState) => {
    window.history.pushState(
      {},
      document.title,
      appState?.targetUrl || window.location.pathname
    );
  };
  return (
    <Auth0Provider onRedirectCallback={onRedirectCallback} {...props}>
      {children}
    </Auth0Provider>
  );
};

const config = getConfig();

const providerConfig = {
  domain: config.domain,
  clientId: config.clientId,
  authorizationParams: {
    redirect_uri: config.redirectUri,
    audience: config.audience,
  },
};

// Create a QueryClient instance
const queryClient = new QueryClient();

// --- Define our routes ---

// The root route simply renders an Outlet.
const rootRoute = createRootRoute({
  component: () => <Outlet />,
  notFoundComponent: NotFound,
  errorComponent: Error,
});

// public route, home if unauth, app if auth
const publicRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  // check auth
  component: function PublicRoute() {
    const { isAuthenticated, isLoading, error } = useAuth0();

    // If loading, show loading
    if (isLoading) return <Loading />;

    // If error, show error
    if (error) return <div>Error: {error.message}</div>;

    // If authenticated, redirect to /app
    if (isAuthenticated) return <Navigate to="/app/transactions" />;

    // If not authenticated, show homepage
    return <Homepage />;
  },
});

// Public homepage route
const publicHomeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/Home",
  component: Homepage,
});

// Protected layout route (all protected pages will be nested under "/app")
const protectedLayoutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/app",
  component: ProtectedLayout,
  // This route will only be rendered if the user is authenticated
  notFoundComponent: NotFound,
  errorComponent: Error,
});

// Protected child routes
const transactionsRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: "/transactions",
  component: () => (
    <div className="p-2 overflow-y-auto">
      <TransactionsPage />
    </div>
  ),
});

const expensesRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: "/expenses",
  component: () => (
    <div className="p-2 overflow-y-auto">
      <ExpensesPage />
    </div>
  ),
});

const budgetRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: "/budget",
  component: () => (
    <div className="p-2 overflow-y-auto">
      <BudgetPage />
    </div>
  ),
});

const historyRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: "/history",
  component: () => (
    <div className="p-2 overflow-y-auto">
      <HistoryPage />
    </div>
  ),
});

const LoginRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: "/login",
  component: function Login() {
    const { loginWithRedirect } = useAuth0();
    React.useEffect(() => {
      loginWithRedirect();
    }, [loginWithRedirect]);
    return <Loading />;
  },
});

// Logout route (also under /app)
const logoutRoute = createRoute({
  getParentRoute: () => protectedLayoutRoute,
  path: "/logout",
  component: function Logout() {
    const { logout } = useAuth0();
    React.useEffect(() => {
      logout({ logoutParams: { returnTo: window.location.origin } });
    }, [logout]);
    return <Loading />;
  },
});

// Build the route tree
const routeTree = rootRoute.addChildren([
  publicHomeRoute,
  protectedLayoutRoute.addChildren([
    publicRoute,
    transactionsRoute,
    expensesRoute,
    budgetRoute,
    historyRoute,
    LoginRoute,
    logoutRoute,
  ]),
]);

const router = createRouter({ routeTree });

// --- App Component ---
function App() {
  return (
    <StrictMode>
      <Auth0ProviderWithRedirectCallback {...providerConfig}>
        <QueryClientProvider client={queryClient}>
          <div className="App h-screen max-w-6xl mx-auto flex flex-col overflow-hidden">
            <RouterProvider router={router} />
          </div>
        </QueryClientProvider>
      </Auth0ProviderWithRedirectCallback>
    </StrictMode>
  );
}

export default App;
