# arxifter: sifting through open archives

It is intended for AI searches on arxiv, biorxiv, etc.
The first module is prepared for ***bioRχiv***, sifting through its feeds.

The interface to arxifter searches is via a *Flask* web server.
When arxifter is run the way described below, it listens on port *8000*,
i.e. being available on `http://localhost:8000`.

#### Arxifter is in a developmental stage, being used via docker/podman.

Arxifter does the (indexing and) searching via LLM servers, and by that it needs respective API keys.
The current implementation uses *OpenAI* services through the *LlamaIndex* framework,
with the OpenAI API key to be put into the `srv/keys/llm_key.txt` file.

To run arxifter via podman, run the two following commands from the arxifter distribution directory;
it contains the `Dockerfile` file.

- `buildah build -f Dockerfile -t arxifter:v01 .`
- `podman run -it -p 8000:5000 -v ./srv:/arxifter/srv --name arxifter arxifter:v01`

To stop and restart the containers, do it the standard ways, e.g. via `podman stop arxifter`
and `podman start -ia arxifter` commands.

Once being within a running container, biorxiv RSS feeds can be taken, parsed and indexed
by the `feeder.sh` script in the `srv` subdirectory.
Then the web server can be started by the `server.sh` script located there too.

**The project site is at [QuaDet](https://quadet.com/arxifter/) and its repository is hosted at [Codeberg](https://codeberg.org/msat/arxifter/).**
