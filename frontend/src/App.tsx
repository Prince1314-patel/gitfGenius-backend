import { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useContacts } from "@/hooks/useContacts";
import { AppLayout } from "@/components/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { ContactDetailPage } from "@/pages/ContactDetailPage";
import { CalendarPage } from "@/pages/CalendarPage";
import { DatabasePage } from "@/pages/DatabasePage";
import { SettingsPage } from "@/pages/SettingsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function AppContent() {
  const {
    contacts,
    isLoading: contactsLoading,
    fetchContacts,
    fetchMemories,
    addContact,
    updateContact,
    deleteContact,
    addMemory,
    deleteMemory,
    fetchRecommendations,
    recommendationsByContactId,
    getContact,
  } = useContacts();

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={
            <DashboardPage
              contacts={contacts}
              isLoading={contactsLoading}
              userName="there"
              onAddContact={addContact}
            />
          }
        />
        <Route
          path="/contact/:id"
          element={
            <ContactDetailPage
              getContact={getContact}
              fetchMemories={fetchMemories}
              onDeleteContact={deleteContact}
              onUpdateContact={updateContact}
              onAddMemory={addMemory}
              onDeleteMemory={deleteMemory}
              onFetchRecommendations={fetchRecommendations}
              recommendations={id => recommendationsByContactId[id] ?? []}
              contactsLoading={contactsLoading}
            />
          }
        />
        <Route path="/calendar" element={<CalendarPage contacts={contacts} />} />
        <Route path="/database" element={<DatabasePage />} />
        <Route
          path="/settings"
          element={
            <SettingsPage
              userName="User"
              userEmail=""
            />
          }
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppLayout>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
