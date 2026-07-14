"use client";
import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import CustomButton from "@/components/shared/CustomButton";
import Heading from "@/components/shared/CustomHeading";
import { DataTable } from "@/components/shared/DataTable";
import { AdminUserTableColumns } from "@/components/shared/tableColumnDef/AdminUserTableColumns";
import { useToast } from "@/hooks/use-toast";
import {
  useDeleteUserMutation,
  useGetAdminUsersQuery,
  useUpdateUserMutation,
} from "@/redux/api/adminApi";
import { MonitorPause, Trash } from "lucide-react";
import React, { useState } from "react";

const User = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const { data } = useGetAdminUsersQuery({ page, limit });
  const [updateUser] = useUpdateUserMutation();
  const [deleteUser] = useDeleteUserMutation();
  const { toast } = useToast();

  const totalPages = Math.ceil((data?.meta?.total || 0) / limit);

  const handlePreviousPage = () => {
    if (page > 1) setPage((prev) => prev - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage((prev) => prev + 1);
  };

  const handleSuspendUser = async (userId: string) => {
    try {
      await updateUser({
        id: userId,
        data: { isSuspended: true },
      }).unwrap();

      toast({
        description: "User suspended successfully:",
      });

      // console.log("User suspended successfully:", updatedUser);
    } catch (error) {
      console.error("Error suspending user:", error);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    try {
      await deleteUser(userId).unwrap();
      toast({
        description: "User deleted successfully:",
      });
    } catch (error) {
      console.error("Error deleting user:", error);
    }
  };

  const columns = AdminUserTableColumns.map((col) =>
    col.id === "actions"
      ? {
          ...col,
          cell: ({ row }: any) => (
            <div className="flex justify-center items-center gap-2">
              <CustomButton
                icon={<MonitorPause />}
                onClick={() => handleSuspendUser(row.original.id)}
              ></CustomButton>
              <CustomButton
                icon={<Trash />}
                onClick={() => handleDeleteUser(row.original.id)}
                className="ml-2"
              />
            </div>
          ),
        }
      : col,
  );

  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/admin" },
          { label: "Users" },
        ]}
        title="Users Page"
      />
      <div className="p-5">
        <div className="flex justify-center items-center pt-10 pb-10">
          <Heading text="Users" className="text-4xl lg:text-6xl" />
        </div>
        <DataTable
          data={data?.data || []}
          columns={columns}
          pageIndex={page}
          totalPages={totalPages}
          onPreviousPage={handlePreviousPage}
          onNextPage={handleNextPage}
        />
      </div>
    </div>
  );
};

export default User;
