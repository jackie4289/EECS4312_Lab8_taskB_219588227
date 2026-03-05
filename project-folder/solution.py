## Student Name: Jackie Lin
## Student ID: 219588227

"""
solution.py — Task B: Event Registration with Waitlist

This module implements a single-event registration system with a fixed capacity and a FIFO
waitlist.

Clarifications / assumptions (to resolve underspecified parts of the handout):
1) User IDs are case-sensitive and compared exactly as provided (no normalization).
2) Input validation:
   - capacity must be an int >= 0 (ValueError for negative, TypeError for non-int)
   - user_id must be a non-empty string after stripping whitespace (TypeError/ValueError)
3) Duplicate registration attempts (user already registered OR waitlisted) raise DuplicateRequest.
4) cancel(user_id) raises NotFound if the user is not currently registered or waitlisted.
5) Ordering is deterministic:
   - registered list preserves insertion order; promotions append to the end
   - waitlist is FIFO; promotions always pop from the front
6) Re-registration is allowed after a user cancels (they are removed from the system).

Public API:
- EventRegistration(capacity)
- register(user_id) -> UserStatus
- cancel(user_id) -> None
- status(user_id) -> UserStatus
- snapshot() -> dict with keys: "registered", "waitlist"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set, Dict


class DuplicateRequest(Exception):
    """Raised if a user tries to register but is already registered or waitlisted."""


class NotFound(Exception):
    """Raised if a user cannot be found for cancellation."""


@dataclass(frozen=True)
class UserStatus:
    """
    state:
      - "registered"
      - "waitlisted"
      - "none"
    position: 1-based waitlist position if waitlisted; otherwise None
    """
    state: str
    position: Optional[int] = None


class EventRegistration:
    """Event registration system with FIFO waitlist and deterministic behavior."""

    def __init__(self, capacity: int) -> None:
        """Initialize a new registration system.

        Args:
            capacity: maximum number of registered users (int >= 0)

        Raises:
            TypeError: if capacity is not an int
            ValueError: if capacity < 0
        """
        # bool is a subclass of int; treat it as invalid here.
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be >= 0")

        self.capacity: int = capacity
        self._registered: List[str] = []
        self._waitlist: List[str] = []
        # Track current membership for fast duplicate checks.
        self._users: Set[str] = set()

    @staticmethod
    def _validate_user_id(user_id: str) -> None:
        if not isinstance(user_id, str):
            raise TypeError("user_id must be a str")
        if user_id.strip() == "":
            raise ValueError("user_id must be a non-empty string")

    def _assert_invariants(self) -> None:
        """Debug-only invariant checks."""
        assert len(self._registered) <= self.capacity
        assert len(self._registered) == len(set(self._registered))
        assert len(self._waitlist) == len(set(self._waitlist))
        assert set(self._registered).isdisjoint(set(self._waitlist))
        assert self._users == set(self._registered) | set(self._waitlist)

    def register(self, user_id: str) -> UserStatus:
        """Register a user.

        - If capacity available -> registered
        - Else -> waitlisted (FIFO)

        Raises:
            DuplicateRequest if user already exists (registered or waitlisted)
        """
        self._validate_user_id(user_id)

        if user_id in self._users:
            raise DuplicateRequest(f"{user_id} is already registered or waitlisted")

        if len(self._registered) < self.capacity:
            self._registered.append(user_id)
            self._users.add(user_id)
            self._assert_invariants()
            return UserStatus("registered")

        # Full (including capacity == 0)
        self._waitlist.append(user_id)
        self._users.add(user_id)
        self._assert_invariants()
        return UserStatus("waitlisted", len(self._waitlist))

    def cancel(self, user_id: str) -> None:
        """Cancel a user's registration or waitlist entry.

        - If registered -> remove and promote earliest waitlisted user (if any and if capacity allows)
        - If waitlisted -> remove from waitlist
        - If not found -> raise NotFound

        Raises:
            NotFound if user does not exist in the system
        """
        self._validate_user_id(user_id)

        if user_id in self._registered:
            self._registered.remove(user_id)
            self._users.remove(user_id)

            # Promote FIFO if a slot is available
            if self._waitlist and len(self._registered) < self.capacity:
                promoted = self._waitlist.pop(0)
                # promoted user stays in _users; we only move them between lists
                self._registered.append(promoted)

            self._assert_invariants()
            return

        if user_id in self._waitlist:
            self._waitlist.remove(user_id)
            self._users.remove(user_id)
            self._assert_invariants()
            return

        raise NotFound(f"{user_id} not found")

    def status(self, user_id: str) -> UserStatus:
        """Return status of a user.

        Returns:
          - registered
          - waitlisted with 1-based position
          - none
        """
        self._validate_user_id(user_id)

        if user_id in self._registered:
            return UserStatus("registered")
        if user_id in self._waitlist:
            return UserStatus("waitlisted", self._waitlist.index(user_id) + 1)
        return UserStatus("none")

    def snapshot(self) -> Dict[str, List[str]]:
        """Return a deterministic snapshot of internal state."""
        return {"registered": list(self._registered), "waitlist": list(self._waitlist)}