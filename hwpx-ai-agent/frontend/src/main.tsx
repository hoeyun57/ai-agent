import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { Bot, FileClock, FileSearch, History, Settings, Upload } from "lucide-react";
import { App } from "./pages/App";
import "./styles.css";

const queryClient = new QueryClient();

const nav = [
  { to: "/", label: "업로드", icon: Upload },
  { to: "/documents", label: "문서", icon: FileSearch },
  { to: "/agent", label: "AI 작업", icon: Bot },
  { to: "/plans", label: "승인", icon: FileClock },
  { to: "/history", label: "이력", icon: History },
  { to: "/settings", label: "설정", icon: Settings }
];

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="shell">
          <aside className="sidebar">
            <h1>HWPX AI Agent</h1>
            <nav>
              {nav.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink key={item.to} to={item.to}>
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </aside>
          <main>
            <Routes>
              <Route path="/*" element={<App />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);

