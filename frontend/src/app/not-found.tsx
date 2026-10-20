import Link from "next/link";

export default function NotFound() {
  return (
    <>
      <h1>Page Not Found</h1>
      <p>The page you asked for does not exist or has moved.</p>
      <Link href="/">Back to Home</Link>
    </>
  );
}
