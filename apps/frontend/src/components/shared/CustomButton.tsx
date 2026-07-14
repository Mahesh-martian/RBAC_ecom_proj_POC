import { Button, ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { AiOutlineLoading3Quarters } from "react-icons/ai";

interface ReusableButtonProps extends ButtonProps {
  icon?: React.ReactNode;
  loading?: boolean;
  iconPosition?: "left" | "right";
}

const CustomButton: React.FC<ReusableButtonProps> = ({
  children,
  icon,
  loading,
  className,
  onClick,
  variant,
  iconPosition = "left",
  ...props
}) => {
  return (
    <Button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 px-4 py-2 rounded-md transition",
        loading && "opacity-50 cursor-not-allowed",
        className,
      )}
      variant={variant}
      {...props}
    >
      {loading ? (
        <span className="animate-spin">
          <AiOutlineLoading3Quarters className="text-primary" />
        </span>
      ) : iconPosition === "left" && icon ? (
        <span>{icon}</span>
      ) : null}

      {children}

      {!loading && iconPosition === "right" && icon ? (
        <span>{icon}</span>
      ) : null}
    </Button>
  );
};

export default CustomButton;
