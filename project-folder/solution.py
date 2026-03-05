## Student Name:
## Student ID:

"""
Task B: Event Registration with Waitlist (Stub)
In this lab, you will design and implement an Event Registration with Waitlist system using an LLM assistant as your primary programming collaborator. 
You are asked to implement a Python module that manages registration for a single event with a fixed capacity. 
The system must:
•	Accept a fixed capacity.
•	Register users until capacity is reached.
•	Place additional users into a FIFO waitlist.
•	Automatically promote the earliest waitlisted user when a registered user cancels.
•	Prevent duplicate registrations.
•	Allow users to query their current status.

The system must ensure that:
•	The number of registered users never exceeds capacity.
•	Waitlist ordering preserves FIFO behavior.
•	Promotions occur deterministically under identical operation sequences.

The module must preserve the following invariants:
•	A user may not appear more than once in the system.
•	A user may not simultaneously exist in multiple states.
•	The system state must remain consistent after every operation.

The system must correctly handle non-trivial scenarios such as:
•	Multiple cancellations in sequence.
•	Users attempting to re-register after canceling.
•	Waitlisted users canceling before promotion.
•	Capacity equal to zero.
•	Simultaneous or rapid consecutive operations.
•	Queries during state transitions.

The output consists of the updated registration state and ordered lists of registered and waitlisted users after each operation.
"""

from dataclasses import dataclass
from typing import List, Optional


class DuplicateRequest(Exception):
    """Raised if a user tries to register but is already registered or waitlisted."""
    pass


class NotFound(Exception):
    """Raised if a user cannot be found for cancellation (if required by handout)."""
    pass


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
    """
    Students must implement this class per the lab handout.
    Deterministic ordering is required (e.g., FIFO waitlist, predictable registration order).
    """

    def __init__(self, capacity: int) -> None:
        """
        Args:
            capacity: maximum number of registered users (>= 0)
        """
        # TODO: Initialize internal data structures
        raise NotImplementedError("EventRegistration.__init__ not implemented yet")

    def register(self, user_id: str) -> UserStatus:
        """
        Register a user:
          - if capacity available -> registered
          - else -> waitlisted (FIFO)

        Raises:
            DuplicateRequest if user already exists (registered or waitlisted)
        """
        # TODO: Implement per lab handout
        raise NotImplementedError("register not implemented yet")

    def cancel(self, user_id: str) -> None:
        """
        Cancel a user:
          - if registered -> remove and promote earliest waitlisted user (if any)
          - if waitlisted -> remove from waitlist
          - behavior when user not found depends on handout (raise NotFound or ignore)

        Raises:
            NotFound (if required by handout)
        """
        # TODO: Implement per lab handout
        raise NotImplementedError("cancel not implemented yet")

    def status(self, user_id: str) -> UserStatus:
        """
        Return status of a user:
          - registered
          - waitlisted with position (1-based)
          - none
        """
        # TODO: Implement per lab handout
        raise NotImplementedError("status not implemented yet")

    def snapshot(self) -> dict:
        """
        (Optional helper for debugging/tests)
        Return a deterministic snapshot of internal state.
        """
        # TODO: Implement if required/allowed
        raise NotImplementedError("snapshot not implemented yet")