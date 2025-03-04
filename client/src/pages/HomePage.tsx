// pages/Homepage.tsx
import { useAuth0 } from "@auth0/auth0-react";
import { Button } from "@/components/ui/button";
import { BookOpenText, LogIn, Moon, Notebook, Sun } from "lucide-react";
import screenRecording from "@/assets/screen-recording.mp4";
import { useTheme } from "@/hooks/useTheme";
import { usePingQuery } from "../hooks/api/usePingQuery";

const Homepage = () => {
  const { loginWithRedirect } = useAuth0();

  const { theme, toggleTheme } = useTheme();

  const handleLearnMore = () => {
    window.open("https://github.com/francotechadmin/budget-plus", "_blank");
  };

  // ping the API
  usePingQuery();

  return (
    <div className="min-h-screen text-gray-900 dark:text-gray-100">
      {/* Header */}
      <header className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="text-xl font-bold flex items-center">
          <Notebook className="inline-block mr-1 h-5 w-5" />
          Budget+
        </div>
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={toggleTheme}>
            {theme == "dark" ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>
          <Button variant="default" onClick={() => loginWithRedirect()}>
            Sign In
            <LogIn className="ml-1 h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="p-8 flex flex-col items-center">
        <div className="max-w-4xl text-center">
          <h1 className="text-3xl lg:text-4xl md:text-5xl font-extrabold mb-4">
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
            playsInline
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
              <LogIn className="ml-1 h-4 w-4" />
            </Button>
            <Button variant="outline" size="lg" onClick={handleLearnMore}>
              Learn More
              <BookOpenText className="ml-1 h-4 w-4" />
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
