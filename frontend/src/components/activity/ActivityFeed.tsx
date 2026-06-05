export default function ActivityFeed() {
  const activities = [
    {
      user: "Shalaka",
      action: "viewed",
      item: "API_Request_SOP.pdf",
    },
    {
      user: "user 2",
      action: "uploaded",
      item: "Deployment_Guide.pdf",
    },
  ];

  return (
    <div className="h-full bg-white border-r border-gray-200 p-4">
      <h2 className="text-lg font-bold mb-4">
        Recent Activity
      </h2>

      <div className="space-y-3">
        {activities.map((activity, index) => (
          <div
            key={index}
            className="p-3 rounded-lg bg-slate-50"
          >
            <p className="font-medium">
              {activity.user}
            </p>

            <p className="text-sm text-gray-600">
              {activity.action}
            </p>

            <p className="text-sm break-words">
              {activity.item}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}