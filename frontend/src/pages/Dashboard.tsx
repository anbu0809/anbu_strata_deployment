import { useNavigate } from 'react-router-dom';
import { BarChart, Users, AlertTriangle, CheckCircle, Database, TrendingUp } from 'lucide-react';

const Dashboard = () => {
  const navigate = useNavigate();

  const handleStartMigration = () => {
    navigate('/analyze');
  };
  const stats = [
    {
      title: 'Total Migration Data',
      value: '0 GB',
      icon: Database,
      gradient: 'bg-gradient-to-r from-[#ec6225] to-[#085690]',
      change: 'Ready to start'
    },
    {
      title: 'Top Migration Issues',
      value: '0',
      icon: AlertTriangle,
      gradient: 'bg-gradient-to-r from-[#085690] to-[#ec6225]',
      change: 'No issues detected'
    },
    {
      title: 'Migrations Completed',
      value: '0',
      icon: CheckCircle,
      gradient: 'bg-gradient-to-r from-[#ec6225] to-[#085690]',
      change: 'No migrations yet'
    },
    {
      title: 'Failed Migrations',
      value: '0',
      icon: TrendingUp,
      gradient: 'bg-gradient-to-r from-[#085690] to-[#ec6225]',
      change: 'No failures yet'
    }
  ];

  const recentActivity = [
    { id: 1, action: 'Migration completed', source: 'MySQL → PostgreSQL', status: 'success', time: '2 hours ago' },
    { id: 2, action: 'Schema analysis started', source: 'Oracle → PostgreSQL', status: 'pending', time: '4 hours ago' },
    { id: 3, action: 'Migration failed', source: 'PostgreSQL → MySQL', status: 'failed', time: '6 hours ago' },
    { id: 4, action: 'Data validation passed', source: 'MySQL → PostgreSQL', status: 'success', time: '8 hours ago' },
    { id: 5, action: 'Connection established', source: 'SQL Server → PostgreSQL', status: 'success', time: '1 day ago' }
  ];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">Overview of your database migration activities</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className={`${stat.gradient} p-3 rounded-lg`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
              <div className="mt-4">
                <span className="text-sm text-gray-500">{stat.change}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    activity.status === 'success' ? 'bg-green-500' :
                    activity.status === 'pending' ? 'bg-yellow-500' : 'bg-red-500'
                  }`}></div>
                  <div>
                    <p className="font-medium text-gray-900">{activity.action}</p>
                    <p className="text-sm text-gray-500">{activity.source}</p>
                  </div>
                </div>
                <span className="text-sm text-gray-500">{activity.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={handleStartMigration}
            className="p-4 bg-gradient-to-r from-[#ec6225] to-[#085690] text-white rounded-lg hover:from-[#d5551f] hover:to-[#074580] transition-colors font-medium"
          >
            Start New Migration
          </button>
          <button
            onClick={() => navigate('/reconcile')}
            className="p-4 bg-gradient-to-r from-[#085690] to-[#ec6225] text-white rounded-lg hover:from-[#074580] hover:to-[#d5551f] transition-colors font-medium"
          >
            View Reports
          </button>
          <button className="p-4 bg-gradient-to-r from-[#ec6225] to-[#085690] text-white rounded-lg hover:from-[#d5551f] hover:to-[#074580] transition-colors font-medium">
            Export Data
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-12 text-center">
        <p className="text-lg font-bold text-gray-900 mb-2">DecisionMinds</p>
        <p className="text-sm text-gray-600">Powered by DecisionMinds</p>
      </div>
    </div>
  );
};

export default Dashboard;