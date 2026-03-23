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
import tomllib
from pathlib import Path

from .setting import (
    HF_MODELS_SUBDIR,
    HF_MODEL_DIR_PREFIX,
    FE_MODEL_SPEC_FILE_NAME,
    FE_DATA_PREC,
    FE_DATA_CAST,
)


def _get_static_encoder(conf):
    import model2vec
    static_encoder = model2vec.StaticModel.from_pretrained(
        path=conf["embed"]["static_embed_model"],
        force_download=False,
    )
    return {
        "name": conf["embed"]["static_embed_model"],
        "dim": conf["embed"]["static_embed_dim"],
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
    model_name = conf["embed"]["dense_embed_model"]

    model_is_known = False
    for test_model in fastembed.TextEmbedding.list_supported_models():
        if test_model["model"].lower() == model_name.lower():
            model_is_known = True
            break

    if not model_is_known:
        import fastembed.common.model_description as fe_desc
        model_dir = Path(
            conf["embed"]["models_base_dir"]["path"],
            HF_MODELS_SUBDIR,
            HF_MODEL_DIR_PREFIX + model_name.replace("/", "--"),
        )
        with open(model_dir / FE_MODEL_SPEC_FILE_NAME, "rb") as fh:
            model_spec = tomllib.load(fh)["fastembed"]
        is_pooled = model_spec["pooled"]
        is_normailzed = model_spec["normailzed"]
        embed_dim = model_spec["embed_dim"]
        if embed_dim != conf["embed"]["dense_embed_dim"]:
            raise OSError(" ".join([
                f"the dense-model spec on embedding dimension ({embed_dim})",
                "differs from the dimension set at the overall config:",
                str(conf["embed"]["dense_embed_dim"]),
            ]))
        model_file = model_spec["model_file"]
        fastembed.TextEmbedding.add_custom_model(
            model=model_name,
            pooling=(
                fe_desc.PoolingType.MEAN if is_pooled else
                fe_desc.PoolingType.DISABLED
            ),
            normalization=is_normailzed,
            sources=fe_desc.ModelSource(
                hf=model_name,
            ),
            dim=embed_dim,
            model_file=model_file,
        )

    dense_encoder = fastembed.TextEmbedding(
        model_name=model_name,
        cache_dir=conf["embed"]["models_cache_dir"]["path"],
        local_files_only=True,
    )

    return {
        "name": conf["embed"]["dense_embed_model"],
        "dim": conf["embed"]["dense_embed_dim"],
        "method": lambda text, is_query=False: (
            list(dense_encoder.query_embed([text]))[0].astype(
                FE_DATA_PREC, casting=FE_DATA_CAST
            )
            if is_query else
            list(dense_encoder.embed([text]))[0].astype(
                FE_DATA_PREC, casting=FE_DATA_CAST
            )
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
