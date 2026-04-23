import asyncio

from app.api.v1.analytics import BatchTrackRequest, TrackEventRequest, get_dashboard, get_events, get_funnel, track_batch, track_event


def test_track_event_returns_success_payload():
    async def run_test():
        request = TrackEventRequest(eventName="page_view", metadata={"page": "dh-list"})
        response = await track_event(request)

        assert response.code == 0
        assert response.message == "success"
        assert response.data["accepted"] is True
        assert response.data["eventName"] == "page_view"
        assert "receivedAt" in response.data

    asyncio.run(run_test())


def test_track_batch_returns_event_count():
    async def run_test():
        request = BatchTrackRequest(
            events=[
                TrackEventRequest(eventName="page_view"),
                TrackEventRequest(eventName="button_click", metadata={"target": "retry"}),
            ]
        )

        response = await track_batch(request)

        assert response.code == 0
        assert response.data["accepted"] is True
        assert response.data["count"] == 2

    asyncio.run(run_test())


def test_dashboard_and_events_default_to_empty_collections():
    async def run_test():
        dashboard = await get_dashboard()
        events = await get_events()
        funnel = await get_funnel()

        assert dashboard.code == 0
        assert dashboard.data["dailyStats"] == []
        assert dashboard.data["eventStats"] == {}
        assert events.data["events"] == []
        assert events.data["total"] == 0
        assert funnel.data["steps"] == []

    asyncio.run(run_test())
