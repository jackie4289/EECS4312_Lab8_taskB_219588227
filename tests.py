import pytest

from solution import EventRegistration, UserStatus, DuplicateRequest, NotFound


# Covers C1, C2, C9, AC1
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


# Covers C1, C2, C5, AC2, AC8
def test_cancel_registered_promotes_earliest_waitlisted_fifo():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist
    er.register("u3")  # waitlist

    result = er.cancel("u1")  # should promote u2

    assert result.state == "none"
    assert "promoted" in (result.message or "").lower()
    assert er.status("u1") == UserStatus("none")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]


# Covers C6, C7, AC3
def test_duplicate_register_raises_for_registered_and_waitlisted():
    er = EventRegistration(capacity=1)
    er.register("u1")
    with pytest.raises(DuplicateRequest):
        er.register("u1")

    er.register("u2")  # waitlisted
    with pytest.raises(DuplicateRequest):
        er.register("u2")


# Covers C7, AC12
def test_waitlisted_cancel_removes_and_updates_positions():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos1
    er.register("u3")  # waitlist pos2

    result = er.cancel("u2")  # remove from waitlist

    assert result == UserStatus("none")
    assert er.status("u2") == UserStatus("none")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u3"]


# Covers C7, AC7
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
# Additional tests to cover remaining acceptance criteria and edge cases.
#################################################################################


# Covers C8, C9, AC6
def test_status_for_registered_waitlisted_and_none():
    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")

    assert er.status("u1") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)
    assert er.status("unknown") == UserStatus("none")


# Covers C6, AC4
def test_cancel_nonexistent_user_raises_notfound():
    er = EventRegistration(capacity=1)

    with pytest.raises(NotFound):
        er.cancel("missing_user")


# Covers C3, C4, AC5
def test_repeating_same_operation_sequence_produces_same_final_state():
    er1 = EventRegistration(capacity=2)
    er2 = EventRegistration(capacity=2)

    ops = [
        ("register", "u1"),
        ("register", "u2"),
        ("register", "u3"),
        ("register", "u4"),
        ("cancel", "u1"),
        ("cancel", "u4"),
    ]

    for op, user in ops:
        getattr(er1, op)(user)
        getattr(er2, op)(user)

    assert er1.snapshot() == er2.snapshot()


# Covers C2, C10, AC11
def test_registered_cancellation_with_empty_waitlist_removes_user_without_promotion():
    er = EventRegistration(capacity=2)

    er.register("u1")
    result = er.cancel("u1")

    assert result.state == "none"
    assert "no promotion" in (result.message or "").lower()

    snap = er.snapshot()
    assert snap["registered"] == []
    assert snap["waitlist"] == []


# Covers C4, AC10
def test_operations_follow_deterministic_request_order():
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.register("u2")      # waitlisted
    er.cancel("u1")        # promotes u2
    er.register("u3")      # now waitlisted behind u2

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]


# Covers C5, AC9
def test_waitlist_result_includes_explanation():
    er = EventRegistration(capacity=1)

    er.register("u1")
    result = er.register("u2")

    assert result == UserStatus("waitlisted", 1)
    assert result.message is not None
    assert "waitlist" in result.message.lower()


# Covers C5, AC9
def test_registered_result_includes_explanation():
    er = EventRegistration(capacity=1)

    result = er.register("u1")

    assert result == UserStatus("registered")
    assert result.message is not None
    assert "registered" in result.message.lower()


# Covers C1, C2, C10, AC2, AC8
def test_multiple_promotions_after_multiple_cancellations():
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


# Covers C1, C8, AC6
def test_waitlist_positions_update_after_promotion():
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.register("u2")
    er.register("u3")

    er.cancel("u1")  # promote u2

    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)


# Covers C1, C10, AC1, AC2
def test_snapshot_state_consistency():
    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")

    snap = er.snapshot()

    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3"]


# Covers C7, supports edge case EC6
def test_reregister_after_cancellation():
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.cancel("u1")

    # user should be able to register again as a new request
    s = er.register("u1")
    assert s == UserStatus("registered")