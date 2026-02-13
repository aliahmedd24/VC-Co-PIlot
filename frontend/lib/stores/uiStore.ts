import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  activeWorkspaceId: string | null;
  activeSessionId: string | null;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveWorkspace: (id: string | null) => void;
  setActiveSession: (id: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activeWorkspaceId: null,
  activeSessionId: null,

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
  setActiveWorkspace: (id: string | null) =>
    set({ activeWorkspaceId: id }),
  setActiveSession: (id: string | null) =>
    set({ activeSessionId: id }),
}));
