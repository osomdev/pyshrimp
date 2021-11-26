def _collect_stream_to_string(stream) -> str:
    if isinstance(stream, str):
        return stream

    try:
        return stream.read()
    finally:
        stream.close()
