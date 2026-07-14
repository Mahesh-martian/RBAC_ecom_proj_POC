import { Skeleton } from "@/components/ui/skeleton";

const SkeletonCard = () => (
  <div className="h-[420px] w-[300px] p-4 bg-white dark:bg-black rounded-lg">
    <Skeleton className="w-full h-[300px] rounded" />
    <div className="mt-4">
      <Skeleton className="w-3/4 h-[20px] mb-2" />
      <Skeleton className="w-1/2 h-[20px]" />
    </div>
  </div>
);

export default SkeletonCard;
