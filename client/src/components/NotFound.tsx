// NotFound.tsx

import { Link } from "@tanstack/react-router";

function NotFound() {
  return (
    <div className="w-1/2 mx-auto p-4">
      <h1 className="text-4xl font-bold">404 - Page Not Found</h1>
      <br />
      <div className="flex flex-col items-center">
        <p className="text-lg">The page you are looking for does not exist.</p>
        <Link to="/" className="text-blue-500 hover:underline">
          Go back
        </Link>
      </div>
    </div>
  );
}

export default NotFound;
