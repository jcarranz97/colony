from datetime import date
from decimal import Decimal

import pytest

from app.activity import models as activity_models
from app.activity.constants import ActivityAction, EntityType
from app.activity.exceptions import (
    CommentDeleteForbiddenExceptionError,
    CommentNotAuthorExceptionError,
    InvalidEntityTypeExceptionError,
)
from app.activity.helpers import compute_diff
from app.activity.service import activity_service, comment_service
from app.cycles.constants import CycleStatus
from app.cycles.models import Cycle
from app.payment_methods import schemas as pm_schemas
from app.payment_methods.constants import CurrencyCode, PaymentMethodType
from app.payment_methods.service import payment_method_service


class TestComputeDiff:
    def test_returns_empty_when_no_changes(self):
        before = {"name": "A", "amount": Decimal("10.00")}
        assert compute_diff(before, dict(before)) == {}

    def test_detects_string_change(self):
        diff = compute_diff({"name": "old"}, {"name": "new"})
        assert diff == {"name": {"from": "old", "to": "new"}}

    def test_serializes_decimals_and_dates(self):
        before = {"amount": Decimal("10.00"), "due_date": date(2025, 1, 1)}
        after = {"amount": Decimal("20.00"), "due_date": date(2025, 2, 1)}
        diff = compute_diff(before, after)
        assert diff["amount"] == {"from": "10.00", "to": "20.00"}
        assert diff["due_date"] == {"from": "2025-01-01", "to": "2025-02-01"}


class TestActivityServiceRecord:
    def test_persists_an_activity_row(self, db, test_household, test_user):
        entity_id = test_household.id  # any uuid is fine for the test
        activity_service.record(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=entity_id,
            actor_user_id=test_user.id,
            action=ActivityAction.CREATED,
        )
        db.commit()
        rows = (
            db.query(activity_models.ActivityLog)
            .filter(activity_models.ActivityLog.entity_id == entity_id)
            .all()
        )
        assert len(rows) == 1
        assert rows[0].action == "created"
        assert rows[0].actor_user_id == test_user.id

    def test_list_for_cycle_includes_child_entity_events(
        self, db, test_household, test_user, test_payment_method
    ):
        # Create a cycle, then record events on it AND on a "child" entity
        # (here, the payment method, with cycle_id denormalized as a stand-in).
        cycle = Cycle(
            household_id=test_household.id,
            name="Cycle A",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            remaining_balance=Decimal("0"),
            status=CycleStatus.ACTIVE,
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)

        activity_service.record(
            db,
            household_id=test_household.id,
            entity_type=EntityType.CYCLE,
            entity_id=cycle.id,
            cycle_id=cycle.id,
            actor_user_id=test_user.id,
            action=ActivityAction.CREATED,
        )
        activity_service.record(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            cycle_id=cycle.id,
            actor_user_id=test_user.id,
            action=ActivityAction.UPDATED,
            changes={"name": {"from": "X", "to": "Y"}},
        )
        db.commit()

        cycle_events = activity_service.list_for_cycle(
            db, household_id=test_household.id, cycle_id=cycle.id
        )
        assert len(cycle_events) == 2
        # Newest first
        assert cycle_events[0].action == "updated"


class TestPaymentMethodActivity:
    """Activity recording is triggered by service mutations end-to-end."""

    def test_create_records_created(self, db, test_household, test_user):
        data = pm_schemas.PaymentMethodCreate(
            name="My Card",
            method_type=PaymentMethodType.DEBIT,
            default_currency=CurrencyCode.USD,
            description=None,
            last_4_digits=None,
        )
        pm = payment_method_service.create_payment_method(
            db, data, str(test_household.id), actor=test_user
        )
        events = activity_service.list_for_entity(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=pm.id,
        )
        assert len(events) == 1
        assert events[0].action == "created"
        assert events[0].actor_user_id == test_user.id

    def test_rename_records_updated_with_diff(
        self, db, test_household, test_payment_method, test_user
    ):
        data = pm_schemas.PaymentMethodUpdate.model_validate({"name": "Renamed"})
        payment_method_service.update_payment_method(
            db, test_payment_method, data, actor=test_user
        )
        events = activity_service.list_for_entity(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
        )
        assert len(events) == 1
        assert events[0].action == "updated"
        assert "name" in events[0].changes
        assert events[0].changes["name"]["to"] == "Renamed"

    def test_soft_delete_records_deactivated(
        self, db, test_household, test_payment_method, test_user
    ):
        payment_method_service.delete_payment_method(
            db, test_payment_method, actor=test_user
        )
        events = activity_service.list_for_entity(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
        )
        assert len(events) == 1
        assert events[0].action == "deactivated"


class TestCommentService:
    def test_create_persists_comment_and_records_activity(
        self, db, test_household, test_payment_method, test_user
    ):
        comment = comment_service.create(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            body="**bold** body",
            actor=test_user,
        )
        assert comment.body == "**bold** body"
        assert comment.active is True

        events = activity_service.list_for_entity(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
        )
        assert any(e.action == "commented" for e in events)

    def test_create_rejects_invalid_entity_type(
        self, db, test_household, test_payment_method, test_user
    ):
        with pytest.raises(InvalidEntityTypeExceptionError):
            comment_service.create(
                db,
                household_id=test_household.id,
                entity_type=EntityType.COMMENT,  # not commentable
                entity_id=test_payment_method.id,
                body="x",
                actor=test_user,
            )

    def test_update_by_author_succeeds(
        self, db, test_household, test_payment_method, test_user
    ):
        comment = comment_service.create(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            body="first",
            actor=test_user,
        )
        updated = comment_service.update(
            db, comment=comment, body="second", actor=test_user
        )
        assert updated.body == "second"
        assert updated.edited_at is not None

    def test_update_by_non_author_forbidden(
        self,
        db,
        test_household,
        test_payment_method,
        test_user,
        other_user,
    ):
        comment = comment_service.create(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            body="mine",
            actor=test_user,
        )
        with pytest.raises(CommentNotAuthorExceptionError):
            comment_service.update(
                db, comment=comment, body="hostile", actor=other_user
            )

    def test_delete_by_author_soft_deletes(
        self, db, test_household, test_payment_method, test_user
    ):
        comment = comment_service.create(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            body="to delete",
            actor=test_user,
        )
        comment_service.soft_delete(db, comment=comment, actor=test_user)
        db.refresh(comment)
        assert comment.active is False

        # Soft-deleted comments are filtered out of list endpoints.
        live = comment_service.list_for_entity(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
        )
        assert all(c.id != comment.id for c in live)

    def test_delete_by_admin_succeeds(
        self, db, test_household, test_payment_method, test_user, admin_user
    ):
        comment = comment_service.create(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            body="moderate me",
            actor=test_user,
        )
        comment_service.soft_delete(db, comment=comment, actor=admin_user)
        db.refresh(comment)
        assert comment.active is False

    def test_delete_by_other_user_forbidden(
        self, db, test_household, test_payment_method, test_user, other_user
    ):
        comment = comment_service.create(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            body="mine",
            actor=test_user,
        )
        with pytest.raises(CommentDeleteForbiddenExceptionError):
            comment_service.soft_delete(db, comment=comment, actor=other_user)

    def test_markdown_body_roundtrips_unmodified(
        self, db, test_household, test_payment_method, test_user
    ):
        body = "## Heading\n\n- item 1\n- item 2\n\n[link](https://x.test)"
        comment = comment_service.create(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            body=body,
            actor=test_user,
        )
        assert comment.body == body
