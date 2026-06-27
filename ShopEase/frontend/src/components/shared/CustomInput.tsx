import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ReactNode, forwardRef } from "react";
import { cn } from "@/lib/utils";

type InputProps = {
  label?: string;
  placeholder?: string;
  isRequired?: boolean;
  icon?: ReactNode;
  type?: string;
  error?: string | undefined;
  inputClassName?: string;
  labelClassName?: string;
  iconClassName?: string;
} & React.ComponentPropsWithoutRef<"input">;

const CustomInput = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      placeholder,
      isRequired,
      icon,
      type = "text",
      error,
      inputClassName = "",
      labelClassName = "",
      iconClassName = "",
      ...rest
    },
    ref,
  ) => {
    return (
      <div className="flex flex-col gap-2">
        {label && (
          <Label className={cn("text-sm font-medium", labelClassName)}>
            {label} {isRequired && <span className="text-red-500">*</span>}
          </Label>
        )}
        <div className="relative">
          {icon && (
            <div
              className={cn(
                "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500",
                iconClassName,
              )}
            >
              {icon}
            </div>
          )}
          <Input
            ref={ref}
            type={type}
            placeholder={placeholder}
            className={cn(
              icon ? "pl-10" : "",
              !placeholder ? "placeholder-transparent" : "",
              inputClassName,
            )}
            {...rest}
          />
        </div>
        {error && <span className="text-red-500 text-xs">{error}</span>}
      </div>
    );
  },
);

CustomInput.displayName = "CustomInput";
export default CustomInput;
