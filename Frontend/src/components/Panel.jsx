export default function Panel({ title, action, children }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        {action ? <div className="panel-action">{action}</div> : null}
      </div>
      <div className="panel-content">{children}</div>
    </section>
  );
}
