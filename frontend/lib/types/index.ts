// ── Enums (matching backend Python enums) ──

export enum VentureStage {
  IDEATION = "ideation",
  PRE_SEED = "pre_seed",
  SEED = "seed",
  SERIES_A = "series_a",
  SERIES_B = "series_b",
  GROWTH = "growth",
  EXIT = "exit",
}

export enum DocumentType {
  PITCH_DECK = "pitch_deck",
  FINANCIAL_MODEL = "financial_model",
  BUSINESS_PLAN = "business_plan",
  PRODUCT_DOC = "product_doc",
  OTHER = "other",
}

export enum DocumentStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  INDEXED = "indexed",
  FAILED = "failed",
}

export enum ArtifactType {
  LEAN_CANVAS = "lean_canvas",
  RESEARCH_BRIEF = "research_brief",
  PITCH_NARRATIVE = "pitch_narrative",
  DECK_OUTLINE = "deck_outline",
  FINANCIAL_MODEL = "financial_model",
  VALUATION_MEMO = "valuation_memo",
  DATAROOM_STRUCTURE = "dataroom_structure",
  KPI_DASHBOARD = "kpi_dashboard",
  BOARD_MEMO = "board_memo",
  CUSTOM = "custom",
}

export enum ArtifactStatus {
  DRAFT = "draft",
  IN_PROGRESS = "in_progress",
  READY = "ready",
  ARCHIVED = "archived",
}

export enum KGEntityType {
  VENTURE = "venture",
  MARKET = "market",
  ICP = "icp",
  COMPETITOR = "competitor",
  PRODUCT = "product",
  TEAM_MEMBER = "team_member",
  METRIC = "metric",
  FUNDING_ASSUMPTION = "funding_assumption",
  RISK = "risk",
}

export enum KGEntityStatus {
  CONFIRMED = "confirmed",
  NEEDS_REVIEW = "needs_review",
  SUGGESTED = "suggested",
  PINNED = "pinned",
}

export enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
}

export enum ModelProfile {
  REASONING_HEAVY = "reasoning_heavy",
  WRITING_POLISH = "writing_polish",
  TOOL_USING = "tool_using",
  FAST_RESPONSE = "fast_response",
  DEFAULT = "default",
}

export enum WorkspaceRole {
  OWNER = "owner",
  ADMIN = "admin",
  MEMBER = "member",
}

// ── Auth ──

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  is_active: boolean;
}

// ── Workspace & Venture ──

export interface Venture {
  id: string;
  name: string;
  stage: VentureStage;
  one_liner: string | null;
  problem: string | null;
  solution: string | null;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  role: WorkspaceRole;
  venture: Venture | null;
  created_at: string;
}

// ── Documents ──

export interface Document {
  id: string;
  name: string;
  type: DocumentType;
  status: DocumentStatus;
  mime_type: string;
  size: number;
  created_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

// ── Chat ──

export interface RoutingPlan {
  selected_agent: string;
  model_profile: ModelProfile;
  tools: string[];
  artifact_needed: boolean;
  fallback_agent: string;
  confidence: number;
  reasoning: string;
  latency_ms: number;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  agent_id: string | null;
  citations: Record<string, unknown>[] | null;
  artifact_id: string | null;
  created_at: string;
}

export interface SendMessageRequest {
  workspace_id: string;
  content: string;
  session_id?: string | null;
  override_agent?: string | null;
}

export interface SendMessageResponse {
  session_id: string;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  routing_plan: RoutingPlan;
  proposed_updates: Record<string, unknown>[];
  artifact_id: string | null;
}

export interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface ChatSessionListResponse {
  sessions: ChatSession[];
}

// ── Artifacts ──

export interface Artifact {
  id: string;
  type: ArtifactType;
  title: string;
  status: ArtifactStatus;
  owner_agent: string;
  content: Record<string, unknown>;
  current_version: number;
  assumptions: Record<string, unknown>[] | null;
  created_at: string;
  updated_at: string;
}

export interface ArtifactVersion {
  id: string;
  version: number;
  content: Record<string, unknown>;
  diff: Record<string, unknown> | null;
  created_by: string | null;
  created_at: string;
}

export interface ArtifactCreateRequest {
  workspace_id: string;
  type: ArtifactType;
  title: string;
  content?: Record<string, unknown> | null;
}

export interface ArtifactUpdateRequest {
  title?: string | null;
  status?: ArtifactStatus | null;
  content?: Record<string, unknown> | null;
  expected_version: number;
}

export interface ArtifactListResponse {
  artifacts: Artifact[];
}

export interface ArtifactVersionListResponse {
  versions: ArtifactVersion[];
}

export interface ExportTaskResponse {
  task_id: string;
  status: string;
  download_url: string | null;
}

// ── Brain / Knowledge Graph ──

export interface ChunkResult {
  chunk_id: string;
  document_id: string;
  content: string;
  similarity: number;
  freshness_weight: number;
  final_score: number;
}

export interface EntityResult {
  id: string;
  type: KGEntityType;
  status: KGEntityStatus;
  data: Record<string, unknown>;
  confidence: number;
  evidence_count: number;
}

export interface BrainSearchRequest {
  workspace_id: string;
  query: string;
  entity_types?: KGEntityType[] | null;
  max_chunks?: number;
}

export interface BrainSearchResponse {
  chunks: ChunkResult[];
  entities: EntityResult[];
  citations: Record<string, unknown>[];
}

export interface EntityCreateRequest {
  venture_id: string;
  type: KGEntityType;
  data: Record<string, unknown>;
  confidence?: number;
}

export interface EntityUpdateRequest {
  data?: Record<string, unknown> | null;
  status?: KGEntityStatus | null;
  confidence?: number | null;
}

export interface VentureProfile {
  venture: Venture;
  entities_by_type: Record<string, EntityResult[]>;
  total_documents: number;
  total_entities: number;
}

// ── SSE Streaming ──

export interface SSERoutingEvent {
  selected_agent: string;
  model_profile: ModelProfile;
  tools: string[];
  artifact_needed: boolean;
  fallback_agent: string;
  confidence: number;
  reasoning: string;
  latency_ms: number;
}

export interface SSEDoneEvent {
  message_id: string;
  citations: Record<string, unknown>[];
  proposed_updates: Record<string, unknown>[];
  artifact_id: string | null;
}

export interface SSEToolCallEvent {
  tool: string;
}

export interface SSEToolResultEvent {
  tool: string;
}

// ── Tool Types ──

export interface ValuationRequest {
  revenue?: number | null;
  growth_rate?: number | null;
  industry?: string | null;
  stage?: string | null;
  discount_rate?: number | null;
  projection_years?: number | null;
  comparable_exits?: number[] | null;
}

export interface ValuationMethodResult {
  method: string;
  low: number;
  mid: number;
  high: number;
  assumptions: string[];
}

export interface ValuationResult {
  methods: ValuationMethodResult[];
  summary: { low: number; mid: number; high: number };
  warnings: string[];
}

export interface ReadinessDimension {
  name: string;
  score: number;
  max_score: number;
  checks_passed: string[];
  checks_failed: string[];
}

export interface InvestorReadinessScore {
  overall_score: number;
  grade: string;
  dimensions: ReadinessDimension[];
  gaps: string[];
  recommendations: string[];
  summary: string;
}

export interface RoundInput {
  raise_amount: number;
  pre_money: number;
  option_pool_pct?: number;
}

export interface FundingScenario {
  round_label: string;
  raise_amount: number;
  pre_money: number;
  post_money: number;
  dilution_pct: number;
  founder_ownership_pct: number;
}

export interface ExitScenario {
  exit_multiple: number;
  exit_valuation: number;
  founder_proceeds: number;
}

export interface ScenarioModelResult {
  rounds: FundingScenario[];
  exit_scenarios: ExitScenario[];
}

export interface ScenarioRequest {
  rounds: RoundInput[];
  exit_multiples?: number[];
}

export interface BenchmarkMetric {
  name: string;
  value: number;
  p25: number;
  median: number;
  p75: number;
  percentile: number;
  classification: string;
}

export interface BenchmarkResult {
  industry: string;
  stage: string;
  cohort_size: number;
  metrics: BenchmarkMetric[];
  strengths: string[];
  weaknesses: string[];
}

export interface BenchmarkRequest {
  industry: string;
  stage: string;
  metrics: Record<string, number>;
}

export interface SuccessStoryMatch {
  name: string;
  industry: string;
  similarity_score: number;
  parallels: string[];
  differences: string[];
  peak_valuation: string;
}

export interface SuccessStoryResult {
  matches: SuccessStoryMatch[];
  query_attributes: Record<string, string>;
}

export interface SuccessStoryRequest {
  industry: string;
  stage?: string;
  business_model?: string;
  attributes?: string[];
}

// ── Venture Update ──

export interface VentureUpdateRequest {
  name?: string | null;
  stage?: VentureStage | null;
  one_liner?: string | null;
  problem?: string | null;
  solution?: string | null;
}
