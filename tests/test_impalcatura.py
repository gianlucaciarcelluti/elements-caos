"""Verifica che il pacchetto sia importabile e correttamente configurato."""


def test_pacchetto_importabile() -> None:
    """Il pacchetto elements_caos deve essere importabile e avere una versione."""
    import elements_caos

    assert elements_caos.__version__ == "0.1.0"
