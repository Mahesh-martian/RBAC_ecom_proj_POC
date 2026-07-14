import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import Heading from "@/components/shared/CustomHeading";
import { DataTable } from "@/components/shared/DataTable";
import { AdminTransactionTableColumns } from "@/components/shared/tableColumnDef/AdminTransactionTableColumns";
import { useGetPaymentsQuery } from "@/redux/api/paymentApi";
import React, { useState } from "react";

const Transactions = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const { data } = useGetPaymentsQuery({ page: 1, limit: 10 });

  const totalPages = Math.ceil((data?.meta?.total || 0) / limit);

  const handlePreviousPage = () => {
    if (page > 1) setPage((prev) => prev - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage((prev) => prev + 1);
  };

  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/admin" },
          { label: "Transactions" },
        ]}
        title="Transactions Page"
      />
      <div className="p-5 pb-20">
        <div className="flex justify-center items-center pt-10 pb-10">
          <Heading text="Transactions" className="text-4xl lg:text-6xl" />
        </div>
        <DataTable
          data={data?.data || []}
          columns={AdminTransactionTableColumns}
          pageIndex={page}
          totalPages={totalPages}
          onPreviousPage={handlePreviousPage}
          onNextPage={handleNextPage}
        />
      </div>
    </div>
  );
};

export default Transactions;
