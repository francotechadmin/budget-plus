// Error.tsx

import { Link } from "@tanstack/react-router";

interface Error {
  message: string;
}

interface ErrorProps {
  error?: Error;
}

function Error({ error }: ErrorProps) {
  return (
    <div className="w-1/2 mx-auto p-4">
      <h1 className="text-4xl font-bold">Error</h1>
      <br />
      <div className="flex flex-col items-center">
        <p className="text-lg">
          {error?.message || "An unexpected error occurred."}
        </p>
        <Link to="/" className="text-blue-500 hover:underline">
          Go back
        </Link>
      </div>
    </div>
  );
}

export default Error;
