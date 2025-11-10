"""Calendar and scheduling tools (simulated)."""

from datetime import datetime, timedelta
from typing import Any


def get_available_slots(days_ahead: int = 7) -> list[dict[str, str]]:
    """Get available appointment slots.

    Args:
        days_ahead: Number of days ahead to show availability

    Returns:
        List of available time slots
    """
    slots = []
    start_date = datetime.now() + timedelta(days=1)  # Start from tomorrow

    for day in range(days_ahead):
        current_date = start_date + timedelta(days=day)

        # Skip weekends
        if current_date.weekday() >= 5:
            continue

        # Morning slots (9 AM - 12 PM)
        for hour in [9, 10, 11]:
            slots.append(
                {
                    "slot_id": f"SLOT-{current_date.strftime('%Y%m%d')}-{hour:02d}00",
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": f"{hour:02d}:00",
                    "datetime_str": f"{current_date.strftime('%A, %B %d')} at {hour}:00 AM",
                }
            )

        # Afternoon slots (2 PM - 5 PM)
        for hour in [14, 15, 16]:
            display_hour = hour - 12
            slots.append(
                {
                    "slot_id": f"SLOT-{current_date.strftime('%Y%m%d')}-{hour:02d}00",
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": f"{hour:02d}:00",
                    "datetime_str": f"{current_date.strftime('%A, %B %d')} at {display_hour}:00 PM",
                }
            )

    return slots[:15]  # Return first 15 slots


def schedule_appointment(
    slot_id: str,
    contact_method: str,
    contact_value: str,
    issue_summary: str,
    user_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Schedule an appointment with a live agent.

    Args:
        slot_id: The selected time slot ID
        contact_method: How to contact (phone/email)
        contact_value: Phone number or email address
        issue_summary: Brief summary of the issue
        user_context: Additional user context

    Returns:
        Confirmation details
    """
    # Find the slot details
    available_slots = get_available_slots(days_ahead=14)
    selected_slot = None

    for slot in available_slots:
        if slot["slot_id"] == slot_id:
            selected_slot = slot
            break

    if not selected_slot:
        return {
            "error": "Invalid slot",
            "message": "The selected time slot is no longer available. Please choose another slot.",
        }

    # Generate confirmation number
    confirmation_number = f"CONF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return {
        "confirmation_number": confirmation_number,
        "scheduled_datetime": selected_slot["datetime_str"],
        "contact_method": contact_method,
        "contact_value": contact_value,
        "issue_summary": issue_summary,
        "policy_id": user_context.get("policy_id") if user_context else None,
        "message": (
            f"Your appointment has been scheduled for {selected_slot['datetime_str']}. "
            f"A live agent will contact you via {contact_method} at {contact_value}. "
            f"Your confirmation number is {confirmation_number}."
        ),
    }


def cancel_appointment(confirmation_number: str) -> dict[str, Any]:
    """Cancel a scheduled appointment.

    Args:
        confirmation_number: The confirmation number of the appointment

    Returns:
        Cancellation confirmation
    """
    # In a real system, this would check if the appointment exists
    return {
        "confirmation_number": confirmation_number,
        "status": "cancelled",
        "message": f"Appointment {confirmation_number} has been cancelled successfully.",
    }
