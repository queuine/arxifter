#!/usr/bin/env python
"""
Preparation of encoders.

A combination of embedding models that provides reasonable presifting
results with sustainable requirements on resources is:
* dense model known as BAAI/bge-base-en-v1.5 for fastembed
  (even though it is actually qdrant/bge-base-en-v1.5-onnx-q model,
  a version quantized by Qdrant who is the maker of fastembed too),
* NeuML/pubmedbert-base-embeddings-8M static model.

Notice:
It is important to not import the model2vec.StaticModel class globally,
b/c it would lead to taking the HF_HUB_CACHE env variable before it is
set within loading arxifter configuration.
The used embedding model would get re-downloaded from HF then.
"""


def _get_static_encoder(conf):
    import model2vec
    static_encoder = model2vec.StaticModel.from_pretrained(
        path=conf["embed"]["static_embed_model"],
        force_download=False,
    )
    return {
        "name": conf["embed"]["static_embed_model"],
        # the "is_query" parameter is not used now, but keeping it,
        # since it may get used at some point;
        "method": lambda text, is_query=False: (
            list(static_encoder.encode(text))
            if type(text) in (list, tuple) else
            list(static_encoder.encode([text]))[0]
        ),
    }


def _get_dense_encoder(conf):
    import fastembed
    dense_encoder = fastembed.TextEmbedding(
        model_name=conf["embed"]["dense_embed_model"],
        cache_dir=conf["embed"]["models_cache_dir"]["path"],
        local_files_only=True,
    )
    return {
        "name": conf["embed"]["dense_embed_model"],
        "method": lambda text, is_query=False: (
            list(dense_encoder.query_embed([text]))[0]
            if is_query else
            list(dense_encoder.embed([text]))[0]
        ),
    }


def get_encoders(conf, logging=None):
    """
    Provides encoders used for making embeddings of docs and queries.
    """
    try:
        return {
            "static": _get_static_encoder(conf),
            "dense": _get_dense_encoder(conf),
        }
    except Exception as exc:
        if logging is not None:
            logging.error("\n".join([
                "cannot load embedding encoders",
                str(exc),
            ]))
        return None
