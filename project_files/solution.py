## Student Name: Jackie Lin
## Student ID: 219588227

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class DuplicateRequest(Exception):
    """Raised when a user tries to register but is already registered or waitlisted."""
    pass


class NotFound(Exception):
    """Raised when a user cannot be found for cancellation."""
    pass


@dataclass(frozen=True)
class UserStatus:
    """
    state:
      - "registered"
      - "waitlisted"
      - "none"

    position:
      1-based waitlist position if waitlisted; otherwise None

    message:
      Optional explanation. Excluded from equality checks to keep status
      comparisons compatible with tests that only care about state/position.
    """
    state: str
    position: Optional[int] = None
    message: Optional[str] = field(default=None, compare=False)


class EventRegistration:
    """
    Single-event registration system with:
    - fixed capacity
    - FIFO waitlist
    - automatic promotion on cancellation
    - duplicate prevention
    - deterministic snapshot output
    """

    def __init__(self, capacity: int) -> None:
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be >= 0")

        self.capacity: int = capacity
        self._registered: List[str] = []
        self._waitlist: List[str] = []

    def _validate_user_id(self, user_id: str) -> None:
        if not isinstance(user_id, str):
            raise TypeError("user_id must be a string")
        if user_id.strip() == "":
            raise ValueError("user_id must be non-empty")

    def _exists(self, user_id: str) -> bool:
        return user_id in self._registered or user_id in self._waitlist

    def _promote_if_possible(self) -> Optional[str]:
        """
        Promote the earliest waitlisted user if there is free capacity.
        Returns the promoted user_id, or None if no promotion occurs.
        """
        if len(self._registered) < self.capacity and self._waitlist:
            promoted = self._waitlist.pop(0)
            self._registered.append(promoted)
            return promoted
        return None

    def register(self, user_id: str) -> UserStatus:
        """
        Register a user.
        - If capacity is available, user becomes registered.
        - Otherwise, user is placed on the waitlist.

        Raises:
            DuplicateRequest: if already registered or waitlisted
            TypeError / ValueError: for invalid user_id
        """
        self._validate_user_id(user_id)

        if self._exists(user_id):
            raise DuplicateRequest(f"user '{user_id}' is already registered or waitlisted")

        if len(self._registered) < self.capacity:
            self._registered.append(user_id)
            return UserStatus(
                state="registered",
                message="Registered successfully."
            )

        self._waitlist.append(user_id)
        position = len(self._waitlist)
        return UserStatus(
            state="waitlisted",
            position=position,
            message=f"Event is full. Added to waitlist at position {position}."
        )

    def cancel(self, user_id: str) -> UserStatus:
        """
        Cancel a registered or waitlisted user.

        If a registered user cancels, the earliest waitlisted user is promoted.

        Raises:
            NotFound: if the user is neither registered nor waitlisted
            TypeError / ValueError: for invalid user_id
        """
        self._validate_user_id(user_id)

        if user_id in self._registered:
            self._registered.remove(user_id)
            promoted = self._promote_if_possible()

            if promoted is None:
                return UserStatus(
                    state="none",
                    message="Registration canceled. No promotion occurred."
                )

            return UserStatus(
                state="none",
                message=(
                    f"Registration canceled. Waitlisted user '{promoted}' "
                    f"was promoted to registered."
                )
            )

        if user_id in self._waitlist:
            self._waitlist.remove(user_id)
            return UserStatus(
                state="none",
                message="Waitlist entry canceled."
            )

        raise NotFound(f"user '{user_id}' was not found")

    def status(self, user_id: str) -> UserStatus:
        """
        Return the user's current status.

        Raises:
            TypeError / ValueError: for invalid user_id
        """
        self._validate_user_id(user_id)

        if user_id in self._registered:
            return UserStatus(
                state="registered",
                message="User is currently registered."
            )

        if user_id in self._waitlist:
            position = self._waitlist.index(user_id) + 1
            return UserStatus(
                state="waitlisted",
                position=position,
                message=f"User is waitlisted at position {position}."
            )

        return UserStatus(
            state="none",
            message="User is not registered or waitlisted."
        )

    def snapshot(self) -> Dict[str, List[str]]:
        """
        Return a deterministic snapshot of the current state.

        The returned lists are copies, not live internal references.
        """
        return {
            "registered": list(self._registered),
            "waitlist": list(self._waitlist),
        }