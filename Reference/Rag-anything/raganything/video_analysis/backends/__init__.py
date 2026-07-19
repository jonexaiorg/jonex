"""Built-in video analysis backends — imported to trigger @register_video_analysis_backend."""

from raganything.video_analysis.backends.local import LocalVideoBackend  # noqa: F401
from raganything.video_analysis.backends.mps import MPSVideoBackend  # noqa: F401
