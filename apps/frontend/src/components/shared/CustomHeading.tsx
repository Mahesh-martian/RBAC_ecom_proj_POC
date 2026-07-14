import React from "react";
import clsx from "clsx"; // Import clsx

interface HeadingProps {
  text: string;
  className?: string;
}

const Heading: React.FC<HeadingProps> = ({ text, className }) => {
  return (
    <h1
      className={clsx(
        "text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r",
        "from-[hsl(var(--chart-1))] to-[hsl(var(--chart-2))]",
        "dark:from-[hsl(var(--chart-3))] dark:to-[hsl(var(--chart-4))]",
        className,
      )}
    >
      {text}
    </h1>
  );
};

export default Heading;
