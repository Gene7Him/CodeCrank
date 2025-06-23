import { useState } from 'react';

export default function Home() {
  const [repoUrl, setRepoUrl] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    setOutput('');
    const res = await fetch('http://localhost:8000/run-repo/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl }),
    });
    const data = await res.json();
    setOutput(JSON.stringify(data, null, 2));
    setLoading(false);
  };

  return (
    <div className="p-10 font-mono">
      <h1 className="text-2xl mb-4">ReplRunner</h1>
      <input
        type="text"
        placeholder="Paste GitHub repo URL"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        className="border px-3 py-2 w-full max-w-lg"
      />
      <button
        onClick={handleRun}
        disabled={loading}
        className={`mt-4 px-4 py-2 text-white ${loading ? "bg-gray-600" : "bg-black"}`}
      >
        {loading ? 'Running...' : 'Run Repo'}
      </button>

      {output && (
        <pre className="mt-6 p-4 bg-gray-100 text-sm whitespace-pre-wrap">
          {output}
        </pre>
      )}
    </div>
  );
}
