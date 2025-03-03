// pages/Homepage.tsx
import { useAuth0 } from "@auth0/auth0-react";
import { Button } from "@/components/ui/button";

const Homepage = () => {
  const { loginWithRedirect } = useAuth0();

  return (
    <div className="p-4">
      <h1>Welcome to Budget+</h1>
      <p>This is the public homepage.</p>

      <Button
        variant="default"
        size="lg"
        className="mt-4"
        onClick={() => loginWithRedirect()}
      >
        Login
      </Button>
      <p className="mt-4">
        This is a simple application that allows you to manage your budget.
      </p>
    </div>
  );
};

export default Homepage;
