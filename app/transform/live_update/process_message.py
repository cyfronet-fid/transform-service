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


def _check_task_success(task) -> bool:
    """
    Checks if a Celery task completed successfully.
    Returns True if task succeeded or was not needed, False if it failed or timed out.
    """
    if task is None:
        return True
    try:
        if hasattr(task, "get") and callable(task.get):
            res = task.get(timeout=120)
        else:
            res = task

        if isinstance(res, dict):
            status = res.get("status")
            if status is not None:
                return status == "SUCCESS"
            return True
        elif isinstance(res, list):
            if not res:
                return True
            return all(
                isinstance(item, dict) and item.get("status") in ("SUCCESS", "ABORTED")
                for item in res
            )
        return True
    except Exception as e:
        logger.error(f"[LiveUpdate] Task execution failed: {e}", exc_info=True)
        return False


def process_message(frame_or_data, ack_id_or_subscription=None) -> bool:
    """
    Processes incoming messages from both JMS (STOMP) and AMS.

    AMS sends: JSON string or dict with the data, plus ack_id containing subscription info
    STOMP sends: Frame object with .headers and .body

    Args:
        frame_or_data: Either a STOMP frame object or a JSON string/dict from AMS
        ack_id_or_subscription: Optional ack_id from AMS (contains subscription name)
                               Format: projects/{project}/subscriptions/{subscription_name}:{message_id}

    Returns:
        bool: True if processing and Solr update succeeded, False otherwise.
    """
    # Determine if this is a STOMP frame or AMS data
    if hasattr(frame_or_data, "headers") and hasattr(frame_or_data, "body"):
        # STOMP/JMS message
        return _process_stomp_message(frame_or_data)
    else:
        # AMS message (string or dict)
        return _process_ams_message(frame_or_data, ack_id_or_subscription)


def _process_stomp_message(frame) -> bool:
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
        return handle_create_action(
            active, suspended, status, collection, data, data_id
        )
    elif action == "update":
        return handle_update_action(
            active, suspended, status, collection, data, data_id
        )
    elif action == "delete":
        return handle_delete_action(collection, data_id, data)
    else:
        logger.warning(f"Unknown STOMP action: {action}")
        return False


def _process_ams_message(message_data, ack_id=None) -> bool:
    """Process AMS format messages"""
    # Parse if it's a string
    if isinstance(message_data, str):
        try:
            frame_body = json.loads(message_data)
        except json.JSONDecodeError as e:
            logger.error(
                f"[AMS] Failed to parse message as JSON: {e}. Message content: {message_data[:300]}"
            )
            return False
    elif isinstance(message_data, dict):
        frame_body = message_data
    else:
        logger.error(f"[AMS] Invalid message_data type: {type(message_data)}")
        return False

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
            return False

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
    if data is None:
        logger.error(
            f"[AMS] Could not extract data for collection='{raw_collection}' from frame"
        )
        return False

    logger.info(
        f"[AMS] Started processing message: type={raw_collection}, collection={collection}, id={data_id}, action={action}, active={active}, suspended={suspended}, status='{status}'"
    )

    if action == "create":
        return handle_create_action(
            active, suspended, status, collection, data, data_id
        )
    elif action == "update":
        return handle_update_action(
            active, suspended, status, collection, data, data_id
        )
    elif action == "delete":
        return handle_delete_action(collection, data_id, data)
    else:
        logger.warning(f"[AMS] Unknown action: {action}")
        return False


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


def handle_create_action(active, suspended, status, collection, data, data_id) -> bool:
    """
    Handles the 'create' action for the message.

    Args:
        active (bool): Flag indicating if the record is active.
        suspended (bool): Flag indicating if the record is suspended.
        status (str): The status of the record.
        collection (str): The name of the collection.
        data (dict): The data to be processed.
        data_id (str): The ID of the data.

    Returns:
        bool: True if task succeeded or action was skipped, False otherwise.
    """
    if active and not suspended and status in APPROVED_STATUSES:
        logger.info(
            f"[LiveUpdate] Scheduling create/transform batch task for collection='{collection}', id='{data_id}'"
        )
        task = transform_batch.delay(collection, data, full_update=False)
        return _check_task_success(task)
    else:
        logger.info(
            f"[LiveUpdate] Aborting create action for collection='{collection}', id='{data_id}'. "
            f"Reason: active={active}, suspended={suspended}, status='{status}' (approved statuses: {APPROVED_STATUSES})"
        )
        return True


def handle_update_action(active, suspended, status, collection, data, data_id) -> bool:
    """
    Handles the 'update' action for the message.

    Args:
        active (bool): Flag indicating if the record is active.
        suspended (bool): Flag indicating if the record is suspended.
        status (str): The status of the record.
        collection (str): The name of the collection.
        data (dict): The data to be processed.
        data_id (str): The ID of the data.

    Returns:
        bool: True if task succeeded or action was skipped, False otherwise.
    """
    logger.info(
        f"[LiveUpdate] handle_update_action: collection='{collection}', id='{data_id}', "
        f"active={active}, suspended={suspended}, status='{status}'"
    )
    if active and not suspended and status in APPROVED_STATUSES:
        logger.info(
            f"[LiveUpdate] Scheduling update/transform batch task for collection='{collection}', id='{data_id}'"
        )
        task = transform_batch.delay(collection, data, full_update=False)
        return _check_task_success(task)
    else:
        doc_exists = check_document_exists(collection, data_id)
        if doc_exists:
            logger.info(
                f"[LiveUpdate] Item is inactive/unapproved but exists in collection='{collection}', id='{data_id}'. "
                "Scheduling delete task."
            )
            task = delete_data_by_id.delay(collection, data, delete=True)
            return _check_task_success(task)
        else:
            logger.info(
                f"[LiveUpdate] Item is inactive/unapproved and does NOT exist in collection='{collection}', id='{data_id}'. Skipping delete."
            )
            return True


def handle_delete_action(collection, data_id, data) -> bool:
    """
    Handles the 'delete' action for the message.

    Args:
        collection (str): The name of the collection.
        data_id (str): The ID of the data to be deleted.
        data (dict): The data to be deleted.

    Returns:
        bool: True if task succeeded or action was skipped, False otherwise.
    """
    doc_exists = check_document_exists(collection, data_id)
    if doc_exists:
        logger.info(
            f"[LiveUpdate] Scheduling delete task for collection='{collection}', id='{data_id}'"
        )
        task = delete_data_by_id.delay(collection, data, delete=True)
        return _check_task_success(task)
    else:
        logger.info(
            f"[LiveUpdate] Delete action skipped. Document does not exist in collection='{collection}', id='{data_id}'"
        )
        return True
