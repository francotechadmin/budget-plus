// pages/Homepage.tsx
import { useState, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";
import screenRecording from "/public/screen-recording.mp4";

const Homepage = () => {
  const { loginWithRedirect } = useAuth0();

  // Read the current theme from the body class (this could be improved to persist theme in a global store)
  const [isDark, setIsDark] = useState(() =>
    document.body.classList.contains("dark")
  );

  // Optionally, listen to theme changes if they're applied elsewhere
  useEffect(() => {
    setIsDark(document.body.classList.contains("dark"));
  }, []);

  const toggleTheme = () => {
    document.body.classList.toggle("dark");
    setIsDark(!isDark);
  };

  const handleLearnMore = () => {
    window.open("https://github.com/francotechadmin/budget-plus", "_blank");
  };

  return (
    <div className="min-h-screen text-gray-900 dark:text-gray-100">
      {/* Header */}
      <header className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="text-xl font-bold">Budget+</div>
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={toggleTheme}>
            {isDark ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>
          <Button variant="default" onClick={() => loginWithRedirect()}>
            Sign In
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="p-8 flex flex-col items-center">
        <div className="max-w-4xl text-center">
          <h1 className="text-4xl md:text-5xl font-extrabold mb-4">
            Welcome to Budget+
          </h1>
          <p className="text-lg md:text-xl mb-6">
            Seamlessly manage your budget with{" "}
            <span className="font-semibold">automatic categorization</span> and
            insightful visualizations.
          </p>
          <video
            className="w-full mx-auto mb-6 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700"
            controls
            autoPlay
            loop
            muted
          >
            <source src={screenRecording} type="video/mp4" />
            Your browser does not support the video tag.
          </video>

          <div className="flex flex-col md:flex-row gap-4 justify-center">
            <Button
              variant="default"
              size="lg"
              onClick={() => loginWithRedirect()}
            >
              Sign Up
            </Button>
            <Button variant="outline" size="lg" onClick={handleLearnMore}>
              Learn More
            </Button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-4 text-center text-sm">
        &copy; {new Date().getFullYear()} Budget+. All rights reserved.
      </footer>
    </div>
  );
};

export default Homepage;
