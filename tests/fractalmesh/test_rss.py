from __future__ import annotations

from datetime import datetime, timedelta

from fractalmesh.rss.config import export_opml, load_sources_from_env, load_sources_from_file
from fractalmesh.rss.processor import RSSProcessor
from fractalmesh.rss.rotation import RSSSource, SourcePool


def test_source_pool_returns_available_source() -> None:
    pool = SourcePool()
    pool.add_source(RSSSource(url="https://a.example/rss", weight=2.0))
    assert pool.next_source() is not None


def test_source_pool_applies_backoff() -> None:
    pool = SourcePool()
    source = RSSSource(url="https://a.example/rss", ttl_seconds=30)
    source.last_fetched = datetime.utcnow()
    source.fail_count = 2
    pool.add_source(source)
    assert pool.next_source() is None
    source.last_fetched = datetime.utcnow() - timedelta(seconds=200)
    assert pool.next_source() is not None


def test_source_pool_success_and_dedup() -> None:
    pool = SourcePool()
    pool.add_source(RSSSource(url="https://a.example/rss"))
    pool.mark_success("https://a.example/rss")
    pool.record_seen("hash-1")
    assert pool.is_duplicate("hash-1") is True
    assert pool.sources["https://a.example/rss"].fail_count == 0


def test_load_sources_from_env(monkeypatch) -> None:
    monkeypatch.setenv("RSS_SOURCES", "https://a.example/rss, https://b.example/rss")
    assert load_sources_from_env() == [
        "https://a.example/rss",
        "https://b.example/rss",
    ]


def test_load_sources_from_json_and_export_opml(tmp_path) -> None:
    json_path = tmp_path / "sources.json"
    json_path.write_text('["https://a.example/rss"]', encoding="utf-8")
    assert load_sources_from_file(str(json_path)) == ["https://a.example/rss"]
    opml_path = tmp_path / "sources.opml"
    export_opml(["https://a.example/rss"], str(opml_path))
    assert load_sources_from_file(str(opml_path)) == ["https://a.example/rss"]


def test_processor_fetch_and_process() -> None:
    xml = """
    <rss><channel><item><title>Test</title>
    <description><![CDATA[<p>Hello world</p>]]></description>
    </item></channel></rss>
    """
    pool = SourcePool()
    pool.add_source(RSSSource(url="https://a.example/rss"))
    processor = RSSProcessor(
        source_pool=pool,
        embed_fn=lambda text: [float(len(text))],
        summarize_fn=lambda text: text.upper(),
        opener=lambda url: xml,
    )
    events = processor.fetch_and_process("https://a.example/rss")
    assert len(events) == 1
    assert events[0]["title"] == "Test"
    assert events[0]["summary"] == "HELLO WORLD"
