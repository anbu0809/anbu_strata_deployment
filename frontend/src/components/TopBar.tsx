import { Settings, LogOut } from 'lucide-react';

interface TopBarProps {
  onSettingsClick: () => void;
}

const TopBar = ({ onSettingsClick }: TopBarProps) => {
  return (
    <div className="bg-white shadow-sm border-b px-6 py-4 flex justify-between items-center">
      <div className="flex items-center">
        <div>
          <h2 className="text-lg font-bold text-[#085690]">Strata</h2>
          <p className="text-xs text-gray-500 -mt-1">AI-Powered Database Migration</p>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <div className="flex items-center">
          <div className="w-3 h-3 rounded-full bg-[#085690] mr-2"></div>
          <span className="text-sm font-medium text-[#085690]">Online</span>
        </div>
        
        <button 
          onClick={onSettingsClick}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          aria-label="Database Connections"
          title="Database Connections"
        >
          <Settings className="h-5 w-5 text-[#085690]" />
        </button>
        
        <button 
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          aria-label="Logout"
        >
          <LogOut className="h-5 w-5 text-[#085690]" />
        </button>
      </div>
    </div>
  );
};

export default TopBar;