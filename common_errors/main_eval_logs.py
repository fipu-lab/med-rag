import json
import threading
import random
import datetime as dt
import asyncio
import llm
import time
from itertools import islice
from pprint import pprint
from types import SimpleNamespace as sn
from tqdm import tqdm

random.seed(42)


class LogOutput:
    def __init__(self, file_path):
        self.log_file = open(file_path, "a")

    def write(self, message):
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.log_file.flush()


def logger(file_path):
    output = LogOutput(file_path)

    def log(*args, sep=" ", end="\n", file=output):
        print(*args, sep=sep, end=end, file=file)

    return log


def parse_log_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()
        cases = content.split("*" * 30)
        cases = [case.strip() for case in cases if case.strip()]

        parsed_cases = []
        for case in cases:
            lines = case.split("\n")
            case_dict = {}
            current_llm_output = None

            for line in lines:
                if line.startswith("CASE:"):
                    case_dict["key"] = line.split(":", 1)[1].strip()
                elif line.startswith("QUESTION:"):
                    case_dict["question_refine"] = line.split(":", 1)[1].strip()
                elif line.startswith("TRUE:"):
                    case_dict["sql"] = line.split(":", 1)[1].strip()
                elif line.startswith("LLM ["):
                    if "llm_outputs" not in case_dict:
                        case_dict["llm_outputs"] = []
                    model = line.split("[", 1)[1].split("]", 1)[0]
                    sql = line.split(":", 1)[1].strip()
                    current_llm_output = {"model": model, "sql": sql, "meta": {}}
                    case_dict["llm_outputs"].append(current_llm_output)
                elif line.startswith("MODEL:") and current_llm_output:
                    current_llm_output["meta"]["model"] = line.split(":", 1)[1].strip()
                elif line.startswith("USAGE:") and current_llm_output:
                    usage_str = line.split(":", 1)[1].strip()
                    try:
                        current_llm_output["meta"]["usage"] = json.loads(usage_str)
                    except json.JSONDecodeError:
                        current_llm_output["meta"]["usage"] = usage_str
                elif line.startswith("ANSWER:") and current_llm_output:
                    answer_parts = line.split(":", 1)[1].strip().split()
                    current_llm_output["meta"]["answer"] = {
                        "result": answer_parts[0],
                        "rows": answer_parts[1] if len(answer_parts) > 1 else None,
                        "truth": answer_parts[2] if len(answer_parts) > 2 else None,
                        "truth_rows": (
                            answer_parts[3] if len(answer_parts) > 3 else None
                        ),
                    }

            if case_dict:
                parsed_cases.append(sn(**case_dict))

        return parsed_cases


def batch_iterator(iterable, batch_size=10):
    batch = []
    count = 0
    for idx, item in enumerate(iterable):
        batch.append((idx, item))
        if len(batch) == batch_size:
            yield count, batch
            count += 1
            batch = []
    if batch:
        yield count, batch


async def run_test_case(case, model, exclude_prompts):
    tasks = {}
    time_a = time.monotonic()

    prompt = f"""
CASE: {case.key}
QUESTION: {case.question_refine}
TRUE: {case.sql}

LLM outputs:
"""
    for llm_output in case.llm_outputs:
        prompt += f"\nLLM [{llm_output['model']}]: {llm_output['sql']}"

    prompt += "\n\nPlease analyze the errors in each LLM's query using the numbered categories. For each LLM output, provide the error numbers and brief explanation."

    task = llm.ai_query(
        message=prompt,
        model=model,
        max_tokens=1000,
        exclude_system_sections=exclude_prompts,
        sql=False,
    )
    tasks[model] = task

    results = await asyncio.gather(*tasks.values())
    time_b = time.monotonic()

    if (time_b - time_a) < 2.0:
        await asyncio.sleep(1)

    return sn(
        case=case,
        output=results[0],
    )


async def main(
    experiment_name,
    batch_size=10,
    batch_limit=-1,
    exclude_prompts={},
    continue_from=None,
    models_filter=None,
):
    print = logger(f"output/cat_eval_{experiment_name}.log")

    if not continue_from:
        print()
        print("=" * 30)
        print()
        print(
            f"Starting experiment {experiment_name} at {dt.datetime.now().isoformat()}..."
        )
        print()

    cases = parse_log_file("output/false_logs/all_false_cases.log")

    if continue_from:
        index = [x.key for x in cases].index(continue_from)
        cases = cases[index:]

    models = ["gpt-4o"]

    for batch_id, batch in tqdm(
        batch_iterator(cases, batch_size=batch_size),
        total=batch_limit if batch_limit > 0 else len(cases) // batch_size,
    ):
        if batch_id >= batch_limit:
            break

        tasks = []
        for _, case in batch:
            tasks.append(run_test_case(case, models[0], exclude_prompts))

        batch_results = await asyncio.gather(*tasks)

        for batch_result in batch_results:
            print("*" * 30)
            print()
            print("CASE:", batch_result.case.key)
            print("QUESTION:", batch_result.case.question_refine)
            print("TRUE:", batch_result.case.sql)
            print()
            print("EVALUATION:")
            print(batch_result.output.text)
            print()


batch_size = 5
batch_limit = 200
exclude_prompts = set()
continue_from = None
models_filter = None

exclude_info = "-".join(exclude_prompts) if len(exclude_prompts) else "none"
experiment_name = (
    f"eval_batch_size={batch_size}&n={batch_size * batch_limit}&exclude={exclude_info}"
)

if __name__ == "__main__":

    print("\nRunning full evaluation...")
    asyncio.run(
        main(
            experiment_name,
            batch_size,
            batch_limit,
            exclude_prompts,
            continue_from,
            models_filter,
        )
    )
