import AppHeader from "../../components/header/AppHeader";

const users = [
  {
    name: "Shalaka",
    email: "shalaka@company.com",
    drive: "Connected",
    docs: 245,
  },
  {
    name: "John",
    email: "john@company.com",
    drive: "Connected",
    docs: 180,
  },
  {
    name: "Sarah",
    email: "sarah@company.com",
    drive: "Connected",
    docs: 132,
  },
];

export default function Users() {
  return (
    <>
      <AppHeader />

      <div className="bg-white rounded-xl shadow p-5">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left py-3">Name</th>
              <th className="text-left py-3">Email</th>
              <th className="text-left py-3">Drive Status</th>
              <th className="text-left py-3">Documents</th>
            </tr>
          </thead>

          <tbody>
            {users.map((user) => (
              <tr
                key={user.email}
                className="border-b"
              >
                <td className="py-3">{user.name}</td>
                <td>{user.email}</td>
                <td>{user.drive}</td>
                <td>{user.docs}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}