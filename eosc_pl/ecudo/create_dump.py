import asyncio
import json
import math
from typing import Dict, List

import aiohttp
from ecudo import settings


async def fetch_json(session: aiohttp.ClientSession, url: str) -> dict:
    """Fetch JSON from a URL with retries and basic error handling."""
    for attempt in range(1, settings.MAX_RETRIES + 1):
        try:
            async with session.get(
                url,
                timeout=settings.TIMEOUT,
                headers=settings.HEADERS,
                allow_redirects=True,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    text = await resp.text()
                    print(f"❌ Error {resp.status} while fetching {url}\n{text}")
                    return {}
        except Exception as e:
            print(f"⚠️ Attempt {attempt}/{settings.MAX_RETRIES} failed for {url}: {e}")
            await asyncio.sleep(2 * attempt)  # exponential backoff
    return {}


async def get_organizations(session: aiohttp.ClientSession) -> List[Dict]:
    data = await fetch_json(session, f"{settings.BASE_URL}/organizations")
    return data.get("organizations", [])


async def get_metadata_ids_for_org(
    session: aiohttp.ClientSession, org_id: str, max_records: int
) -> List[str]:
    metadata_ids = []
    pages = math.ceil(max_records / settings.PAGE_SIZE)
    for page in range(pages):
        offset = page * settings.PAGE_SIZE + 1
        url = f"{settings.BASE_URL}/organizations/{org_id}/data?offset={offset}&limit={settings.PAGE_SIZE}"
        data = await fetch_json(session, url)
        ids = data.get("metadata", [])
        if not ids:
            break
        metadata_ids.extend(ids)
        if len(metadata_ids) >= max_records:
            break
    return metadata_ids


async def get_metadata_detail(session: aiohttp.ClientSession, record_id: str) -> dict:
    url = f"{settings.BASE_URL}/metadata/{record_id}/json-ld"
    return await fetch_json(session, url)


async def gather_with_concurrency(n: int, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def main():
    errors = []
    async with aiohttp.ClientSession() as session:
        print("📡 Fetching list of organizations...")
        organizations = await get_organizations(session)
        if not organizations:
            print("❌ Failed to fetch organizations.")
            return

        # Filter to only the target organization
        organizations = [
            org for org in organizations if org["id"] == settings.TARGET_ORG_ID
        ]
        if not organizations:
            print(f"❌ Target organization '{settings.TARGET_ORG_ID}' not found.")
            return

        print(f"✅ Found target organization: {settings.TARGET_ORG_ID}")
        all_metadata_ids = []

        for org in organizations:
            org_id = org["id"]
            print(f"📥 Fetching records for organization: {org_id}")
            ids = await get_metadata_ids_for_org(
                session, org_id, settings.TOTAL_RECORDS
            )
            if not ids:
                errors.append(
                    {"organization": org_id, "error": "No records or server error"}
                )
            all_metadata_ids.extend(ids)

        print(
            f"📦 Found {len(all_metadata_ids)} record IDs. Fetching metadata details..."
        )

        results = await gather_with_concurrency(
            settings.CONCURRENCY,
            *[get_metadata_detail(session, rid) for rid in all_metadata_ids],
        )

        successful = []
        for rid, record in zip(all_metadata_ids, results):
            if record:
                successful.append(record)
            else:
                errors.append({"record_id": rid, "error": "Failed to fetch metadata"})

        print(f"✅ Successfully fetched {len(successful)} records.")
        print(f"❌ Failed to fetch {len(errors)} records.")

        with open(settings.OUTPUT_DIR / "ecudo_dump.json", "w", encoding="utf-8") as f:
            json.dump(successful, f, indent=2, ensure_ascii=False)

        with open(
            settings.OUTPUT_DIR / "ecudo_errors.json", "w", encoding="utf-8"
        ) as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)

        print(f"📁 Dump saved to {settings.OUTPUT_DIR / 'ecudo_dump.json'}")
        print(f"📁 Errors saved to {settings.OUTPUT_DIR / 'ecudo_errors.json'}")


if __name__ == "__main__":
    asyncio.run(main())
