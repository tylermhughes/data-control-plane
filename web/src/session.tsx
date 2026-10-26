// Who's signed in (an API key, kept only for this browser tab) and which project is chosen.
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { api, setApiKey, setUnauthorizedHandler } from "./api/client";
import type { Schemas } from "./api/client";

const KEY_STORAGE = "dcp.apiKey"; // sessionStorage: gone when the tab closes
const PROJECT_STORAGE = "dcp.projectId"; // localStorage: a per-viewer convenience

function read(storage: () => Storage, name: string): string | null {
  try {
    return storage().getItem(name);
  } catch {
    return null; // private windows or blocked storage: just don't remember
  }
}

function write(storage: () => Storage, name: string, value: string | null): void {
  try {
    if (value === null) storage().removeItem(name);
    else storage().setItem(name, value);
  } catch {
    /* not remembered; that's fine */
  }
}

interface Session {
  key: string | null;
  me: Schemas["ApiKey"] | null;
  projects: Schemas["Project"][];
  projectId: string | null; // null = all projects (admin keys only)
  canWrite: boolean;
  signIn: (key: string, me: Schemas["ApiKey"]) => void;
  signOut: () => void;
  chooseProject: (id: string | null) => void;
}

const SessionContext = createContext<Session | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [key, setKey] = useState<string | null>(() => read(() => sessionStorage, KEY_STORAGE));
  const [chosen, setChosen] = useState<string | null>(() => read(() => localStorage, PROJECT_STORAGE));
  setApiKey(key);

  const signOut = useCallback(() => {
    write(() => sessionStorage, KEY_STORAGE, null);
    setApiKey(null);
    setKey(null);
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => setUnauthorizedHandler(signOut), [signOut]);

  const me = useQuery({
    queryKey: ["me", key],
    queryFn: () => api<Schemas["ApiKey"]>("/v1/me"),
    enabled: key !== null,
    staleTime: Infinity,
  });
  const projects = useQuery({
    queryKey: ["projects", key],
    queryFn: () => api<Schemas["Page_Project_"]>("/v1/projects", { query: { limit: 200 } }),
    enabled: key !== null && me.isSuccess,
  });

  const value = useMemo<Session>(() => {
    const list = projects.data?.data ?? [];
    const meData = me.data ?? null;
    // Project keys always work in their own project; admins may pick one or see all.
    const projectId = meData?.project_id ?? (list.some((p) => p.id === chosen) ? chosen : null);
    return {
      key,
      me: meData,
      projects: list,
      projectId,
      canWrite: meData?.access === "write",
      signIn: (newKey, newMe) => {
        write(() => sessionStorage, KEY_STORAGE, newKey);
        setApiKey(newKey);
        queryClient.setQueryData(["me", newKey], newMe);
        setKey(newKey);
      },
      signOut,
      chooseProject: (id) => {
        write(() => localStorage, PROJECT_STORAGE, id);
        setChosen(id);
      },
    };
  }, [key, me.data, projects.data, chosen, queryClient, signOut]);

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): Session {
  const session = useContext(SessionContext);
  if (!session) throw new Error("useSession must be used inside SessionProvider");
  return session;
}
