// src/__tests__/components/Homepage.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import Homepage from "../../pages/HomePage";
import { useAuth0 } from "@auth0/auth0-react";
import { useTheme } from "../../hooks/useTheme";
import { usePingQuery } from "../../hooks/api/usePingQuery";

// Mock the hooks
jest.mock("@auth0/auth0-react", () => ({
  useAuth0: jest.fn(),
}));

jest.mock("../../hooks/useTheme", () => ({
  useTheme: jest.fn(),
}));

jest.mock("../../hooks/api/usePingQuery", () => ({
  usePingQuery: jest.fn(),
}));

// Mock video component
jest.mock("../../assets/screen-recording.mp4", () => "mocked-video-url");

describe("Homepage Component", () => {
  beforeEach(() => {
    // Setup default mocks
    (useAuth0 as jest.Mock).mockReturnValue({
      loginWithRedirect: jest.fn(),
    });

    (useTheme as jest.Mock).mockReturnValue({
      theme: "light",
      toggleTheme: jest.fn(),
    });

    (usePingQuery as jest.Mock).mockReturnValue({});
  });

  test("renders correctly", () => {
    render(<Homepage />);

    expect(screen.getByText("Welcome to Budget+")).toBeInTheDocument();
    expect(
      screen.getByText(/Seamlessly manage your budget/)
    ).toBeInTheDocument();
    expect(screen.getByText("Sign Up")).toBeInTheDocument();
    expect(screen.getByText("Learn More")).toBeInTheDocument();
  });

  test("calls loginWithRedirect when Sign In button is clicked", () => {
    const loginWithRedirect = jest.fn();
    (useAuth0 as jest.Mock).mockReturnValue({
      loginWithRedirect,
    });

    render(<Homepage />);

    fireEvent.click(screen.getByText("Sign In"));
    expect(loginWithRedirect).toHaveBeenCalledTimes(1);
  });

  test("toggles theme when theme button is clicked", () => {
    const toggleTheme = jest.fn();
    (useTheme as jest.Mock).mockReturnValue({
      theme: "light",
      toggleTheme,
    });

    render(<Homepage />);

    // Find button by its role and click it
    const themeButton = screen.getByRole("button", { name: "" }); // The button has no text, only an icon
    fireEvent.click(themeButton);

    expect(toggleTheme).toHaveBeenCalledTimes(1);
  });

  test("displays dark mode icon when in light mode", () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: "light",
      toggleTheme: jest.fn(),
    });

    render(<Homepage />);

    // There should be a Moon icon when in light mode
    expect(
      document.querySelector('[class*="lucide-moon"]')
    ).toBeInTheDocument();
  });

  test("displays light mode icon when in dark mode", () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: "dark",
      toggleTheme: jest.fn(),
    });

    render(<Homepage />);

    // There should be a Sun icon when in dark mode
    expect(document.querySelector('[class*="lucide-sun"]')).toBeInTheDocument();
  });
});
