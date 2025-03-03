// pages/ProtectedLayout.tsx
import { useEffect, useState } from "react";
import { Outlet, Link } from "@tanstack/react-router";
import { useAuth0, withAuthenticationRequired } from "@auth0/auth0-react";
import Loading from "../components/ui/loading";
import { addAccessTokenInterceptor } from "../lib/axios";
import { useUpsertUserMutation } from "../hooks/api/useUserUpsertMutation";
import { Notebook, Menu, X, Moon, LogOut } from "lucide-react";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import { Button } from "../components/ui/button";

const basePath = (import.meta.env.VITE_BASE_PATH as string) || "/";

function ProtectedLayoutComponent() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { logout, isLoading } = useAuth0();
  const {
    mutate: upsertUser,
    isPending: isUpserting,
    isError,
  } = useUpsertUserMutation();
  const [tokenAdded, setTokenAdded] = useState(false);

  const { getAccessTokenSilently } = useAuth0();

  // Add access token interceptor
  useEffect(() => {
    // add interceptor and set tokenAdded to true when done
    const addInterceptor = async () => {
      await addAccessTokenInterceptor(getAccessTokenSilently);
      setTokenAdded(true);
    };
    addInterceptor();
  }, []);

  // Upsert user on mount (only run when not loading and without error)
  useEffect(() => {
    if (tokenAdded) {
      console.log("Upserting user");
      upsertUser();
    }
  }, [tokenAdded]);

  if (isLoading || isUpserting) {
    // Show loading screen while loading
    return <Loading />;
  }

  if (isError) {
    // Show error screen if there was an error
    return <div>Error</div>;
  }

  return (
    <>
      {/* Header / Navigation */}
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
                    <Link to={`${basePath}/app/transactions`}>
                      Transactions
                    </Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    asChild
                    className={navigationMenuTriggerStyle()}
                  >
                    <Link to={`${basePath}/app/expenses`}>Expenses</Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    asChild
                    className={navigationMenuTriggerStyle()}
                  >
                    <Link to={`${basePath}/app/budget`}>Budget</Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    asChild
                    className={navigationMenuTriggerStyle()}
                  >
                    <Link to={`${basePath}/app/history`}>History</Link>
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
          <Button
            variant="outline"
            className="h-8 hidden sm:flex items-center"
            onClick={() => document.body.classList.toggle("dark")}
          >
            Toggle Mode
          </Button>
          <Button
            variant="outline"
            className="h-8 sm:hidden p-2 flex items-center justify-center"
            onClick={() => document.body.classList.toggle("dark")}
          >
            <Moon className="h-4 w-4" />
          </Button>

          {/* Logout Button */}
          <Button
            variant="outline"
            className="h-8 hidden p-2 sm:flex items-center"
            onClick={() =>
              logout({ logoutParams: { returnTo: window.location.origin } })
            }
          >
            Logout
          </Button>
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
            <NavigationMenuList>
              <NavigationMenuItem>
                <NavigationMenuLink
                  asChild
                  className={navigationMenuTriggerStyle()}
                >
                  <Link
                    to={`${basePath}/app/transactions`}
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
                    to={`${basePath}/app/expenses`}
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
                    to={`${basePath}/app/budget`}
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
                    to={`${basePath}/app/history`}
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
      {/* only show if token has been added to request */}
      {tokenAdded && <Outlet />}
    </>
  );
}

// Wrap the layout with authentication so that it only renders for signed-in users.
const ProtectedLayout = withAuthenticationRequired(ProtectedLayoutComponent, {
  onRedirecting: () => <Loading />,
});

export default ProtectedLayout;
