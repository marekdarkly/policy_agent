import { useIndustry } from '@/utils/contexts/IndustryContext';

export const IndustryDebug = () => {
  const { industry, assets, flagValue } = useIndustry();
  
  return (
    <div className="fixed top-4 right-4 bg-black bg-opacity-75 text-white p-4 rounded-lg text-sm z-50">
      <div className="font-bold mb-2">Industry Debug</div>
      <div>Flag Value: <span className="text-yellow-400">{flagValue}</span></div>
      <div>Industry: <span className="text-green-400">{industry}</span></div>
      <div>Title: <span className="text-blue-400">{assets.title}</span></div>
      <div className="mt-2 text-xs opacity-75">
        Assets: {Object.keys(assets.icons).length} icons loaded
      </div>
    </div>
  );
};
