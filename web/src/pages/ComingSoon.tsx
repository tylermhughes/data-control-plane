export function ComingSoon({ what, milestone }: { what: string; milestone: string }) {
  return (
    <>
      <div className="view-head">
        <h1>{what}</h1>
      </div>
      <div className="panel empty">
        <p>
          <strong>{what}</strong> arrives in milestone {milestone}.
        </p>
        <p>Everything here is already available through the API at /docs.</p>
      </div>
    </>
  );
}
