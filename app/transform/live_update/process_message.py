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
    "approved",
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
        except json.JSONDecodeError as e:
            logger.error(
                f"[AMS] Failed to parse message as JSON: {e}. Message content: {message_data[:300]}"
            )
            return
    else:
        frame_body = message_data

    # Extract subscription name if ack_id or subscription is provided
    # Formats:
    # 1. Full ack_id: projects/{project}/subscriptions/{subscription_name}:{message_id}
    # 2. Subscription name: sf-training_resource-create, transformer-adapter-update, etc.
    subscription_name = None
    if ack_id:
        if "/subscriptions/" in str(ack_id):
            try:
                subscription_name = ack_id.split("/subscriptions/")[1].split(":")[0]
                logger.info(
                    f"[AMS] Extracted subscription name '{subscription_name}' from ack_id: {ack_id}"
                )
            except (IndexError, AttributeError):
                logger.warning(
                    f"[AMS] Failed to extract subscription name from ack_id: {ack_id}"
                )
        else:
            subscription_name = str(ack_id)
            logger.info(
                f"[AMS] Received subscription name directly: {subscription_name}"
            )

    # Extract action and resource type from subscription name
    # Format: transformer-{resource}-{action}
    # Examples: transformer-adapter-update, transformer-training_resource-create
    raw_collection = None
    action = None

    if subscription_name:
        # clean_sub = subscription_name
        # for prefix in ("sf-", "transformer-"): # add yours if testing
        #     if clean_sub.startswith(prefix):
        #         clean_sub = clean_sub[len(prefix) :]
        #         break
        #
        # parts = clean_sub.split("-")
        # if len(parts) >= 2 and parts[-1] in ("create", "update", "delete"):
        #     action = parts[-1]
        #     raw_collection = "-".join(parts[:-1])
        # elif len(parts) >= 3:
        #     action = parts[-1]
        #     raw_collection = "-".join(parts[1:-1])
        #
        # if action and raw_collection:
        #     logger.info(
        #         f"[AMS] Extracted from subscription '{subscription_name}': action={action}, resource={raw_collection}"
        #     )
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
                f"[AMS] Could not determine resource type from subscription or message keys: {list(frame_body.keys())}"
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
        f"[AMS] Started processing message: type={raw_collection}, collection={collection}, id={data_id}, action={action}, active={active}, suspended={suspended}, status='{status}'"
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
        logger.info(
            f"[LiveUpdate] Scheduling create/transform batch task for collection='{collection}', id='{data_id}'"
        )
        transform_batch.delay(collection, data, full_update=False)
    else:
        logger.info(
            f"[LiveUpdate] Aborting create action for collection='{collection}', id='{data_id}'. "
            f"Reason: active={active}, suspended={suspended}, status='{status}' (approved statuses: {APPROVED_STATUSES})"
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
    logger.info(
        f"[LiveUpdate] handle_update_action: collection='{collection}', id='{data_id}', "
        f"active={active}, suspended={suspended}, status='{status}'"
    )
    if active and not suspended and status in APPROVED_STATUSES:
        logger.info(
            f"[LiveUpdate] Scheduling update/transform batch task for collection='{collection}', id='{data_id}'"
        )
        transform_batch.delay(collection, data, full_update=False)
    else:
        doc_exists = check_document_exists(collection, data_id)
        if doc_exists:
            logger.info(
                f"[LiveUpdate] Item is inactive/unapproved but exists in collection='{collection}', id='{data_id}'. "
                "Scheduling delete task."
            )
            delete_data_by_id.delay(collection, data, delete=True)
        else:
            logger.info(
                f"[LiveUpdate] Item is inactive/unapproved and does NOT exist in collection='{collection}', id='{data_id}'. Skipping delete."
            )


def handle_delete_action(collection, data_id, data):
    """
    Handles the 'delete' action for the message.

    Args:
        collection (str): The name of the collection.
        data_id (str): The ID of the data to be deleted.
        data (dict): The data to be deleted.
    """
    doc_exists = check_document_exists(collection, data_id)
    if doc_exists:
        logger.info(
            f"[LiveUpdate] Scheduling delete task for collection='{collection}', id='{data_id}'"
        )
        delete_data_by_id.delay(collection, data, delete=True)
    else:
        logger.info(
            f"[LiveUpdate] Delete action skipped. Document does not exist in collection='{collection}', id='{data_id}'"
        )
