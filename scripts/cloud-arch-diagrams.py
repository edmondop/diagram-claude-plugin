# /// script
# requires-python = ">=3.10"
# dependencies = ["diagrams"]
# ///
"""
Cloud/infra architecture diagram using the diagrams (mingrammer) library.

Requires graphviz system binary:
  macOS:         brew install graphviz
  Ubuntu/Debian: sudo apt-get install graphviz
  Fedora:        sudo dnf install graphviz

Run: uv run cloud-arch-diagrams.py
"""
from pathlib import Path

from diagrams import Cluster, Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.network import ELB, Route53
from diagrams.aws.storage import S3


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    with Diagram(
        "Web Application Architecture",
        show=False,
        filename="output/cloud-arch-diagrams",
        outformat="svg",
        direction="TB",
    ):
        dns = Route53("DNS")
        lb = ELB("Load Balancer")

        with Cluster("Web Tier"):
            web = [EC2("web-1"), EC2("web-2"), EC2("web-3")]

        with Cluster("Data Tier"):
            db = RDS("PostgreSQL")
            db - [RDS("read-replica")]

        cache = ElastiCache("Redis")
        storage = S3("Static Assets")

        dns >> lb >> web
        web >> db
        web >> cache
        web >> storage

    print("Saved: output/cloud-arch-diagrams.svg")


if __name__ == "__main__":
    main()
