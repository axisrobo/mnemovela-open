from __future__ import annotations


class MnemovelaError(Exception):
    """Raised when a Mnemovela gRPC call fails. Wraps grpc.RpcError without
    requiring callers to import grpc."""

    def __init__(self, code: str, details: str, data=None):
        super().__init__(f"{code}: {details}")
        self.code = code
        self.details = details
        self.data = data

    @classmethod
    def from_rpc_error(cls, err) -> "MnemovelaError":
        code = getattr(err.code(), "name", "UNKNOWN") if hasattr(err, "code") else "UNKNOWN"
        details = err.details() if hasattr(err, "details") else str(err)
        return cls(code, details)
