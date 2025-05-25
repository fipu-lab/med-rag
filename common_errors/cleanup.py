import re
import sys
from collections import defaultdict


def cleanup_log(input_file, output_file):
    with open(input_file, "r") as f:
        content = f.read()

    # Split content into cases
    cases = content.split("******************************")

    cleaned_cases = []
    for case in cases:
        if not case.strip():
            continue

        # Extract CASE, QUESTION, TRUE, and EVALUATION sections
        case_match = re.search(r"CASE: (.*?)\n", case)
        question_match = re.search(r"QUESTION: (.*?)\n", case)
        true_match = re.search(r"TRUE: (.*?)\n", case)
        evaluation_match = re.search(r"EVALUATION:\n(.*?)(?=\n\n|$)", case, re.DOTALL)

        if not all([case_match, question_match, true_match, evaluation_match]):
            continue

        # Format the case
        formatted_case = f"CASE: {case_match.group(1)}\n"
        formatted_case += f"QUESTION: {question_match.group(1)}\n"
        formatted_case += f"TRUE: {true_match.group(1)}\n"
        formatted_case += "EVALUATION:\n"

        # Process evaluation section
        evaluation_text = evaluation_match.group(1).strip()
        # Split evaluation into LLM entries
        llm_entries = re.findall(
            r"LLM \[(.*?)\]: (.*?)(?=LLM \[|$)", evaluation_text, re.DOTALL
        )

        for llm_name, llm_content in llm_entries:
            # Extract error categories and explanation
            error_categories = re.search(
                r"Error categories: (.*?)(?= - |$)", llm_content
            )
            explanation = re.search(
                r"Explanation: (.*?)(?=LLM \[|$)", llm_content, re.DOTALL
            )

            if error_categories and explanation:
                formatted_case += f"LLM [{llm_name}]:\n"
                formatted_case += f"- Error categories: {error_categories.group(1)}\n"
                formatted_case += f"- Explanation:\n{explanation.group(1).strip()}\n"
            else:
                # Fallback for cases where the format doesn't match
                formatted_case += f"LLM [{llm_name}]: {llm_content.strip()}\n"

        cleaned_cases.append(formatted_case)

    # Write cleaned content to output file
    with open(output_file, "w") as f:
        f.write("\n******************************\n\n".join(cleaned_cases))


def extract_error_categories(input_file, output_file):
    with open(input_file, "r") as f:
        content = f.read()

    # Split content into cases
    cases = content.split("******************************")

    for case in cases:
        if not case.strip():
            continue

        # Extract CASE and error categories
        case_match = re.search(r"CASE: (.*?)\n", case)
        if not case_match:
            continue

        case_id = case_match.group(1)

        # Find all LLM entries and their error categories
        llm_entries = re.findall(r"LLM \[(.*?)\]: (.*?)(?=LLM \[|$)", case, re.DOTALL)

        if llm_entries:
            with open(output_file, "a") as f:
                f.write(f"CASE: {case_id}\n")
                for llm_name, llm_content in llm_entries:

                    error_categories = re.search(
                        r"Error categories: (.*?)(?= - |$)", llm_content
                    )
                    if error_categories:
                        error_list = eval(error_categories.group(1))
                        f.write(f"LLM [{llm_name}]: {error_list}\n")

                        # If error category [6] is present, look for explanation
                        if 6 in error_list:
                            # Look for explanation in both formats
                            explanation = re.search(
                                r"Explanation: (.*?)(?=LLM \[|$)",
                                llm_content,
                                re.DOTALL,
                            )
                            if explanation:
                                explanation_text = explanation.group(1).strip()
                                # Find the entire [6] part including either "Other:" or "- Explanation:"
                                error_6_explanation = re.search(
                                    r"\[6\]\s*(?:Other:|-\s*Explanation:)\s*.*?(?=\s*-\s*\[|$)",
                                    explanation_text,
                                )
                                if error_6_explanation:
                                    f.write(f"{error_6_explanation.group(0).strip()}\n")
                f.write("\n******************************\n\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python cleanup.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    cleanup_log(input_file, output_file)

    error_summary_file = output_file.replace(".log", "_error_summary.log")

    with open(error_summary_file, "w") as f:
        f.write("")
    extract_error_categories(input_file, error_summary_file)
