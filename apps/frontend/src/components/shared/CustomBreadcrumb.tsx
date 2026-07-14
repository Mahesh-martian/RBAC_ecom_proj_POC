import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import Link from "next/link";
import { FC } from "react";

interface BreadcrumbProps {
  items: {
    label: string;
    path?: string;
  }[];
  title: string;
}

const CustomBreadcrumb: FC<BreadcrumbProps> = ({ items, title }) => {
  return (
    <div className="bg-gradient-to-r from-primary to-accent dark:from-yellow-500 dark:to-yellow-600 py-6 lg:py-12 px-8 rounded-md shadow-md text-foreground dark:text-yellow-200">
      <Breadcrumb className="flex items-center space-x-2 text-sm">
        {items.map((item, index) => (
          <BreadcrumbItem key={index}>
            {item.path ? (
              <Link
                href={item.path}
                className="lg:text-lg text-primary-foreground dark:text-white hover:underline"
              >
                {item.label}
              </Link>
            ) : (
              <span className="text-muted-foreground dark:text-white lg:text-lg">
                {item.label}
              </span>
            )}
            {index < items.length - 1 && (
              <BreadcrumbSeparator className="text-border dark:text-white">
                /
              </BreadcrumbSeparator>
            )}
          </BreadcrumbItem>
        ))}
      </Breadcrumb>
      <h1 className="text-3xl lg:text-6xl font-bold lg:mt-4 text-primary-foreground dark:text-white">
        {title}
      </h1>
    </div>
  );
};

export default CustomBreadcrumb;
