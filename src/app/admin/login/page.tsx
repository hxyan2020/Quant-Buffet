import AdminLoginForm from "@/components/admin/AdminLoginForm";

export default function AdminLoginPage() {
  return (
    <div className="qb-admin-login-page">
      <div className="qb-admin-login-card">
        <p className="qb-admin-login-eyebrow">Quant Buffet</p>
        <h1 className="qb-admin-login-title">Admin sign in</h1>
        <p className="qb-admin-login-sub">
          Staff-only CMS. This is separate from the public member login.
        </p>
        <AdminLoginForm />
        <p className="qb-admin-login-foot">
          <a href="/en">← Back to website</a>
        </p>
      </div>
    </div>
  );
}
