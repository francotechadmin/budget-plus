"use client";
import { Share, SquarePlus } from "lucide-react";
import { useEffect, useState } from "react";

function InstallPrompt() {
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  // Track whether the prompt should be shown
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    // Check if user already dismissed this prompt in the past
    const dismissed = localStorage.getItem("installPromptDismissed");
    if (dismissed) return;

    // Check if on iOS
    setIsIOS(
      /iPad|iPhone|iPod/.test(navigator.userAgent) && !("MSStream" in window)
    );

    // Check if app is already in standalone mode
    setIsStandalone(window.matchMedia("(display-mode: standalone)").matches);

    // If not standalone (i.e., not installed), show the prompt
    setShowPrompt(true);
  }, []);

  // If app is installed or user dismissed prompt, don't render
  if (isStandalone || !showPrompt) {
    return null;
  }

  const handleDismiss = () => {
    // Mark the prompt as dismissed in localStorage, then hide
    localStorage.setItem("installPromptDismissed", "true");
    setShowPrompt(false);
  };

  if (!isIOS) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 w-72 p-4 rounded-md shadow-md bg-white text-black z-50 border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-sm">
          Install App to Home Screen for Easier Access!
        </h3>
        {/* Small 'X' button to dismiss */}
        <button
          onClick={handleDismiss}
          className="text-gray-600 hover:bg-gray-200 rounded-full p-1"
          aria-label="Close install prompt"
        >
          ✕
        </button>
      </div>
      {/* 
         For iOS, there's no direct "prompt" – we just display instructions.
         For other devices, you might handle the PWA install prompt differently.
      */}
      {isIOS ? (
        <p className="text-xs">
          <span className="inline-flex items-center gap-1">
            To install on iOS, tap the Share button
            <Share size={10} />,
          </span>
          <span className="inline-flex items-center gap-1">
            then select <strong>Add to Home Screen</strong>
            <SquarePlus size={10} />
          </span>
        </p>
      ) : (
        <button
          onClick={() => alert("Show Add to Home Screen instructions here.")}
          className="bg-red-600 text-white w-full py-1 mt-1 rounded hover:bg-red-500 text-sm"
        >
          Add to Home Screen
        </button>
      )}
    </div>
  );
}

export default InstallPrompt;
