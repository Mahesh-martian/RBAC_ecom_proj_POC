import { FeatureCardProps } from "@/types";

const FeatureCard: React.FC<FeatureCardProps> = ({ Icon, text }) => {
  return (
    <div className="flex flex-col items-center text-center gap-2">
      <Icon className="w-8 h-8 text-muted-foreground" />
      <span className="text-sm">{text}</span>
    </div>
  );
};

export default FeatureCard;
