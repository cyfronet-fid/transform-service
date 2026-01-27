"""Handling live update for trainings and interoperability guidelines"""

import json
import logging

from app.services.solr.validate.endpoints.validate import check_document_exists
from app.settings import settings
from app.tasks.solr.delete_data_by_id import delete_data_by_id
from app.tasks.transform.batch import transform_batch

APPROVED_TRAINING_STATUS = "approved resource"
APPROVED_GUIDELINE_STATUS = "approved interoperability record"
APPROVED_ADAPTER_STATUS = "approved adapter"
APPROVED_STATUSES = (
    APPROVED_TRAINING_STATUS,
    APPROVED_GUIDELINE_STATUS,
    APPROVED_ADAPTER_STATUS,
)
logger = logging.getLogger(__name__)


def process_message(frame_or_data, ack_id_or_subscription=None) -> None:
    """
    Processes incoming messages from both JMS (STOMP) and AMS.

    AMS sends: JSON string or dict with the data, plus ack_id containing subscription info
    STOMP sends: Frame object with .headers and .body

    Args:
        frame_or_data: Either a STOMP frame object or a JSON string/dict from AMS
        ack_id_or_subscription: Optional ack_id from AMS (contains subscription name)
                               Format: projects/{project}/subscriptions/{subscription_name}:{message_id}
    """
    # Determine if this is a STOMP frame or AMS data
    if hasattr(frame_or_data, "headers") and hasattr(frame_or_data, "body"):
        # STOMP/JMS message
        _process_stomp_message(frame_or_data)
    else:
        # AMS message (string or dict)
        _process_ams_message(frame_or_data, ack_id_or_subscription)


def _process_stomp_message(frame) -> None:
    """Process STOMP/JMS format messages"""
    action = frame.headers["destination"].split(".")[-1]
    if settings.STOMP_TOPIC_PREFIX:
        raw_collection = frame.headers["destination"].split("/")[-1].split(".")[-2]
    else:
        raw_collection = frame.headers["destination"].split("/")[-1].split(".")[0]

    frame_body = json.loads(frame.body)

    active = frame_body["active"]
    suspended = frame_body["suspended"]
    status = frame_body["status"]

    collection, data, data_id = extract_data_from_frame(raw_collection, frame_body)
    logger.info(
        f"Started to process STOMP message, type: {raw_collection}, id: {data_id}"
    )

    if action == "create":
        handle_create_action(active, suspended, status, collection, data, data_id)
    elif action == "update":
        handle_update_action(active, suspended, status, collection, data, data_id)
    elif action == "delete":
        handle_delete_action(collection, data_id, data)


def _process_ams_message(message_data, ack_id=None) -> None:
    """Process AMS format messages"""
    # Parse if it's a string
    if isinstance(message_data, str):
        try:
            frame_body = json.loads(message_data)
        except json.JSONDecodeError:
            logger.error(f"[AMS] Failed to parse message as JSON: {message_data[:100]}")
            return
    else:
        frame_body = message_data

    # Extract subscription name from ack_id
    # Format: projects/{project}/subscriptions/{subscription_name}:{message_id}
    # Example: projects/eosc-beyond-providers/subscriptions/transformer-adapter-update:22
    subscription_name = None
    if ack_id:
        try:
            subscription_name = ack_id.split("/subscriptions/")[1].split(":")[0]
            logger.info(
                f"[AMS] Extracted subscription name from ack_id: {subscription_name}"
            )
        except (IndexError, AttributeError):
            logger.warning(
                f"[AMS] Failed to extract subscription name from ack_id: {ack_id}"
            )

    # Extract action and resource type from subscription name
    # Format: transformer-{resource}-{action}
    # Examples: transformer-adapter-update, transformer-training_resource-create
    raw_collection = None
    action = None

    if subscription_name:
        # Parse subscription name: "transformer-adapter-update" -> action="update", resource="adapter"
        parts = subscription_name.split("-")
        if len(parts) >= 3:
            action = parts[-1]  # Last part is the action (create/update/delete)
            # Everything between "transformer-" and the action is the resource
            raw_collection = "-".join(
                parts[1:-1]
            )  # Handles multi-part names like "training_resource"
            logger.info(
                f"[AMS] Extracted from subscription: action={action}, resource={raw_collection}"
            )

    # Fallback: determine resource type from message content if subscription parsing failed
    if not raw_collection:
        if "adapter" in frame_body:
            raw_collection = "adapter"
        elif "interoperabilityRecord" in frame_body:
            raw_collection = "interoperability_record"
        elif "trainingResource" in frame_body:
            raw_collection = "training_resource"
        else:
            logger.warning(
                f"[AMS] Could not determine resource type from message: {list(frame_body.keys())}"
            )
            return

    # Fallback: if action still not determined, assume update
    if not action:
        logger.warning(
            f"[AMS] Could not determine action from subscription name, assuming 'update'"
        )
        action = "update"

    active = frame_body.get("active", True)
    suspended = frame_body.get("suspended", False)
    status = frame_body.get("status", "")

    collection, data, data_id = extract_data_from_frame(raw_collection, frame_body)
    logger.info(
        f"Started to process AMS message, type: {raw_collection}, id: {data_id}, action: {action}"
    )

    if action == "create":
        handle_create_action(active, suspended, status, collection, data, data_id)
    elif action == "update":
        handle_update_action(active, suspended, status, collection, data, data_id)
    elif action == "delete":
        handle_delete_action(collection, data_id, data)
    else:
        logger.warning(f"[AMS] Unknown action: {action}")


def extract_data_from_frame(raw_collection, frame_body):
    """
    Extracts data and collection information from the frame body.

    Args:
        raw_collection (str): The collection type from the message.
        frame_body (dict): The body of the message containing the data.

    Returns:
        tuple: Returns a tuple containing collection, data, and data_id.
    """
    if raw_collection == "training_resource":
        collection = settings.TRAINING
        data = frame_body["trainingResource"]
        data_id = data["id"]
    elif raw_collection == "interoperability_record":
        collection = settings.GUIDELINE
        data = [frame_body["interoperabilityRecord"]]
        data_id = data[0]["id"]
    elif raw_collection == "adapter":
        logger.info(f"{frame_body['adapter']=}")
        collection = settings.ADAPTER
        data = [frame_body["adapter"]]
        data_id = data[0]["id"]
    else:
        collection = raw_collection
        data = None
        data_id = None

    return collection, data, data_id


def handle_create_action(active, suspended, status, collection, data, data_id):
    """
    Handles the 'create' action for the message.

    Args:
        active (bool): Flag indicating if the record is active.
        suspended (bool): Flag indicating if the record is suspended.
        status (str): The status of the record.
        collection (str): The name of the collection.
        data (dict): The data to be processed.
        data_id (str): The ID of the data.
    """
    if active and not suspended and status in APPROVED_STATUSES:
        logger.info(f"Creating action - {collection=}, ID: {data_id}")
        transform_batch.delay(collection, data, full_update=False)
    else:
        logger.info(
            f"Aborting create action {collection=}, {data_id=}. Not active or suspended or status not approved."
        )


def handle_update_action(active, suspended, status, collection, data, data_id):
    """
    Handles the 'update' action for the message.

    Args:
        active (bool): Flag indicating if the record is active.
        suspended (bool): Flag indicating if the record is suspended.
        status (str): The status of the record.
        collection (str): The name of the collection.
        data (dict): The data to be processed.
        data_id (str): The ID of the data.
    """
    if active and not suspended and status in APPROVED_STATUSES:
        logger.info(f"Update action - {collection=}, ID: {data_id}")
        transform_batch.delay(collection, data, full_update=False)
    else:
        if check_document_exists(collection, data_id):
            logger.info(f"Delete action - {collection=}, ID: {data_id}")
            delete_data_by_id.delay(collection, data, delete=True)


def handle_delete_action(collection, data_id, data):
    """
    Handles the 'delete' action for the message.

    Args:
        collection (str): The name of the collection.
        data_id (str): The ID of the data to be deleted.
        data (dict): The data to be deleted.
    """
    if check_document_exists(collection, data_id):
        logger.info(f"Delete action - {collection=}, ID: {data_id}")
        delete_data_by_id.delay(collection, data, delete=True)
