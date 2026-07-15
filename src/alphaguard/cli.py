"""CLI entrypoints — smoke / replay without starting Kafka."""

from __future__ import annotations

import os

# OpenMP: XGBoost + other native libs can collide on macOS; fail-open for local smoke.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import argparse
import json
import logging
import sys
from pathlib import Path

from alphaguard.config import get_settings
from alphaguard.infra.preflight import PreflightError, preflight_ollama
from alphaguard.ingest.consumer import NewsRawConsumer
from alphaguard.ingest.producer import KafkaProduceError, create_producer, produce_event
from alphaguard.ingest.replay import FixtureLoadError, get_event_by_id, run_replay
from alphaguard.pipeline.service import PipelineService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("alphaguard")


def cmd_smoke(event_id: str | None) -> int:
    settings = get_settings()
    settings.alphaguard_mode = "replay"
    # Prefer fixture RAG for default smoke (16GB-safe).
    if not settings.alphaguard_rag_mode:
        settings.alphaguard_rag_mode = "fixture"

    try:
        model = preflight_ollama(settings)
    except PreflightError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    service = PipelineService(settings=settings, resolved_model=model)
    fixtures = settings.fixtures_dir / "replay_events.jsonl"
    try:
        envelope = run_replay(service, fixtures, event_id=event_id)
    except FixtureLoadError as exc:
        print(f"fixture error: {exc}", file=sys.stderr)
        return 2

    print("=== AlphaGuard smoke (replay) ===")
    print(f"model={model} mode={envelope.mode} rag_mode={envelope.rag_mode}")
    print(f"status={envelope.status} run_id={envelope.run_id}")
    print(f"obs.langsmith={envelope.obs.langsmith} obs.phoenix={envelope.obs.phoenix}")
    print(f"local_summary={envelope.obs.local_summary_path}")
    if envelope.proposal:
        print("Agent1 proposal:")
        print(json.dumps(envelope.proposal.model_dump(mode="json"), indent=2))
    if envelope.decision:
        print("Agent2 decision:")
        print(json.dumps(envelope.decision.model_dump(mode="json"), indent=2))
    if envelope.error:
        print("error:")
        print(json.dumps(envelope.error.model_dump(mode="json"), indent=2))
        return 1
    if envelope.status == "error":
        return 1
    return 0


def cmd_replay(event_id: str | None) -> int:
    return cmd_smoke(event_id)


def cmd_kafka_consume() -> int:
    settings = get_settings()
    service = PipelineService(settings=settings, skip_ollama_preflight=True)
    NewsRawConsumer(settings, service).run_forever()
    return 0


def cmd_kafka_produce(event_id: str) -> int:
    settings = get_settings()
    fixtures = settings.fixtures_dir / "replay_events.jsonl"
    try:
        event = get_event_by_id(fixtures, event_id)
    except FixtureLoadError as exc:
        print(f"fixture error: {exc}", file=sys.stderr)
        return 2

    producer = create_producer(settings.kafka_bootstrap_servers)
    try:
        result = produce_event(producer, event)
    except KafkaProduceError as exc:
        print(f"kafka produce error: {exc}", file=sys.stderr)
        return 2
    finally:
        producer.close()

    print(json.dumps(result))
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="alphaguard")
    sub = parser.add_subparsers(dest="command", required=True)

    smoke = sub.add_parser("smoke", help="Replay-first smoke (Kafka not required)")
    smoke.add_argument("--event-id", default=None)

    replay = sub.add_parser("replay", help="Replay one fixture event via PipelineService")
    replay.add_argument("--event-id", default=None)

    pre = sub.add_parser("preflight", help="Check Ollama reachability + model tag")
    pre.add_argument("--json", action="store_true")

    kafka = sub.add_parser("kafka", help="Kafka ingest helpers (requires Compose)")
    kafka_sub = kafka.add_subparsers(dest="kafka_command", required=True)
    kafka_sub.add_parser("consume", help="Start news.raw consumer")
    produce = kafka_sub.add_parser("produce", help="One-shot produce from fixture event_id")
    produce.add_argument("--event-id", default="evt-aapl-001")

    args = parser.parse_args(argv)
    if args.command == "preflight":
        settings = get_settings()
        try:
            model = preflight_ollama(settings)
        except PreflightError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(2)
        payload = {"ok": True, "model": model, "base_url": settings.ollama_base_url}
        print(json.dumps(payload) if args.json else f"ok model={model}")
        sys.exit(0)

    if args.command == "kafka":
        if args.kafka_command == "consume":
            sys.exit(cmd_kafka_consume())
        sys.exit(cmd_kafka_produce(args.event_id))

    event_id = getattr(args, "event_id", None)
    code = cmd_smoke(event_id)
    sys.exit(code)


if __name__ == "__main__":
    main()
