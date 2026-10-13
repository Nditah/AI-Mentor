import { create } from "zustand";
import { persist } from "zustand/middleware";

type StudioState = {
  devUserId: string;
  notes: string;
  labCode: string;
  setDevUserId: (id: string) => void;
  setNotes: (notes: string) => void;
  setLabCode: (code: string) => void;
};

export const useStudio = create<StudioState>()(
  persist(
    (set) => ({
      devUserId: "demo-student",
      notes: "",
      labCode: "",
      setDevUserId: (devUserId) => set({ devUserId }),
      setNotes: (notes) => set({ notes }),
      setLabCode: (labCode) => set({ labCode }),
    }),
    { name: "ai-mentor-studio" },
  ),
);
