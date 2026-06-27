"use client";
import Sidebar from "@/components/dashboard/Sidebar";
import { allowedRoles, sidebarItems } from "@/constants";
import ProtectedRoute from "@/protectedRoute/ProtectedRoute";
import { RootState } from "@/redux/store";
import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";

const Dashboard = () => {
  const user = useSelector((state: RootState) => state.auth.user);
  useState<React.ComponentType | null>(null);
  const [activeComponent, setActiveComponent] = useState<React.ReactNode>(null);

  useEffect(() => {
    if (!activeComponent && user?.role) {
      const DefaultComponent = sidebarItems[user.role]?.[0]?.component; // Get the first component
      if (DefaultComponent) {
        setActiveComponent(<DefaultComponent />); // Instantiate it as a JSX element
      }
    }
  }, [user, activeComponent]);
  return (
    <ProtectedRoute allowedRoles={allowedRoles}>
      <div className="flex  min-h-screen">
        <div className="flex-0">
          <Sidebar setActiveComponent={setActiveComponent} />
        </div>
        <div className="flex-1 w-full">
          {activeComponent || (
            <h1 className="text-center text-gray-500">
              Select an option from the menu
            </h1>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
};

export default Dashboard;
