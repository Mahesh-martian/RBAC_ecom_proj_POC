import React from "react";
import clsx from "clsx";

// Typography Component
type TypographyProps = {
  children: React.ReactNode;
  className?: string;
};

export const H1: React.FC<TypographyProps> = ({ children, className }) => (
  <h1
    className={clsx(
      "scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl text-foreground dark:text-primary-foreground",
      className,
    )}
  >
    {children}
  </h1>
);

export const H2: React.FC<TypographyProps> = ({ children, className }) => (
  <h2
    className={clsx(
      " scroll-m-20 text-3xl font-semibold tracking-tight transition-colors ",
      className,
    )}
  >
    {children}
  </h2>
);

export const H3: React.FC<TypographyProps> = ({ children, className }) => (
  <h3
    className={clsx(
      "scroll-m-20 text-2xl font-semibold tracking-tight text-foreground dark:text-secondary-foreground",
      className,
    )}
  >
    {children}
  </h3>
);

export const H4: React.FC<TypographyProps> = ({ children, className }) => (
  <h4
    className={clsx(
      "scroll-m-20 text-xl font-semibold tracking-tight ",
      className,
    )}
  >
    {children}
  </h4>
);

export const H5: React.FC<TypographyProps> = ({ children, className }) => (
  <h5
    className={clsx(
      "scroll-m-20 text-lg font-semibold tracking-tight text-foreground dark:text-muted-foreground",
      className,
    )}
  >
    {children}
  </h5>
);

export const H6: React.FC<TypographyProps> = ({ children, className }) => (
  <h6
    className={clsx(
      "scroll-m-20 text-base font-semibold tracking-tight text-foreground dark:text-muted-foreground",
      className,
    )}
  >
    {children}
  </h6>
);

export const Paragraph: React.FC<TypographyProps> = ({
  children,
  className,
}) => (
  <p
    className={clsx(
      "leading-7 text-muted-foreground dark:text-accent-foreground",
      className,
    )}
  >
    {children}
  </p>
);

export const Blockquote: React.FC<TypographyProps> = ({
  children,
  className,
}) => (
  <blockquote
    className={clsx(
      "mt-6 border-l-2 pl-6 italic text-muted-foreground dark:text-muted",
      className,
    )}
  >
    {children}
  </blockquote>
);

export const List: React.FC<TypographyProps> = ({ children, className }) => (
  <ul
    className={clsx(
      "my-6 ml-6 list-disc [&>li]:mt-2 text-foreground dark:text-muted-foreground",
      className,
    )}
  >
    {children}
  </ul>
);

export const Table: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className }) => (
  <div className="my-6 w-full overflow-y-auto">
    <table
      className={clsx(
        "w-full border-collapse border-spacing-0 text-foreground dark:text-muted-foreground",
        className,
      )}
    >
      {children}
    </table>
  </div>
);
