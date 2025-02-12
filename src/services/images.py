from fastapi import APIRouter, Path, Query
from pydantic import BaseModel
from typing import Dict, List

import httpx
import numpy as np
import pathlib
import random
import sys
from collections import defaultdict
from functools import partial

try:
    import dao
    import util
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao
    import util

route = APIRouter(tags=["images"])


class CopyrightDetails(BaseModel):
    holder: str | None
    year: str | None
    license: str | None
    institution: str | None


class ImageMetadata(BaseModel):
    image_url: str
    thumbnail_url: str
    object_id: str
    batch: int | None
    file_name: str | None
    processid: str | None
    sampleid: str | None
    taxon: str | None
    meta: str | None
    copyright: CopyrightDetails
    photographer: str | None


class ImageSummary(BaseModel):
    images: Dict[str, List[ImageMetadata]]
    photographers: Dict[str | None, int]


# TODO: Integrate settings.py/util.py to fetch these values/functions
_IMG_PID_LIMIT = 500
_IMG_LIMIT = 50

_TAX_RANKS = [
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "subfamily",
    "tribe",
    "genus",
    "species",
    "subspecies",
]


def calculate_weight(pair_arr, target):
    pair_arr = sorted(pair_arr, key=lambda pair: pair[0])
    input_arr = np.array([pair[0] for pair in pair_arr])
    specimen_name = [pair[1] for pair in pair_arr]
    N = len(input_arr)

    sum = np.sum(input_arr)
    if sum <= target:
        return {specimen_name[i]: int(input_arr[i]) for i in range(N)}

    log_arr = np.log(input_arr)
    sum_log = np.sum(log_arr)
    log_arr *= target / sum_log

    output_arr = np.ceil(log_arr).astype(np.int64)

    output_arr[output_arr == 0] = 1
    current_sum = np.sum(output_arr)
    difference = current_sum - target

    for i in range(N):
        if output_arr[i] > input_arr[i]:
            difference += input_arr[i] - output_arr[i]
            output_arr[i] = input_arr[i]
        elif difference < 0:
            remaining_items = N - i
            if (
                difference < remaining_items
                and i != N - 1
                and output_arr[i] == output_arr[i + 1]
            ):
                continue
            increase_value = np.ceil(difference * (-1) / remaining_items).astype(
                np.int64
            )
            prev_value = output_arr[i]
            output_arr[i] = min(output_arr[i] + increase_value, input_arr[i])
            difference += output_arr[i] - prev_value
        if difference > 0:
            remaining_items = N - i
            decreased_value = np.ceil(difference / remaining_items).astype(np.int64)
            prev_value = output_arr[i]
            output_arr[i] = max(1, output_arr[i] - decreased_value)
            difference += output_arr[i] - prev_value

    return {specimen_name[i]: int(output_arr[i]) for i in range(len(output_arr))}


def map_data_list(map, row, preprocess):
    """
    MapReduce map function for collecting data into single map data list
    after a preprocess function

    - **map**: Aggregate map data list
    - **row**: Single row data object
    - **preprocess**: Function to preprocess row into one data point
    """
    data = preprocess(row)
    map.append(data)


def reduce_data_count(map):
    """
    MapReduce reduce function to aggregate data list into frequency counts

    - **map**: Aggregate map data list

    Returns: dict, frequency count
    """
    frequencies = defaultdict(lambda: 0)
    for data in map:
        frequencies[data] += 1
    return frequencies


def preprocess_row_string(row, key):
    """
    Preprocess and return string from row's document

    - **row**: Document
    - **key**: Key to extract value from

    Returns: str, document content under key
    """
    data = row.get(key, "")
    return data


@route.get(
    "/images/{query_id}",
    response_model=ImageSummary,
    response_description="Image Metadata Summary",
)
async def generate_images_summary(
    query_id: str = Path(title="Documents query ID"),
    max_images: int = Query(-1, title="Maximum # of images"),
    assorted_subtaxa: bool = Query(
        False, title="Select images based on subsampling each subtaxa"
    ),
):
    """
    Retrieve a set of image metadata and image URLs from an encoded query (query_id). Selects a random
    set of `IMG_LIMIT` images from querying a random set of process IDs (maximum `IMG_PID_LIMIT`) to CAOS.

    - **query_id**: Encoded triplets query from `/api/query`
    - **max_images**: Maximum number of images returned, set to `IMG_LIMIT` if max_images < 0
    - **assorted_subtaxa**: Use taxon in query to select diverse set of images of subtaxa;
        Must have single taxonomy triplet in query
    """
    triplets = util.get_triplets_from_query_id(query_id)
    fields = ["processid", "identification"]

    if assorted_subtaxa:
        try:
            # Add subtaxa rank to fields to retrieve
            for triplet in triplets[:-1]:
                if triplet.startswith("tax"):
                    rank = triplet.split(":")[1]
                    rank_index = _TAX_RANKS.index(rank)
                    fields.append(f"`{_TAX_RANKS[rank_index + 1]}`")

            # Only allow one taxonomy triplet
            if len(fields) > 2:
                raise
        except:
            fields = ["processid", "identification"]

    if max_images < 0:
        max_images = _IMG_LIMIT

    cb_data = "primary_data"
    bucket = dao.NAME_MAP[cb_data]["bucket"]
    collection = dao.NAME_MAP[cb_data]["collection"]

    documents = dao.get_cb_field_values(triplets, fields, bucket, collection, 5000)

    processid_to_taxon_map = {}
    index_to_processid_map = {}
    if len(fields) > 2:
        subtaxa_rank = fields[-1].strip("`")
        subtaxa_processids = defaultdict(lambda: set())
        for document in documents:
            processid_to_taxon_map[document["processid"]] = document["identification"]

            subtaxon = document.get(subtaxa_rank)
            subtaxa_processids[subtaxon].add(document["processid"])

        index_subsampling = calculate_weight(
            [
                (len(processids), subtaxon)
                for subtaxon, processids in subtaxa_processids.items()
            ],
            _IMG_PID_LIMIT,
        )

        for subtaxon, count in index_subsampling.items():
            index_to_processid_map[subtaxon] = random.sample(
                sorted(subtaxa_processids[subtaxon]),
                min(len(subtaxa_processids[subtaxon]), count),
            )
    else:
        processids = []
        for document in documents:
            processid_to_taxon_map[document["processid"]] = document["identification"]
            processids.append(document["processid"])
        processids = random.sample(
            sorted(set(processids)), min(len(set(processids)), _IMG_PID_LIMIT)
        )

        index_to_processid_map = {None: processids}

    processid_to_index_map = {}
    for index, processids in index_to_processid_map.items():
        for processid in processids:
            processid_to_index_map[processid] = index

    processids = [
        processid
        for processid_list in index_to_processid_map.values()
        for processid in processid_list
    ]
    if not processids:
        return {"images": {}, "photographers": {}}

    # TODO: Validate behaviour on exception
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.get(
                url=f"{util.get_caos_url()}/api/images",
                params={"processids": ",".join(processids)},
            )
            resp.raise_for_status()
            metadata = resp.json()

    except httpx.HTTPStatusError:
        raise

    # Collect retrieved images
    index_to_image_map = defaultdict(lambda: [])
    for obj_meta in metadata:
        processid = obj_meta["processid"]
        index = processid_to_index_map[processid]
        index_to_image_map[index].append(obj_meta)

    # Sort by score on each index
    for index, images in index_to_image_map.items():
        index_to_image_map[index] = sorted(
            images, key=lambda x: x["score"] if x["score"] else 0, reverse=True
        )

    # Select images from each index via round robin, from highest to lowest score, up to max_images
    image_weighting = [
        (index, len(images)) for index, images in index_to_image_map.items()
    ]
    index_cycle_order = [
        index[0] for index in sorted(image_weighting, key=lambda x: x[1], reverse=True)
    ]
    image_list = []
    for i, index in enumerate(index_cycle_order):
        image_list.extend(
            [
                (j * len(index_cycle_order) + i, image)
                for j, image in enumerate(index_to_image_map[index])
            ]
        )
    sorted_image_list = [image[1] for image in sorted(image_list)][:max_images]

    photographers_map = []
    photographers_preprocess = partial(preprocess_row_string, key="photographer")

    # Reorganize images by index (subtaxa) or orientation
    images_to_return = defaultdict(lambda: [])
    for obj_meta in sorted_image_list:
        map_data_list(photographers_map, obj_meta, photographers_preprocess)

        object_id = obj_meta["objectid"]
        object_ext = object_id.split("_")[1].split(".", 2)[-1]

        processid = obj_meta["processid"]
        index = processid_to_index_map[processid]
        if not index:  # assorted_subtaxa = False or subtaxa is None
            index = obj_meta["meta"] if obj_meta["meta"] else "Unknown"  # Orientation
        images_to_return[index].append(
            {
                "image_url": f"{util.get_caos_url()}/api/objects/{object_id}?subunit=1024.{object_ext}",
                "thumbnail_url": f"{util.get_caos_url()}/api/objects/{object_id}?subunit=320.{object_ext}",
                "object_id": object_id,
                "batch": obj_meta["batch"],
                "file_name": obj_meta["file_name"],
                "processid": processid,
                "sampleid": obj_meta["sampleid"],
                "taxon": processid_to_taxon_map[processid],
                "meta": obj_meta["meta"],
                "copyright": {
                    "holder": obj_meta["copyright_license_holder"],
                    "year": obj_meta["copyright_license_year"],
                    "license": obj_meta["copyright_license"],
                    "institution": obj_meta["copyright_license_institution"],
                },
                "photographer": obj_meta["photographer"],
            }
        )
        i += 1

    photographers = reduce_data_count(photographers_map)

    return {"images": images_to_return, "photographers": photographers}
