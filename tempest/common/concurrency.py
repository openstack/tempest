# Copyright 2025 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import multiprocessing


def run_concurrent_tasks(target, resource_count, **kwargs):
    """Run a target function concurrently using multiprocessing.

    :param target: Function to execute concurrently. Must accept
                   (index, resource_ids, **kwargs) as parameters.
    :param resource_count: Number of concurrent processes to spawn.
    :param kwargs: Additional keyword arguments passed to the target function.
    :return: List of results collected from all processes.
    :raises RuntimeError: If any worker process fails during execution.
    """
    manager = multiprocessing.Manager()
    resource_ids = manager.list()
    errors = manager.list()  # Capture exceptions from workers

    def wrapped_target(index, resource_ids, **kwargs):
        try:
            target(index, resource_ids, **kwargs)
        except Exception as exc:
            errors.append(f"Worker {index} failed: {exc}")

    processes = []
    for i in range(resource_count):
        p = multiprocessing.Process(
            target=wrapped_target,
            args=(i, resource_ids),
            kwargs=kwargs
        )
        processes.append(p)

    # Start all processes
    for p in processes:
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()

    if errors:
        raise RuntimeError(
            "One or more concurrent tasks failed:\n" + "\n".join(errors)
        )

    return list(resource_ids)
