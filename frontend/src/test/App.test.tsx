import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import { AuthProvider } from "../auth";

const user = { id: "u1", email: "student@example.com", display_name: "Student", created_at: "2026-01-01T00:00:00Z" };
function json(data: unknown, status = 200) { return Promise.resolve(new Response(status === 204 ? null : JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } })); }
function mount(path: string) { return render(<MemoryRouter initialEntries={[path]}><AuthProvider><App /></AuthProvider></MemoryRouter>); }

beforeEach(() => { document.cookie = "mindmesh_csrf=test"; vi.restoreAllMocks(); });

it("restores a session and renders overview metrics", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => String(input).endsWith("/api/auth/me") ? json(user) : json({ total: 3, normal: 2, flagged: 1, model_version: "1.0.0", recent: [] }));
  mount("/"); expect(await screen.findByText("Know where to look next.")).toBeInTheDocument(); expect(await screen.findByText("3")).toBeInTheDocument();
});

it("submits a validated prediction and presents probability as probability", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => String(input).endsWith("/api/auth/me") ? json(user) : json({ id: "p1", probability: .22, predicted_failure: false, result: "Normal Operation", risk_level: "low", recommendation: "Continue routine monitoring.", model_version: "1.0.0", created_at: "2026-01-01T00:00:00Z", inputs: {} }));
  mount("/prediction"); await screen.findByText("New prediction"); await userEvent.click(screen.getByRole("button", { name: "Analyse machine" })); expect(await screen.findByText("22.0%")).toBeInTheDocument(); expect(screen.getByText(/Probability is not certainty/)).toBeInTheDocument();
});

it("shows server validation errors without losing the form", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => String(input).endsWith("/api/auth/me") ? json(user) : json({ detail: "Readings outside accepted range" }, 422));
  mount("/prediction"); await screen.findByText("New prediction"); await userEvent.click(screen.getByRole("button", { name: "Analyse machine" })); expect(await screen.findByRole("alert")).toHaveTextContent("Readings outside accepted range");
});

it("renders the static-help disclosure", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => String(input).endsWith("/api/auth/me") ? json(user) : String(input).includes("/api/predictions") ? json({ items: [] }) : String(input).endsWith("/api/conversations") && init?.method === "POST" ? json({ reply: "Static help", mode: "static" }) : json([]));
  mount("/ask"); await screen.findByRole("heading", { name: "Ask MindMesh" }); await userEvent.type(screen.getByLabelText("Question"), "What is recall?"); await userEvent.click(screen.getByRole("button", { name: "Send question" })); expect(await screen.findByText(/Static help mode/)).toBeInTheDocument();
});

it("redirects an unauthenticated visitor to login", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => json({ detail: "Authentication required" }, 401));
  mount("/history"); await waitFor(() => expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument());
});

