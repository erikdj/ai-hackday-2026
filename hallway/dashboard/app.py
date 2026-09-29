"""Judge dashboard. FastAPI is imported only inside create_app()."""

_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>TrustEdge</title></head>
<body>
<h1>TrustEdge AI Safe Scribe: who saw what</h1>
<pre id="who"></pre><pre id="followups"></pre><pre id="history"></pre>
<script>
fetch("/summary").then(function (r) { return r.json(); }).then(function (d) {
  document.getElementById("who").textContent = JSON.stringify(d.who_saw_identifiers);
  document.getElementById("followups").textContent = JSON.stringify(d.open_followups);
  document.getElementById("history").textContent = JSON.stringify(d.histories);
});
</script>
</body></html>
"""


def create_app():
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    from hallway.dashboard import queries

    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/lineage/who-saw-identifiers")
    def who_saw():
        return queries.who_saw_identifiers()

    @app.get("/followups")
    def followups():
        return queries.open_followups()

    @app.get("/patients/{pseudo_id}/history")
    def history(pseudo_id: str):
        return queries.patient_history(pseudo_id)

    @app.get("/summary")
    def summary():
        return queries.summary()

    @app.get("/", response_class=HTMLResponse)
    def index():
        return _PAGE

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=8090)
