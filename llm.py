import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from litellm import acompletion, aembedding
import litellm
import random
import sys
import asyncio
from types import SimpleNamespace as sn
import re
import os
from dotenv import load_dotenv

load_dotenv()

litellm.enable_cache(
    type="disk",
    supported_call_types=["aembedding"],
    disk_cache_dir="llm_cache",
)

RETRY_LIMIT = 5
MAX_TOKENS = 200
TIMEOUT = 120  # 15

models = {
    "deepseek-v3": sn(
        model="fireworks_ai/accounts/fireworks/models/deepseek-v3",
        meta=sn(
            price_in=0.90,
            price_out=0.90,
        ),
    ),
    "llama3.3-70b": sn(
        model="fireworks_ai/accounts/fireworks/models/llama-v3p3-70b-instruct",
        meta=sn(
            price_in=0.90,
            price_out=0.90,
        ),
    ),
    "gpt-4o": sn(
        model="gpt-4o",
        meta=sn(
            price_in=2.50,
            price_out=10.00,
        ),
    ),
    # "deepseek-coder": sn(
    #     model="fireworks_ai/accounts/fireworks/models/deepseek-coder-7b-instruct-v1p5",
    #     meta=sn(
    #         price_in=0.20,
    #         price_out=0.20,
    #     ),
    # ),
    "deepseek-r1": sn(
        model="fireworks_ai/accounts/fireworks/models/deepseek-r1",
        meta=sn(
            price_in=8.0,
            price_out=8.0,
            extra_tokens=10000,
        ),
    ),
    "deepseek-r1-groq": sn(
        model="groq/deepseek-r1-distill-llama-70b",
        meta=sn(
            price_in=8.0,
            price_out=8.0,
            extra_tokens=10000,
        ),
    ),
}


def parse_file(filename):
    parsed_data = {}
    current_section = None

    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                parsed_data[current_section] = line + "\n"
            elif current_section:
                parsed_data[current_section] += line + "\n"
            else:
                raise ValueError(
                    "File format is invalid. Ensure sections are properly defined."
                )

    parsed_data = {k: v.strip() for k, v in parsed_data.items()}
    return parsed_data


prompts = parse_file("prompts/common_errors.md")


def get_models(include_large=False, models_filter=None):
    return [
        key
        for key, value in models.items()
        if (not hasattr(value, "large") or not value.large)
        and (models_filter is None or key in models_filter)
    ]


def normalize(x):
    if x:
        return re.sub(r"\s+", " ", x).strip()
    return x


async def ai_embeddings(inputs=[]):
    if len(inputs) == 0:
        return {"data": []}
    response = await aembedding(
        model="text-embedding-3-small",
        input=inputs,
        dimensions=512,
        caching=True,
    )
    return response


async def ai_query(
    message=None,
    system=None,
    model="llama3.2",
    max_tokens=MAX_TOKENS,
    prefix=None,
    exclude_system_sections={},
    sql=True,
):
    if system is None:
        system = "".join(
            content
            for section, content in prompts.items()
            if section not in exclude_system_sections
        )

    model_spec = models.get(model)

    if hasattr(model_spec, "meta") and hasattr(model_spec.meta, "extra_tokens"):
        max_tokens += model_spec.meta.extra_tokens

    messages = []

    if system is not None:
        if (
            hasattr(model_spec, "meta")
            and hasattr(model_spec.meta, "has_system")
            and not model_spec.meta.has_system
        ):
            message = f"Context: {system} \n\n" + message
        else:
            messages.append({"content": system, "role": "system"})

    if message is not None:
        messages.append({"content": message, "role": "user"})

    if prefix:
        messages.append({"content": prefix, "role": "system"})

    params = {
        **{k: v for k, v in model_spec.__dict__.items() if k not in {"meta"}},
        "messages": messages,
        # "max_tokens": max_tokens,
        "temperature": 0,
        # "timeout": TIMEOUT,
    }

    response = None
    for retry_idx in range(RETRY_LIMIT):
        try:
            response = await acompletion(**params)
            break
        except Exception as e:
            print(f"ERROR: ({model}) {str(e)}", file=sys.stderr)
            await asyncio.sleep((1.5 + retry_idx) ** 2 + random.uniform(0.5, 3))

    if response and len(response.choices):
        result = response.choices[0].message.content

        if sql:
            if "```sql" in result:
                pattern = r"```sql(.*?)(?:``|$)"
                matches = re.findall(pattern, result, re.DOTALL)
                if len(matches):
                    result = matches[0]
            elif "```" in result:
                pattern = r"```(.*?)(?:``|$)"
                matches = re.findall(pattern, result, re.DOTALL)
                if len(matches):
                    result = matches[0]

        if prefix:
            result = prefix + result

        response.model = model

        if sql:
            return sn(
                sql=normalize(result),
                meta=response,
            )
        else:
            return sn(
                text=normalize(result),
                meta=response,
            )

    if sql:
        return sn(
            sql="--timeout--",
            meta=sn(
                model=model,
                usage=sn(
                    prompt_tokens=0,
                    completion_tokens=0,
                ),
            ),
        )
    else:
        return sn(
            text="--timeout--",
            meta=sn(
                model="none",
                usage=sn(
                    prompt_tokens=0,
                    completion_tokens=0,
                ),
            ),
        )


if __name__ == "__main__":

    print(prompts)
