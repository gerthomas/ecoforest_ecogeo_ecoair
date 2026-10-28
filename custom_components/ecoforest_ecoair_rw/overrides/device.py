from dataclasses import dataclass


@dataclass
class EcoGeoDevice:
    is_supported: bool
    model_name: str

    state: dict[str, any] | None = None

    raw_values: dict | None = None
    failed_reads: list | None = None
    observed_at: str | None = None

    @classmethod
    def build(cls, model_name: str, data: dict[str, any], **metadata):  # -> EcoGeoDevice:

        return EcoGeoDevice(
            is_supported=True,
            model_name=model_name,
            state=data,
            **metadata
        )
