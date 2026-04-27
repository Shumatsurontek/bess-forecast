import asyncio

import pytest

from bess_forecast.infrastructure.api.jobs import (
    DONE_SENTINEL,
    JobBus,
    JobBusProgressSink,
)


@pytest.mark.asyncio
async def test_publish_then_subscribe_replays_buffer():
    bus = JobBus()
    job = bus.new_job_id()
    bus.publish(job, {"stage": "loading_csv"})
    bus.publish(job, {"stage": "fitting"})

    q = await bus.subscribe(job)
    a = await q.get()
    b = await q.get()
    assert a["stage"] == "loading_csv"
    assert b["stage"] == "fitting"


@pytest.mark.asyncio
async def test_close_emits_done_sentinel():
    bus = JobBus()
    job = bus.new_job_id()
    q = await bus.subscribe(job)
    bus.close(job)
    item = await asyncio.wait_for(q.get(), timeout=1)
    assert item is DONE_SENTINEL


@pytest.mark.asyncio
async def test_progress_sink_publishes_through_bus():
    bus = JobBus()
    job = bus.new_job_id()
    sink = JobBusProgressSink(bus, job)
    sink.emit("loading_csv", "reading", pct=0.05, extra={"path": "x.csv"})
    sink.emit("done", pct=1.0)
    assert [e["stage"] for e in bus.buffer(job)] == ["loading_csv", "done"]
    assert bus.buffer(job)[0]["extra"] == {"path": "x.csv"}


@pytest.mark.asyncio
async def test_late_subscriber_after_close_gets_buffer_then_sentinel():
    bus = JobBus()
    job = bus.new_job_id()
    bus.publish(job, {"stage": "fitting"})
    bus.close(job)
    q = await bus.subscribe(job)
    first = await q.get()
    second = await q.get()
    assert first["stage"] == "fitting"
    assert second is DONE_SENTINEL
