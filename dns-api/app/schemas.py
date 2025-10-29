from typing import Optional
from pydantic import BaseModel

class DNSResolverIn(BaseModel):
    base64_data: str # base64 encoded DNS query
    timeout_ms: Optional[int] = 2000

class ExistsOut(BaseModel):
    exists: bool
    record_type: Optional[str] = None

class DNSResolverOut(BaseModel):
    response_base64: str # base64 encoded DNS response
    contacted_server: str
    rtt_ms: int


class DNSResolveIn(BaseModel):
    host: str
    client_ip: str

class DNSResolveOut(BaseModel):
    ip: str
    target_id: Optional[str] = None
    type: Optional[str] = None

class HealthUpdate(BaseModel):
    fqdn: str
    target_id: str
    region: str
    rtt: float
    status: str