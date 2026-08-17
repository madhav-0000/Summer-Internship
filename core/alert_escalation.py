import time
from collections import deque

class AlertEscalation:
    """
    Two-tier alert escalation system.
    
    Tier 1: Individual events (yawn, eye closure, nod, distraction) are detected
            by their respective trackers and recorded here as timestamped events.
    Tier 2: An alarm only fires when N events accumulate within a sliding time
            window of T seconds. Once armed, subsequent events trigger immediately.
            The category disarms after a cooldown period with no new events.
    """

    # Default escalation profiles per category
    DEFAULT_PROFILES = {
        "yawn":        {"events_required": 3, "window_seconds": 45, "cooldown_seconds": 45},
        "eye_closure": {"events_required": 2, "window_seconds": 25, "cooldown_seconds": 25},
        "head_nod":    {"events_required": 2, "window_seconds": 30, "cooldown_seconds": 30},
        "distraction": {"events_required": 3, "window_seconds": 45, "cooldown_seconds": 45},
    }

    def __init__(self, profiles=None):
        """
        Initialize the escalation system.
        
        Args:
            profiles: Optional dict overriding DEFAULT_PROFILES.
                      Keys are category names, values are dicts with
                      'events_required', 'window_seconds', 'cooldown_seconds'.
        """
        self.profiles = dict(self.DEFAULT_PROFILES)
        if profiles:
            for category, overrides in profiles.items():
                if category in self.profiles:
                    self.profiles[category].update(overrides)
                else:
                    self.profiles[category] = overrides

        # Per-category state
        self._event_times = {}   # category -> deque of event timestamps
        self._armed = {}         # category -> bool (escalated / armed)
        self._last_event = {}    # category -> timestamp of last event (for cooldown)

        for category in self.profiles:
            self._event_times[category] = deque()
            self._armed[category] = False
            self._last_event[category] = 0.0

    def record_event(self, category):
        """
        Record that an event just occurred in the given category.
        Call this once per event (on the rising edge), not every frame.
        """
        now = time.time()
        self._event_times[category].append(now)
        self._last_event[category] = now

    def should_alert(self, category):
        """
        Check whether the given category should trigger an alarm right now.
        
        Returns True if:
          - The category is armed (N events within T seconds), OR
          - The category just became armed this check
        """
        profile = self.profiles[category]
        now = time.time()
        window = profile["window_seconds"]
        events_required = profile["events_required"]

        # Prune old events outside the time window
        events = self._event_times[category]
        while events and (now - events[0]) > window:
            events.popleft()

        # Check if we have enough events to arm
        if len(events) >= events_required:
            self._armed[category] = True

        return self._armed[category]

    def update(self, category):
        """
        Call every frame to handle cooldown logic.
        Disarms the category if no events occurred within the cooldown period.
        """
        profile = self.profiles[category]
        now = time.time()
        cooldown = profile["cooldown_seconds"]
        last = self._last_event[category]

        if self._armed[category] and last > 0 and (now - last) > cooldown:
            self._armed[category] = False
            # Also clear the event history so it starts fresh
            self._event_times[category].clear()

    def is_armed(self, category):
        """Returns whether the given category is currently armed."""
        return self._armed[category]

    def get_event_count(self, category):
        """
        Returns the number of events currently in the sliding window
        for the given category.
        """
        profile = self.profiles[category]
        now = time.time()
        window = profile["window_seconds"]
        events = self._event_times[category]

        # Prune old events
        while events and (now - events[0]) > window:
            events.popleft()

        return len(events)

    def get_events_required(self, category):
        """Returns the events_required threshold for a category."""
        return self.profiles[category]["events_required"]

    def reset(self, category=None):
        """
        Reset escalation state. If category is None, resets all categories.
        """
        categories = [category] if category else list(self.profiles.keys())
        for cat in categories:
            self._event_times[cat].clear()
            self._armed[cat] = False
            self._last_event[cat] = 0.0
