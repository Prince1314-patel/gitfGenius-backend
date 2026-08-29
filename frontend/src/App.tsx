import { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useContacts } from "@/hooks/useContacts";
import { AppLayout } from "@/components/AppLayout";
import { AuthPage } from "@/pages/AuthPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ContactDetailPage } from "@/pages/ContactDetailPage";
import { CalendarPage } from "@/pages/CalendarPage";
import { SettingsPage } from "@/pages/SettingsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function AppContent() {
  const {
    user,
    isLoading: authLoading,
    error: authError,
    fieldErrors: authFieldErrors,
    login,
    signup,
    logout,
    isAuthenticated,
  } = useAuth();

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
    getContact,
  } = useContacts();

  useEffect(() => {
    if (isAuthenticated) fetchContacts();
  }, [isAuthenticated, fetchContacts]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <AuthPage
        onLogin={login}
        onSignup={signup}
        isLoading={authLoading}
        error={authError}
        fieldErrors={authFieldErrors}
      />
    );
  }

  return (
    <AppLayout onLogout={logout}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={
            <DashboardPage
              contacts={contacts}
              isLoading={contactsLoading}
              userName={user?.name || 'there'}
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
              onAddMemory={addMemory}
              contactsLoading={contactsLoading}
            />
          }
        />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route
          path="/settings"
          element={
            <SettingsPage
              userName={user?.name || 'User'}
              userEmail={user?.email || ''}
              onLogout={logout}
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
