import pytest

from solution import EventRegistration, UserStatus, DuplicateRequest, NotFound


def test_register_until_capacity_then_waitlist_fifo_positions():
    er = EventRegistration(capacity=2)

    s1 = er.register("u1")
    s2 = er.register("u2")
    s3 = er.register("u3")
    s4 = er.register("u4")

    assert s1 == UserStatus("registered")
    assert s2 == UserStatus("registered")
    assert s3 == UserStatus("waitlisted", 1)
    assert s4 == UserStatus("waitlisted", 2)

    snap = er.snapshot()
    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3", "u4"]


def test_cancel_registered_promotes_earliest_waitlisted_fifo():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist
    er.register("u3")  # waitlist

    er.cancel("u1")  # should promote u2

    assert er.status("u1") == UserStatus("none")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]


def test_duplicate_register_raises_for_registered_and_waitlisted():
    er = EventRegistration(capacity=1)
    er.register("u1")
    with pytest.raises(DuplicateRequest):
        er.register("u1")

    er.register("u2")  # waitlisted
    with pytest.raises(DuplicateRequest):
        er.register("u2")


def test_waitlisted_cancel_removes_and_updates_positions():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos1
    er.register("u3")  # waitlist pos2

    er.cancel("u2")    # remove from waitlist

    assert er.status("u2") == UserStatus("none")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u3"]


def test_capacity_zero_all_waitlisted_and_promotion_never_happens():
    er = EventRegistration(capacity=0)
    assert er.register("u1") == UserStatus("waitlisted", 1)
    assert er.register("u2") == UserStatus("waitlisted", 2)

    # No one can ever be registered when capacity=0
    assert er.status("u1") == UserStatus("waitlisted", 1)
    assert er.status("u2") == UserStatus("waitlisted", 2)
    assert er.snapshot()["registered"] == []

    # Cancel unknown should raise NotFound
    with pytest.raises(NotFound):
        er.cancel("missing")



#################################################################################
# Add your own additional tests here to cover more cases and edge cases as needed.
#################################################################################

def test_status_for_registered_waitlisted_and_none():
    # Validates C3: user exists in only one state
    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")

    assert er.status("u1") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)
    assert er.status("unknown") == UserStatus("none")


def test_reregister_after_cancellation():
    # Validates re-registration behavior
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.cancel("u1")

    # user should be able to register again
    s = er.register("u1")
    assert s == UserStatus("registered")


def test_cancel_nonexistent_user_raises_notfound():
    # Validates C3: operations on unknown users
    er = EventRegistration(capacity=1)

    with pytest.raises(NotFound):
        er.cancel("missing_user")


def test_multiple_promotions_after_multiple_cancellations():
    # Validates C5 and C6: FIFO promotion order
    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")
    er.register("u4")

    er.cancel("u1")  # promotes u3
    er.cancel("u2")  # promotes u4

    assert er.status("u3") == UserStatus("registered")
    assert er.status("u4") == UserStatus("registered")

    snap = er.snapshot()
    assert snap["registered"] == ["u3", "u4"]
    assert snap["waitlist"] == []


def test_waitlist_positions_update_after_promotion():
    # Validates waitlist position updates
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.register("u2")
    er.register("u3")

    er.cancel("u1")  # promote u2

    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)


def test_snapshot_state_consistency():
    # Validates invariant: system state remains consistent
    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")

    snap = er.snapshot()

    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3"]

def test_capacity_negative_raises_valueerror():
    # Validates Clarification: capacity must be int >= 0
    with pytest.raises(ValueError):
        EventRegistration(capacity=-1)


def test_capacity_non_int_raises_typeerror():
    # Validates Clarification: capacity must be an int (bool disallowed too)
    with pytest.raises(TypeError):
        EventRegistration(capacity="2")
    with pytest.raises(TypeError):
        EventRegistration(capacity=2.0)
    with pytest.raises(TypeError):
        EventRegistration(capacity=True)  # bool is a subclass of int


def test_register_empty_or_whitespace_userid_raises_valueerror():
    # Validates Clarification: user_id must be non-empty after stripping whitespace
    er = EventRegistration(capacity=1)

    with pytest.raises(ValueError):
        er.register("")
    with pytest.raises(ValueError):
        er.register("   ")
    with pytest.raises(ValueError):
        er.register("\n\t")


def test_register_non_string_userid_raises_typeerror():
    # Validates Clarification: user_id must be a string
    er = EventRegistration(capacity=1)

    with pytest.raises(TypeError):
        er.register(123)          # int
    with pytest.raises(TypeError):
        er.register(None)         # NoneType
    with pytest.raises(TypeError):
        er.register(["u1"])       # list


def test_cancel_invalid_userid_raises():
    # Validates Clarification: cancel validates user_id format before NotFound logic
    er = EventRegistration(capacity=1)

    with pytest.raises(ValueError):
        er.cancel("")
    with pytest.raises(ValueError):
        er.cancel("   ")
    with pytest.raises(TypeError):
        er.cancel(None)


def test_status_invalid_userid_raises():
    # Validates Clarification: status validates user_id format
    er = EventRegistration(capacity=1)

    with pytest.raises(ValueError):
        er.status("")
    with pytest.raises(ValueError):
        er.status("   ")
    with pytest.raises(TypeError):
        er.status(999)


def test_user_ids_are_case_sensitive():
    # Validates Clarification: user IDs are case-sensitive (Alice != alice)
    er = EventRegistration(capacity=2)

    s1 = er.register("Alice")
    s2 = er.register("alice")

    assert s1 == UserStatus("registered")
    assert s2 == UserStatus("registered")

    snap = er.snapshot()
    assert snap["registered"] == ["Alice", "alice"]


def test_deterministic_promotion_appends_to_end_of_registered():
    # Validates Clarification: registered list preserves order; promotion appends at end
    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")  # waitlisted

    er.cancel("u1")    # u3 promoted

    snap = er.snapshot()
    # u2 remains first; u3 appended
    assert snap["registered"] == ["u2", "u3"]
    assert snap["waitlist"] == []


def test_snapshot_returns_copies_not_live_lists():
    # Validates Clarification: snapshot() returns copies (external mutation shouldn't affect state)
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlisted

    snap = er.snapshot()
    snap["registered"].append("MUTATE")
    snap["waitlist"].clear()

    # Internal state should be unchanged
    snap2 = er.snapshot()
    assert snap2["registered"] == ["u1"]
    assert snap2["waitlist"] == ["u2"]
    
def test_stress_repeated_cancel_and_reregister_cycles():
    # Validates: consistent state after many operations, re-register allowed after cancel,
    # no duplicates, deterministic promotion behavior.
    er = EventRegistration(capacity=2)

    # Fill capacity + waitlist
    er.register("u1")
    er.register("u2")
    er.register("u3")
    er.register("u4")

    # Cycle: cancel a registered user, ensure FIFO promotion, then re-register canceled user
    er.cancel("u1")  # promotes u3
    assert er.snapshot()["registered"] == ["u2", "u3"]
    assert er.snapshot()["waitlist"] == ["u4"]

    er.register("u1")  # should go to waitlist (since capacity full)
    assert er.status("u1") == UserStatus("waitlisted", 2)
    assert er.snapshot()["waitlist"] == ["u4", "u1"]

    er.cancel("u2")  # promotes u4
    assert er.snapshot()["registered"] == ["u3", "u4"]
    assert er.snapshot()["waitlist"] == ["u1"]
    assert er.status("u2") == UserStatus("none")

    # Now re-register u2; should go to waitlist (capacity full)
    er.register("u2")
    assert er.snapshot()["waitlist"] == ["u1", "u2"]

    # Cancel u3 -> promote u1
    er.cancel("u3")
    assert er.snapshot()["registered"] == ["u4", "u1"]
    assert er.snapshot()["waitlist"] == ["u2"]

    # Cancel u4 -> promote u2
    er.cancel("u4")
    assert er.snapshot()["registered"] == ["u1", "u2"]
    assert er.snapshot()["waitlist"] == []

    # Ensure no duplicates and status consistent at end
    assert er.status("u1") == UserStatus("registered")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("none")
    assert er.status("u4") == UserStatus("none")


def test_stress_long_waitlist_middle_removals_and_fifo_promotions():
    # Validates: FIFO ordering under churn + correct position updates after removals/promotions
    er = EventRegistration(capacity=3)

    # Register 3, then waitlist 6
    er.register("r1")
    er.register("r2")
    er.register("r3")

    er.register("w1")
    er.register("w2")
    er.register("w3")
    er.register("w4")
    er.register("w5")
    er.register("w6")

    assert er.snapshot()["registered"] == ["r1", "r2", "r3"]
    assert er.snapshot()["waitlist"] == ["w1", "w2", "w3", "w4", "w5", "w6"]

    # Remove from middle of waitlist
    er.cancel("w3")
    assert er.snapshot()["waitlist"] == ["w1", "w2", "w4", "w5", "w6"]
    assert er.status("w4") == UserStatus("waitlisted", 3)

    # Cancel a registered user -> promote w1 (FIFO)
    er.cancel("r2")
    assert er.snapshot()["registered"] == ["r1", "r3", "w1"]
    assert er.snapshot()["waitlist"] == ["w2", "w4", "w5", "w6"]

    # Cancel another registered user -> promote w2
    er.cancel("r1")
    assert er.snapshot()["registered"] == ["r3", "w1", "w2"]
    assert er.snapshot()["waitlist"] == ["w4", "w5", "w6"]

    # Remove head of waitlist (w4) then cancel registered to promote next (w5)
    er.cancel("w4")
    assert er.snapshot()["waitlist"] == ["w5", "w6"]
    assert er.status("w5") == UserStatus("waitlisted", 1)

    er.cancel("r3")  # promote w5
    assert er.snapshot()["registered"] == ["w1", "w2", "w5"]
    assert er.snapshot()["waitlist"] == ["w6"]
    assert er.status("w6") == UserStatus("waitlisted", 1)

    # Final sanity: no removed users remain
    assert er.status("r1") == UserStatus("none")
    assert er.status("r2") == UserStatus("none")
    assert er.status("w3") == UserStatus("none")
    assert er.status("w4") == UserStatus("none")

def test_full_capacity_registration_adds_user_to_waitlist_with_position():
    er = EventRegistration(capacity=2)

    assert er.register("A") == UserStatus("registered")
    assert er.register("B") == UserStatus("registered")

    status = er.register("C")
    assert status == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["A", "B"]
    assert snap["waitlist"] == ["C"]


# Covers C1, C2, C5, AC2, AC8
def test_cancellation_promotes_earliest_waitlisted_user_fifo():
    er = EventRegistration(capacity=2)

    er.register("A")
    er.register("B")
    er.register("C")
    er.register("D")

    result = er.cancel("A")
    assert result.state == "none"
    assert "promoted" in (result.message or "").lower()

    snap = er.snapshot()
    assert snap["registered"] == ["B", "C"]
    assert snap["waitlist"] == ["D"]


# Covers C6, C7, AC3
def test_duplicate_registration_is_rejected_for_registered_and_waitlisted_users():
    er = EventRegistration(capacity=1)

    er.register("A")
    er.register("B")  # waitlisted

    with pytest.raises(DuplicateRequest):
        er.register("A")

    with pytest.raises(DuplicateRequest):
        er.register("B")


# Covers C6, C7, AC4
def test_cancelling_unknown_user_returns_not_found():
    er = EventRegistration(capacity=1)

    with pytest.raises(NotFound):
        er.cancel("missing-user")


# Covers C3, C4, AC5
def test_repeating_same_operation_sequence_produces_same_final_state():
    er1 = EventRegistration(capacity=2)
    er2 = EventRegistration(capacity=2)

    ops = [
        ("register", "A"),
        ("register", "B"),
        ("register", "C"),
        ("register", "D"),
        ("cancel", "A"),
        ("cancel", "D"),
    ]

    for op, user in ops:
        getattr(er1, op)(user)
        getattr(er2, op)(user)

    assert er1.snapshot() == er2.snapshot()


# Covers C8, C9, AC6
def test_waitlisted_status_returns_state_and_position():
    er = EventRegistration(capacity=1)

    er.register("A")
    er.register("B")
    er.register("C")

    assert er.status("B") == UserStatus("waitlisted", 1)
    assert er.status("C") == UserStatus("waitlisted", 2)


# Covers C7, AC7
def test_capacity_zero_never_registers_users_edge_case():
    er = EventRegistration(capacity=0)

    status = er.register("A")
    assert status == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == []
    assert snap["waitlist"] == ["A"]


# Covers C2, C10, AC11
def test_registered_cancellation_with_empty_waitlist_removes_user_without_promotion_edge_case():
    er = EventRegistration(capacity=2)

    er.register("A")
    result = er.cancel("A")

    assert result.state == "none"
    assert "no promotion" in (result.message or "").lower()

    snap = er.snapshot()
    assert snap["registered"] == []
    assert snap["waitlist"] == []


# Covers C7, AC12
def test_waitlisted_cancellation_removes_user_and_shifts_positions_edge_case():
    er = EventRegistration(capacity=1)

    er.register("A")
    er.register("B")
    er.register("C")
    er.register("D")

    result = er.cancel("C")
    assert result.state == "none"

    snap = er.snapshot()
    assert snap["registered"] == ["A"]
    assert snap["waitlist"] == ["B", "D"]

    assert er.status("B") == UserStatus("waitlisted", 1)
    assert er.status("D") == UserStatus("waitlisted", 2)


# Covers C4, AC10
def test_operations_follow_deterministic_request_order():
    er = EventRegistration(capacity=1)

    er.register("A")
    er.register("B")      # waitlisted
    er.cancel("A")        # promotes B
    er.register("C")      # now waitlisted behind B

    snap = er.snapshot()
    assert snap["registered"] == ["B"]
    assert snap["waitlist"] == ["C"]


# Covers C10, AC2, AC8
def test_multiple_cancellations_trigger_multiple_fifo_promotions():
    er = EventRegistration(capacity=2)

    er.register("A")
    er.register("B")
    er.register("C")
    er.register("D")
    er.register("E")

    er.cancel("A")
    er.cancel("B")

    snap = er.snapshot()
    assert snap["registered"] == ["C", "D"]
    assert snap["waitlist"] == ["E"]