PRESETS = {
    "tiny": {
        "download_rate_kbps": 512,
        "upload_rate_kbps": 128,
        "concurrency": 1,
        "mode": "download",
        "interval_seconds": 1.0,
    },
    "low": {
        "download_rate_kbps": 1024,
        "upload_rate_kbps": 256,
        "concurrency": 2,
        "mode": "mixed",
        "interval_seconds": 1.0,
    },
    "medium": {
        "download_rate_kbps": 4096,
        "upload_rate_kbps": 1024,
        "concurrency": 3,
        "mode": "mixed",
        "interval_seconds": 1.0,
    },
    "high": {
        "download_rate_kbps": 8192,
        "upload_rate_kbps": 2048,
        "concurrency": 4,
        "mode": "mixed",
        "interval_seconds": 1.0,
    },
}
