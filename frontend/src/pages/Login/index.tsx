export default function Login() {
  const login = () => {
    window.location.href =
      "http://localhost:8000/api/auth/google/login";
  };

  return (
    <div className="h-screen flex items-center justify-center">
      <div className="bg-white p-8 rounded-xl shadow">
        <h1 className="text-3xl font-bold mb-6">
          Enterprise KMS
        </h1>

        <button
          onClick={login}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
}