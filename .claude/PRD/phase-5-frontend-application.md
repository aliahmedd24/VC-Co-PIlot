# Phase 5: Frontend Application

> **Timeline:** Weeks 14–16  
> **Priority:** High — user-facing interface  
> **Depends on:** Phases 1–4 (all backend APIs)  
> **Claude Code Tag:** `phase-5`

---

## Objective

Build the complete Next.js 14 frontend application providing the user interface for authentication, workspace management, the main chat experience with agent routing visibility, artifact workspace with versioning, venture profile dashboard, document management, and onboarding flow. The frontend must be fully responsive (mobile-first) and integrate with all backend APIs via React Query for data fetching and Zustand for client-side state.

---

## Tech Stack

| Layer | Tool | Version / Notes |
|-------|------|-----------------|
| Framework | Next.js 14 | App Router, server/client components |
| Language | TypeScript 5.x | Strict mode |
| Styling | Tailwind CSS 3.x | — |
| Components | shadcn/ui | Radix-based accessible components |
| State — Server | React Query (TanStack Query) | Cache, refetch, optimistic updates |
| State — Client | Zustand | Auth, active workspace, UI state |
| Rich Text Editor | TipTap | For artifact prose editing |
| Code/JSON Viewer | Monaco Editor | For structured artifact content |
| Charts | Recharts | KPI dashboards, financial models |
| HTTP Client | Axios | Configured with auth interceptor |
| Form Validation | React Hook Form + Zod | — |
| Package Manager | pnpm | — |

---

## User Flow

### 1. Authentication
1. User visits `/login` → enters email + password → POST `/auth/login` → receives JWT → stored in Zustand + `localStorage`.
2. New user visits `/register` → fills form → POST `/auth/register` → auto-login → redirect to onboarding.
3. Auth interceptor on Axios adds `Authorization: Bearer <token>` to all requests. On 401, redirect to `/login`.

### 2. Onboarding (First-Time User)
1. After registration, user lands on `/onboarding` — a 3-step wizard:
   - **Step 1:** Create workspace (name).
   - **Step 2:** Set up venture (name, stage, one-liner).
   - **Step 3:** Upload first document (optional, skip allowed).
2. On completion, redirect to `/chat`.

### 3. Main Chat Interface (`/chat`)
1. Left sidebar: list of chat sessions (recent first), "New Chat" button, workspace selector.
2. Main area: message thread with user/assistant messages.
3. Each assistant message shows:
   - Agent badge (icon + name, e.g., "🧭 Venture Architect").
   - Confidence indicator (green/yellow/red dot based on routing confidence).
   - Expandable "Routing Details" showing intent, confidence, latency.
   - Inline citations as clickable references.
   - If an artifact was created/updated, an artifact card with link.
4. Message input at the bottom with:
   - Text area (supports Shift+Enter for newline, Enter to send).
   - Agent selector dropdown for manual override (`@agent` shortcut).
   - File attachment button (triggers document upload flow).
5. Typing indicator while waiting for agent response.

### 4. Artifact Workspace (`/artifacts`)
1. Grid/list view of all artifacts in current workspace.
2. Filter by type, status. Sort by updated date.
3. Click an artifact → opens artifact detail view:
   - Left panel: rendered artifact content (type-specific rendering).
   - Right panel: artifact chat for refinements.
   - Top bar: version selector dropdown, export buttons (MD, PDF), status badge.
4. Version comparison: select two versions → side-by-side diff view with highlighted changes.

### 5. Venture Profile (`/profile`)
1. Overview section: venture name, stage, one-liner, problem, solution (editable inline).
2. Knowledge Graph section: entities grouped by type in expandable cards.
   - Each entity shows: data, confidence badge, status pill, evidence count.
   - User can confirm, pin, or delete entities.
3. Documents section: list of uploaded documents with status indicators.
4. Metrics overview: key metrics pulled from KG entities of type METRIC.

### 6. Settings (`/settings`)
1. Workspace settings: name, slug, member management.
2. User profile: name, email, password change.
3. API keys display (masked).

---

## Technical Constraints

- **Mobile responsive:** All pages must work on 375px width minimum. Use Tailwind responsive prefixes (`sm:`, `md:`, `lg:`).
- **Dark mode support** is NOT required for V1 (light mode only).
- **No SSR for authenticated pages** — use client components with React Query for data fetching. Only the landing/login pages are server-rendered.
- **Optimistic updates** for: entity status changes, artifact status changes, sending messages (show user message immediately).
- **Streaming responses:** V1 does NOT implement SSE/WebSocket streaming for agent responses. The UI shows a loading state until the full response returns. (Streaming deferred to Phase 6.)
- **JWT stored in `localStorage`** (acceptable for V1; httpOnly cookie upgrade in Phase 6).
- **All API calls go through a centralized `api` module** with typed request/response interfaces matching backend Pydantic schemas.
- **Error handling:** Global error boundary. Toast notifications for API errors. Inline validation for forms.
- **File upload:** Max 50MB, drag-and-drop support, progress indicator.
- **Page load performance:** LCP < 2.5s on 3G (measured via Lighthouse).

---

## Data Schema (TypeScript Interfaces)

```typescript
// Auth
interface User {
  id: string;
  email: string;
  name: string | null;
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

// Workspace
interface Workspace {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

interface Venture {
  id: string;
  workspace_id: string;
  name: string;
  stage: VentureStage;
  one_liner: string | null;
  problem: string | null;
  solution: string | null;
}

type VentureStage = "ideation" | "pre_seed" | "seed" | "series_a" | "series_b" | "growth" | "exit";

// Chat
interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  agent_id: string | null;
  routing_plan: RoutingPlan | null;
  citations: Citation[] | null;
  artifact_id: string | null;
  created_at: string;
}

interface RoutingPlan {
  selected_agent: string;
  model_profile: string;
  tools: string[];
  artifact_needed: boolean;
  confidence: number;
  reasoning: string;
  latency_ms: number;
}

interface Citation {
  chunk_id: string;
  document_id: string;
  snippet: string;
}

// Artifacts
interface Artifact {
  id: string;
  type: ArtifactType;
  title: string;
  status: ArtifactStatus;
  owner_agent: string;
  content: Record<string, any>;
  current_version: number;
  assumptions: Record<string, any>[] | null;
  created_at: string;
  updated_at: string;
}

type ArtifactType = "lean_canvas" | "research_brief" | "pitch_narrative" | "deck_outline" | "financial_model" | "valuation_memo" | "dataroom_structure" | "kpi_dashboard" | "board_memo" | "custom";
type ArtifactStatus = "draft" | "in_progress" | "ready" | "archived";

interface ArtifactVersion {
  id: string;
  version: number;
  content: Record<string, any>;
  diff: Record<string, any> | null;
  created_by: string | null;
  created_at: string;
}

// Brain / KG
interface KGEntity {
  id: string;
  type: string;
  status: "confirmed" | "needs_review" | "suggested" | "pinned";
  data: Record<string, any>;
  confidence: number;
  evidence_count: number;
}

interface VentureProfile {
  venture: Venture;
  entities_by_type: Record<string, KGEntity[]>;
  total_documents: number;
  total_entities: number;
}

// Documents
interface Document {
  id: string;
  name: string;
  type: string;
  status: "pending" | "processing" | "indexed" | "failed";
  size: number;
  created_at: string;
}
```

---

## Key Files to Create

```
frontend/
├── app/
│   ├── layout.tsx                      # Root layout, providers (QueryClient, Zustand)
│   ├── page.tsx                        # Landing / redirect to /chat
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx                  # Dashboard layout: sidebar + header
│   │   ├── chat/
│   │   │   └── page.tsx                # Main chat interface
│   │   ├── artifacts/
│   │   │   ├── page.tsx                # Artifact list
│   │   │   └── [id]/page.tsx           # Artifact detail + chat
│   │   ├── profile/
│   │   │   └── page.tsx                # Venture profile + KG viewer
│   │   ├── documents/
│   │   │   └── page.tsx                # Document management
│   │   ├── settings/
│   │   │   └── page.tsx                # Workspace + user settings
│   │   └── onboarding/
│   │       └── page.tsx                # 3-step onboarding wizard
│   └── globals.css                     # Tailwind base styles
│
├── components/
│   ├── ui/                             # shadcn/ui components (button, card, dialog, etc.)
│   ├── chat/
│   │   ├── ChatSidebar.tsx             # Session list
│   │   ├── MessageThread.tsx           # Message display
│   │   ├── MessageBubble.tsx           # Single message with agent badge
│   │   ├── RoutingDetails.tsx          # Expandable routing info
│   │   ├── CitationLink.tsx            # Clickable citation
│   │   ├── ArtifactCard.tsx            # Inline artifact reference
│   │   ├── MessageInput.tsx            # Text area + controls
│   │   └── AgentSelector.tsx           # Override dropdown
│   ├── artifacts/
│   │   ├── ArtifactGrid.tsx            # Grid/list view
│   │   ├── ArtifactDetail.tsx          # Full artifact view
│   │   ├── ArtifactRenderer.tsx        # Type-specific content rendering
│   │   ├── LeanCanvasRenderer.tsx      # 9-block canvas visual
│   │   ├── DeckOutlineRenderer.tsx     # Slide list
│   │   ├── FinancialModelRenderer.tsx  # Tables + charts
│   │   ├── KPIDashboardRenderer.tsx    # Metric cards + trend charts
│   │   ├── VersionSelector.tsx         # Version dropdown
│   │   └── VersionDiff.tsx             # Side-by-side diff view
│   ├── profile/
│   │   ├── VentureHeader.tsx           # Editable venture info
│   │   ├── EntityTypeSection.tsx       # Collapsible entity group
│   │   ├── EntityCard.tsx              # Single entity with actions
│   │   └── MetricsOverview.tsx         # Key metrics summary
│   ├── documents/
│   │   ├── DocumentList.tsx
│   │   ├── UploadDropzone.tsx          # Drag-and-drop upload
│   │   └── DocumentStatusBadge.tsx
│   ├── layout/
│   │   ├── DashboardSidebar.tsx        # Main navigation
│   │   ├── Header.tsx                  # Workspace selector + user menu
│   │   └── MobileNav.tsx               # Hamburger menu for mobile
│   └── onboarding/
│       ├── StepWorkspace.tsx
│       ├── StepVenture.tsx
│       └── StepDocument.tsx
│
├── lib/
│   ├── api/
│   │   ├── client.ts                   # Axios instance with interceptor
│   │   ├── auth.ts                     # login, register, me
│   │   ├── workspaces.ts              # workspace CRUD
│   │   ├── chat.ts                     # sendMessage, getSessions
│   │   ├── artifacts.ts               # CRUD + chat + export
│   │   ├── brain.ts                    # search, profile, entities
│   │   └── documents.ts               # upload, list
│   ├── hooks/
│   │   ├── useAuth.ts                  # Auth state hook
│   │   ├── useWorkspace.ts             # Active workspace hook
│   │   ├── useChat.ts                  # Chat queries + mutations
│   │   ├── useArtifacts.ts            # Artifact queries + mutations
│   │   └── useBrain.ts                # Brain queries
│   ├── stores/
│   │   ├── authStore.ts                # Zustand auth store
│   │   └── uiStore.ts                  # Sidebar open, active tab, etc.
│   ├── utils/
│   │   ├── formatters.ts              # Date, number formatters
│   │   ├── agentMeta.ts               # Agent name, icon, color mapping
│   │   └── confidenceColor.ts         # Confidence → color utility
│   └── types/
│       └── index.ts                    # All TypeScript interfaces
│
├── public/
│   └── agents/                         # Agent avatar icons
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── Dockerfile
└── .env.local.example
```

---

## Definition of Done

### Automated Tests (Jest + React Testing Library)

1. **Auth Flow Tests**
   - `test_login_form_submission` → Submits credentials, stores token, redirects.
   - `test_login_invalid_credentials` → Shows error toast.
   - `test_register_form_validation` → Email format and password length enforced.
   - `test_logout` → Clears token, redirects to `/login`.
   - `test_auth_redirect` → Unauthenticated user accessing `/chat` redirected to `/login`.

2. **Chat Interface Tests**
   - `test_send_message` → Message appears in thread immediately (optimistic). Agent response appears after API returns.
   - `test_agent_badge_displayed` → Assistant messages show correct agent name and icon.
   - `test_routing_details_expandable` → Click "Routing Details" shows intent, confidence, latency.
   - `test_citation_links` → Citations render as clickable links.
   - `test_new_chat_creates_session` → "New Chat" button calls API and adds session to sidebar.
   - `test_session_list_sorted` → Sessions ordered by most recent first.

3. **Artifact UI Tests**
   - `test_artifact_grid_renders` → Grid shows artifact cards with type, title, status.
   - `test_artifact_detail_renders_content` → Lean Canvas shows 9 blocks; Deck Outline shows slides.
   - `test_version_selector` → Changing version loads the correct content.
   - `test_export_markdown` → Click "Export MD" downloads a markdown file.
   - `test_status_change` → Click status pill updates via API.

4. **Profile Tests**
   - `test_venture_info_editable` → Inline editing updates venture via API.
   - `test_entity_cards_grouped` → Entities displayed in correct type sections.
   - `test_entity_confirm_action` → "Confirm" button changes entity status.

5. **Responsive Tests**
   - `test_mobile_sidebar_hidden` → Sidebar hidden on < 768px, hamburger menu visible.
   - `test_mobile_chat_full_width` → Chat thread takes full width on mobile.
   - `test_artifact_grid_single_column_mobile` → Grid collapses to 1 column on mobile.

### Manual / CI Checks

- Lighthouse score ≥ 80 for Performance on `/chat` page.
- All pages functional at 375px, 768px, and 1440px widths.
- Full E2E flow: register → onboard → upload document → chat → view artifact → export.
- `pnpm lint` passes with zero errors.
- `pnpm build` succeeds without type errors.
- All components use shadcn/ui primitives — no raw HTML `<input>`, `<button>`, `<dialog>`.
