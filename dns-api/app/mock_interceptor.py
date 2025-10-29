# send_dns_query.py
# Requiere: pip install dnspython requests
import base64, requests, sys, argparse
import dns.message, dns.rdatatype

API_URL = "http://localhost:8080/api/dns_resolver"  # ajustar si corre en otra parte

def make_query_bytes(name: str, qtype="A"):
    q = dns.message.make_query(name, qtype)
    return q.to_wire()

def send_to_api(payload_bytes: bytes, timeout_ms: int = 2000):
    payload_b64 = base64.b64encode(payload_bytes).decode()
    body = {"base64_data": payload_b64, "timeout_ms": timeout_ms}
    r = requests.post(API_URL, json=body, timeout=10)
    return r

def main():
    p = argparse.ArgumentParser()
    p.add_argument("name", help="FQDN to query, e.g. www.google.com")
    p.add_argument("--timeout", type=int, default=2000)
    args = p.parse_args()
    qbytes = make_query_bytes(args.name)
    print(f"Query bytes len: {len(qbytes)}")
    r = send_to_api(qbytes, args.timeout)
    print("Status:", r.status_code)
    print("Body:", r.text)
    if r.status_code == 200:
        print("Response received")
    else:
        print("Error response JSON:", r.json())

if __name__ == "__main__":
    main()