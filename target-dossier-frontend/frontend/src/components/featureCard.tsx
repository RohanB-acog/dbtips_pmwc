import { LucideIcon } from 'lucide-react';

interface FeatureCardProps {
  Icon: LucideIcon;
  title: string;
  description: string;
}

 function FeatureCard({ Icon, title, description }: FeatureCardProps) {
  return (
    <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl shadow-sm hover:shadow-md transition-all hover:-translate-y-1">
      <div className="bg-indigo-100 w-10 h-10 rounded-xl flex items-center justify-center mb-3">
        <Icon className="h-5 w-5 text-blue-600" />
      </div>
      <h3 className="text-lg font-semibold mb-1">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}
export default FeatureCard;